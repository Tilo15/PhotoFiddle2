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


class LightStack(Activity.Activity):

    def on_init(self):
        self.id = "LightStack"
        self.name = "Light Stack"
        self.subtitle = "Stack Many Images to Make Light Trails"

        UI_FILE = "ui/LightStack_Activity.glade"
        self.builder.add_from_file(UI_FILE)

        self.widget = self.builder.get_object("LightStack_main")
        self.stack.add_titled(self.widget, self.id, self.name)

        self.header_widget = self.builder.get_object("LightStack_header")
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
        self.root.get_titlebar().set_subtitle("Light Stack")
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


    def do_stack(self, images):

        GLib.idle_add(self.show_message, "Light Stacking…", "PhotoFiddle is performing a light stack…", True, True)
        GLib.idle_add(self.update_message_progress, 0,1)

        im = cv2.imread(images[0], 2 | 1)
        bpp = int(str(im.dtype).replace("uint", "").replace("float", ""))
        np = float(2 ** bpp - 1)
        c = 1
        GLib.idle_add(self.update_message_progress, c, len(images))
        try:
            for f in images[1:]:
                layer= cv2.imread(f, 2 | 1)
                im[layer > im] = layer[layer > im]
                im[im < 0.0] = 0.0
                im[im > np] = np
                c += 1
                GLib.idle_add(self.update_message_progress, c, len(images))

            GLib.idle_add(self.hide_message)
            return im
        except:
            GLib.idle_add(self.show_message, "Stack Failed.", "All images in the stack must be the same size.", False, False)
            raise Exception()


    def get_paths(self):
        paths = []
        for item in self.ui["images"].get_children():
            paths += [item.get_children()[0].get_children()[1].get_text(),]

        return paths

    def do_preview(self, paths, w, h):
        if (not os.path.exists("/tmp/lightstack-%s" % getpass.getuser())):
            os.mkdir("/tmp/lightstack-%s" % getpass.getuser())

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

            cv2.imwrite("/tmp/lightstack-%s/IN%i.tiff" % (getpass.getuser(),count), im)
            images += ["/tmp/lightstack-%s/IN%i.tiff" % (getpass.getuser(),count),]
            count += 1

        im = self.do_stack(images)
        cv2.imwrite("/tmp/lightstack-preview-%s.tiff" % getpass.getuser(), im)
        pb = GdkPixbuf.Pixbuf.new_from_file("/tmp/lightstack-preview-%s.tiff" % getpass.getuser())
        shutil.rmtree("/tmp/lightstack-%s" % getpass.getuser())
        GLib.idle_add(self.update_preview, pb)

    def update_preview(self, pb):
        self.ui["preview"].set_from_pixbuf(pb)



    def get_export_image(self, w, h):
        GLib.idle_add(self.export_started)
        im = self.do_stack(self.paths)
        GLib.idle_add(self.show_message, "Exporting…", "PhotoFiddle is exporting the light stack…", True, False)

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
        GLib.idle_add(self.export_started)
        self.paths = self.get_paths()
        threading.Thread(target=self.do_export_pf2).start()

    def do_export_pf2(self):
        export_path = "".join(self.paths[0].split(".")[:-1])
        export_path += "_LightStack.tiff"
        im = self.do_stack(self.paths)
        GLib.idle_add(self.show_message, "Sending to Editor", "Exporting photo to the editor…", True)
        cv2.imwrite(export_path, im)
        GLib.idle_add(self.export_pf2_complete, export_path)

    def export_pf2_complete(self, path):
        self.exporting = False
        self.export_state_changed()
        self.switch_activity("PF2", path)






