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

import Activity.Mask.Mask as Mask

import numpy

import Activity.Mask.Inpaint as Inpaint


class Inpainter(Activity.Activity):

    def on_init(self):

        UI_FILE = "ui/Mask_Activity.glade"
        self.builder.add_from_file(UI_FILE)
        print(UI_FILE)

        self.widget = self.builder.get_object("Mask_main")
        self.stack.add_titled(self.widget, self.id, self.name)

        self.header_widget = self.builder.get_object("Mask_header")
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
            "open",
            "popovermenu",
            "toolbar",
            "scroll_window",
            "preview",
            "mask_draw_toggle",
            "mask_erase_toggle",
            "preview_eventbox",
            "scroll_window",
            "mask_brush_size",
            "preview_button"
        ]

        self.paths = []
        self.exporting = False

        for component in components:
            self.ui[component] = self.builder.get_object("Mask_%s" % component))

        self.menu_popover = self.ui["popovermenu"]

        self.image_readonly = None
        self.image = None
        self.image_pb = None
        self.mousedown = False

        self.mask = None
        self.current_path = None
        self.actual_width = 0

        self.ui["open_window"].set_transient_for(self.root)
        self.ui["open_window"].set_titlebar(self.ui["open_header"])
        self.ui["open_open_button"].connect("clicked", self.on_file_opened)
        self.ui["open_cancel_button"].connect("clicked", self.on_file_canceled)
        self.ui["preview_eventbox"].connect('motion-notify-event', self.preview_dragged)
        self.ui["preview_eventbox"].connect('button-press-event', self.new_path)
        self.ui["scroll_window"].connect_after("draw", self.draw_ui_brush_circle)
        self.ui["scroll_window"].connect_after('motion-notify-event', self.mouse_coords_changed)
        self.ui["preview_button"].connect("clicked", self.create_preview)

        self.ui["open"].connect("clicked", self.on_open_clicked)

        self.update_enabled()


    def update_enabled(self):
        self.ui["toolbar"].set_sensitive(type(self.image) == numpy.ndarray)
        self.ui["preview_button"].set_sensitive(type(self.image) == numpy.ndarray)

    def on_open_clicked(self, sender):
        self.ui["open_window"].show_all()

    def on_file_canceled(self, sender):
        self.ui["open_window"].hide()

    def on_file_opened(self, sender):
        self.ui["open_window"].hide()
        path = self.ui["open_chooser"].get_filename()
        threading.Thread(target=self.load_image, args=(path,)).start()


    def load_image(self, path):
        self.get_sized_image(path)
        self.root.get_titlebar().set_subtitle("%s" % path)


    def get_sized_image(self, path):
        self.start_work()
        w = self.ui["scroll_window"].get_allocated_width() - 12
        h = self.ui["scroll_window"].get_allocated_height() - 12
        threading.Thread(target=self.get_preview_image, args=(path, w, h)).start()


    def get_preview_image(self, path, w, h):
        if (not os.path.exists("/tmp/inpainter-%s" % getpass.getuser())):
            os.mkdir("/tmp/inpainter-%s" % getpass.getuser())

        im = cv2.imread(path, 2 | 1)
        height, width = im.shape[:2]

        self.actual_width = width

        # Get fitting size
        ratio = float(w) / width
        if (height * ratio > h):
            ratio = float(h) / height

        nw = width * ratio
        nh = height * ratio

        im = cv2.resize(im, (int(nw), int(nh)), interpolation=cv2.INTER_AREA)

        
        self.image = im
        self.image_readonly = im.copy()
        self.mask = Mask.Mask(im, width, height)
        self.update_preview(im)

    def update_preview(self, image):
        cv2.imwrite("/tmp/inpainter-%s/pre-preview.tiff" % getpass.getuser(), image)
        pb = GdkPixbuf.Pixbuf.new_from_file("/tmp/inpainter-%s/pre-preview.tiff" % getpass.getuser())
        shutil.rmtree("/tmp/inpainter-%s" % getpass.getuser())
        self.image_pb = pb
        GLib.idle_add(self.set_pixbuf)

    def set_pixbuf(self):
        self.ui["preview"].set_from_pixbuf(self.image_pb)
        self.stop_work()
        self.update_enabled()

    
    def preview_dragged(self, widget, event):

        x, y = widget.translate_coordinates(self.ui["preview"], event.x, event.y)

        draw = self.ui["mask_draw_toggle"].get_active()
        erase = self.ui["mask_erase_toggle"].get_active()
        if((draw or erase) and self.current_path):

            if (x < 0.0):
                x = 0
            if (y < 0.0):
                y = 0

            pwidth = self.image_pb.get_width()
            pheight = self.image_pb.get_height()

            if (x > pwidth):
                x = pwidth
            if (y > pheight):
                y = pheight

            print(x, y)

            fill = (0, 0, 255)
            if(erase):
                fill = (255, 0, 0)

            self.draw_path(x, y, pheight, pwidth, fill)

            self.on_mask_change()

            self.mouse_down_coords_changed(widget, event)
            return True


    def draw_path(self, x, y, pheight, pwidth, fill):
        preview = self.current_path.add_point(int(x), int(y), (pheight, pwidth, 3), fill)

        # Bits per pixel
        bpp = float(str(self.image.dtype).replace("uint", "").replace("float", ""))
        # Pixel value range
        np = float(2 ** bpp - 1)

        self.image[preview == 255] = np
        cv2.imwrite("/dev/shm/inpaint-preview-%s-drag.png" % getpass.getuser(), self.image)
        temppbuf = GdkPixbuf.Pixbuf.new_from_file("/dev/shm/inpaint-preview-%s-drag.png" % getpass.getuser())
        self.ui["preview"].set_from_pixbuf(temppbuf)


    def new_path(self, widget, event):
        draw = self.ui["mask_draw_toggle"].get_active()
        erase = self.ui["mask_erase_toggle"].get_active()
        if(draw or erase):
            print(self.image_pb.get_width(), self.image_pb.get_height())
            width = self.image_pb.get_width()
            size = self.ui["mask_brush_size"].get_value()
            feather = 0
            self.current_path = self.mask.mask.get_new_path(size, feather, float(self.actual_width)/float(width), draw)

    
    def mouse_coords_changed(self, widget, event):
        self.mousedown = False
        self.mousex, self.mousey = event.x, event.y
        widget.queue_draw()

    def mouse_down_coords_changed(self, widget, event):
        self.mousedown = True
        self.mousex, self.mousey = widget.translate_coordinates(self.ui["scroll_window"], event.x, event.y)
        widget.queue_draw()


    def draw_ui_brush_circle(self, widget, context):
        if(type(self.image) == numpy.ndarray):
            size = self.ui["mask_brush_size"].get_value()
            if(self.mousedown):
                context.set_source_rgb(255, 0, 0)
            else:
                context.set_source_rgb(255, 255, 255)
            context.arc(self.mousex, self.mousey, size/2.0, 0.0, 2 * numpy.pi)
            context.stroke()


    def on_mask_change(self):
        threading.Thread(target=self.__on_mask_change).start()

    def __on_mask_change(self):
        image = self.image_readonly.copy()
        image = self.mask.get_mask_preview(image)
        self.image = image
        self.update_preview(image)
