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


class FocusStack(Activity.Activity):

    def on_init(self):
        self.id = "FocusStack"
        self.name = "Focus Stack"
        self.subtitle = "Stack Many Images at Different Focus Points"

        UI_FILE = "ui/FocusStack_Activity.glade"
        self.builder.add_from_file(UI_FILE)

        self.widget = self.builder.get_object("FocusStack_main")
        self.stack.add_titled(self.widget, self.id, self.name)

        self.header_widget = self.builder.get_object("FocusStack_header")
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
            "popovermenu"
        ]

        self.paths = []
        self.exporting = False

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
        self.root.get_titlebar().set_subtitle("Focus Stack")
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
        w = self.ui["scroll_window"].get_allocated_width() - 12
        h = self.ui["scroll_window"].get_allocated_height() - 12
        threading.Thread(target=self.do_preview, args=(paths, w, h)).start()


    def do_stack(self, images, output):
        GLib.idle_add(self.show_message, "Focus Stacking…", "PhotoFiddle is aligning images…", True, False)
        if(not os.path.exists("/tmp/stack-%s" % getpass.getuser())):
            os.mkdir("/tmp/stack-%s" % getpass.getuser())

        command = ["align_image_stack", "-m", "-a", "/tmp/stack-%s/OUT_" % getpass.getuser()] + images
        subprocess.call(command)

        aligned_list = glob.glob("/tmp/stack-%s/OUT*.tif" % getpass.getuser())
        aligned_list.reverse()

        GLib.idle_add(self.show_message, "Focus Stacking…", "PhotoFiddle is performing a focus stack…", True, False)

        command = ["enfuse", "--output=/tmp/stacked-%s.tiff" % getpass.getuser(), "--exposure-weight=0",
                   "--saturation-weight=0", "--contrast-weight=1", "--hard-mask",
                   "-v"] + aligned_list

        subprocess.call(command)

        shutil.copyfile("/tmp/stacked-%s.tiff" % getpass.getuser(), output)
        shutil.rmtree("/tmp/stack-%s" % getpass.getuser())
        os.unlink("/tmp/stacked-%s.tiff" % getpass.getuser())

        GLib.idle_add(self.hide_message)


    def get_paths(self):
        paths = []
        for item in self.ui["images"].get_children():
            paths += [item.get_children()[0].get_children()[1].get_text(),]

        return paths

    def do_preview(self, paths, w, h):
        if (not os.path.exists("/tmp/stack-%s" % getpass.getuser())):
            os.mkdir("/tmp/stack-%s" % getpass.getuser())

        length = len(paths)*3
        count = 0
        images = []
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

            cv2.imwrite("/tmp/stack-%s/IN%i.tiff" % (getpass.getuser(),count), im)
            images += ["/tmp/stack-%s/IN%i.tiff" % (getpass.getuser(),count),]
            count += 1

        self.do_stack(images, "/tmp/stack-preview-%s.tiff" % getpass.getuser())
        pb = GdkPixbuf.Pixbuf.new_from_file("/tmp/stack-preview-%s.tiff" % getpass.getuser())
        GLib.idle_add(self.update_preview, pb)

    def update_preview(self, pb):
        self.ui["preview"].set_from_pixbuf(pb)



    def get_export_image(self, w, h):
        GLib.idle_add(self.export_started)
        self.do_stack(self.paths, "/tmp/export-stack-%s.tiff" % getpass.getuser())
        GLib.idle_add(self.show_message, "Exporting…", "PhotoFiddle is exporting the focus stack…", True, False)

        im = cv2.imread("/tmp/export-stack-%s.tiff" % getpass.getuser(), 2 | 1)
        im = cv2.resize(im, (int(w), int(h)), interpolation=cv2.INTER_AREA)
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
        self.paths = self.get_paths()
        height, width = cv2.imread(self.paths[0]).shape[:2]

        Export.ExportDialog(self.root, self.builder, width, height, self.get_export_image,
                            self.export_complete, self.paths[0])


    def export_pf2_clicked(self, sender):
        self.paths = self.get_paths()
        threading.Thread(target=self.do_export_pf2).start()
        self.export_started()

    def do_export_pf2(self):
        export_path = "".join(self.paths[0].split(".")[:-1])
        export_path += "_FocusStack.tiff"
        self.do_stack(self.paths, export_path)
        GLib.idle_add(self.export_pf2_complete, export_path)

    def export_pf2_complete(self, path):
        self.exporting = False
        self.export_state_changed()
        self.switch_activity("PF2", path)






