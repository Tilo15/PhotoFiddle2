import getpass
import glob
import os

import subprocess

import shutil
import threading

import cv2

import Activity
from gi.repository import GLib, Gtk, GdkPixbuf, Pango

import Export
from HDR.Methods import Enfuse
from HDR.Methods import Fattal
from HDR.Methods import Mantuik


class HDR(Activity.Activity):

    def on_init(self):
        self.id = "HDR"
        self.name = "High Dynamic Range Stack"
        self.subtitle = "Stack Many Images at Different Exposures"

        UI_FILE = "ui/HDR_Activity.glade"
        self.builder.add_from_file(UI_FILE)

        self.widget = self.builder.get_object("HDR_main")
        self.stack.add_titled(self.widget, self.id, self.name)

        self.header_widget = self.builder.get_object("HDR_header")
        self.header_stack.add_titled(self.header_widget, self.id, self.name)

        # Get all UI Components
        self.ui = {}
        components = [
            "open_window",
            "open_chooser",
            "preview_button",
            "open_header",
            "open_open_button",
            "open_cancel_button",
            "images",
            "preview",
            "export_image",
            "open_pf2",
            "add_button",
            "remove_button",
            "scroll_window",
            "popovermenu",
            "stack",
            "method"
        ]

        self.paths = []
        self.exporting = False
        self.settings = {}

        for component in components:
            self.ui[component] = self.builder.get_object("%s_%s" % (self.id, component))

        self.menu_popover = self.ui["popovermenu"]

        self.ui["open_window"].set_transient_for(self.root)
        self.ui["open_window"].set_titlebar(self.ui["open_header"])

        # Connect Siginals
        self.ui["add_button"].connect("clicked", self.on_add_clicked)
        self.ui["remove_button"].connect("clicked", self.on_remove_clicked)
        self.ui["open_open_button"].connect("clicked", self.on_file_opened)
        self.ui["open_cancel_button"].connect("clicked", self.on_file_canceled)
        self.ui["preview_button"].connect("clicked", self.on_preview_clicked)
        self.ui["export_image"].connect("clicked", self.export_clicked)
        self.ui["open_pf2"].connect("clicked", self.export_pf2_clicked)
        self.ui["method"].connect("changed", self.on_method_changed)

        self.method = None

        self.methods = [
            Enfuse.Enfuse(),
            Fattal.Fattal(),
            Mantuik.Mantuik06(),
            Mantuik.Mantuik08(),
        ]

        self.methodMap = {}
        for method in self.methods:
            self.methodMap[method.name] = method
            self.ui["method"].append_text(method.name)
            self.ui["stack"].add(method.widget)

        self.ui["method"].set_active(0)

        self.update_enabled()

    def on_add_clicked(self, sender):
        self.ui["open_window"].show_all()

    def on_file_canceled(self, sender):
        self.ui["open_window"].hide()

    def on_file_opened(self, sender):
        self.ui["open_window"].hide()
        paths = self.ui["open_chooser"].get_filenames()
        self.show_message("Loading Images", "Please wait while PhotoFiddle loads your images…", True, True)
        threading.Thread(target=self.add_images, args=(paths,)).start()


    def on_method_changed(self, sender):
        self.ui["stack"].set_visible_child(self.methodMap[self.ui["method"].get_active_text()].widget)


    def update_enabled(self):
        enabled = len(self.get_paths()) > 0
        self.ui["export_image"].set_sensitive(enabled)
        self.ui["open_pf2"].set_sensitive(enabled)
        self.ui["preview_button"].set_sensitive(enabled)

    def add_images(self, paths):
        c = 0
        for path in paths:
            # Create box
            box = Gtk.HBox()
            box.set_spacing(6)
            im = Gtk.Image()

            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 128, 128, True)
            im.set_from_pixbuf(pb)

            box.add(im)

            label = Gtk.Label()
            label.set_ellipsize(Pango.EllipsizeMode.START)
            label.set_text(path)

            box.add(label)
            box.show_all()
            c += 1
            GLib.idle_add(self.add_image_row, box, c, len(paths))

        GLib.idle_add(self.hide_message)

    def add_image_row(self, row, count, length):
        self.ui["images"].add(row)
        self.update_enabled()
        self.update_message_progress(count, length)


    def on_remove_clicked(self, sender):
        items = self.ui["images"].get_selected_rows()
        for item in items:
            item.destroy()
        self.update_enabled()


    def on_open(self, path):
        self.root.get_titlebar().set_subtitle("High Dynamic Range")
        pass

    def on_exit(self):
        if(not self.exporting):
            self.root.get_titlebar().set_subtitle("")
            self.on_init()
            return True
        return False


    def on_preview_clicked(self, sender):
        self.show_message("Generating Preview…", "PhotoFiddle is preparing to generate a preview", True, True)
        paths = self.get_paths()
        self.method = self.methodMap[self.ui["method"].get_active_text()]
        w = self.ui["scroll_window"].get_allocated_width() - 12
        h = self.ui["scroll_window"].get_allocated_height() - 12
        threading.Thread(target=self.do_preview, args=(paths, w, h)).start()


    def do_stack(self, paths, output, w, h):
        if (not os.path.exists("/tmp/hdr-%s" % getpass.getuser())):
            os.mkdir("/tmp/hdr-%s" % getpass.getuser())


        GLib.idle_add(self.show_message, "HDR Stacking…", "PhotoFiddle is processing images…", True, True)

        length = len(paths)*3
        count = 0
        images = []
        height = 0
        width = 0
        for path in paths:
            GLib.idle_add(self.update_message_progress, count, length)
            im = cv2.imread(path, 2 | 1)
            height, width = im.shape[:2]

            # Get fitting size
            ratio = float(w) / width
            if (height * ratio > h):
                ratio = float(h) / height

            nw = width * ratio
            nh = height * ratio

            count += 1
            GLib.idle_add(self.update_message_progress, count, length)

            im = cv2.resize(im, (int(nw), int(nh)), interpolation=cv2.INTER_AREA)

            count += 1
            GLib.idle_add(self.update_message_progress, count, length)

            cv2.imwrite("/tmp/hdr-%s/IN%i.tiff" % (getpass.getuser(), count), im)
            images += ["/tmp/hdr-%s/IN%i.tiff" % (getpass.getuser(), count),]
            count += 1

        GLib.idle_add(self.show_message, "HDR Stacking…", "PhotoFiddle is aligning images…", True, False)

        stacked_list = self.method.stack(images)

        GLib.idle_add(self.show_message, "HDR Stacking…", "PhotoFiddle is performing an HDR stack…", True, False)

        self.method.run(stacked_list, output, width, height)


        GLib.idle_add(self.hide_message)


    def get_paths(self):
        paths = []
        for item in self.ui["images"].get_children():
            paths += [item.get_children()[0].get_children()[1].get_text(),]

        return paths

    def do_preview(self, paths, w, h):
        self.do_stack(paths, "/tmp/hdr-preview-%s.tiff" % getpass.getuser(), w, h)
        pb = GdkPixbuf.Pixbuf.new_from_file("/tmp/hdr-preview-%s.tiff" % getpass.getuser())
        GLib.idle_add(self.update_preview, pb)

    def update_preview(self, pb):
        self.ui["preview"].set_from_pixbuf(pb)



    def get_export_image(self, w, h):
        GLib.idle_add(self.export_started)
        self.do_stack(self.paths, "/tmp/export-hdr-%s.tiff" % getpass.getuser(), w, h)
        GLib.idle_add(self.show_message, "Exporting…", "PhotoFiddle is exporting the HDR photo…", True, False)

        im = cv2.imread("/tmp/export-hdr-%s.tiff" % getpass.getuser(), 2 | 1)
        return im

    def export_started(self):
        self.exporting = True
        self.export_state_changed()


    def export_complete(self, path):
        self.exporting = False
        self.export_state_changed()
        self.show_message("Export Complete!", "Your photo has been exported to '%s'" % path)

    def export_state_changed(self):
        self.ui["export_image"].set_sensitive(not self.exporting)
        self.ui["open_pf2"].set_sensitive(not self.exporting)
        self.ui["preview_button"].set_sensitive(not self.exporting)


    def export_clicked(self, sender):
        self.method = self.methodMap[self.ui["method"].get_active_text()]
        self.paths = self.get_paths()
        height, width = cv2.imread(self.paths[0]).shape[:2]

        Export.ExportDialog(self.root, self.builder, width, height, self.get_export_image,
                            self.export_complete, self.paths[0])


    def export_pf2_clicked(self, sender):
        self.method = self.methodMap[self.ui["method"].get_active_text()]
        GLib.idle_add(self.export_started)
        self.paths = self.get_paths()
        threading.Thread(target=self.do_export_pf2).start()

    def do_export_pf2(self):
        export_path = "".join(self.paths[0].split(".")[:-1])
        export_path += "_HDR.tiff"
        height, width = cv2.imread(self.paths[0]).shape[:2]
        self.do_stack(self.paths, export_path, width, height)
        GLib.idle_add(self.export_pf2_complete, export_path)

    def export_pf2_complete(self, path):
        self.exporting = False
        self.export_state_changed()
        self.switch_activity("PF2", path)






