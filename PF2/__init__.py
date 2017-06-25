import ast
import time
from gi.repository import GLib, Gtk, Gdk, GdkPixbuf
import Activity
import Export
import threading
import cv2
import numpy
import getpass
import os

from PF2 import Histogram, Layer
from PF2.Tools import BlackWhite
from PF2.Tools import Colours
from PF2.Tools import Contrast
from PF2.Tools import Details
from PF2.Tools import Tonemap
from PF2.Tools import HueEqualiser


class PF2(Activity.Activity):

    def on_init(self):
        self.id = "PF2"
        self.name = "Edit a Photo"
        self.subtitle = "Edit a Raster Image with PhotoFiddle"

        UI_FILE = "ui/PF2_Activity.glade"
        self.builder.add_from_file(UI_FILE)

        self.widget = self.builder.get_object("PF2_main")
        self.stack.add_titled(self.widget, self.id, self.name)

        self.header_widget = self.builder.get_object("PF2_header")
        self.header_stack.add_titled(self.header_widget, self.id, self.name)

        # Get all UI Components
        self.ui = {}
        components = [
            "control_reveal",
            "histogram_reveal",
            "layers_reveal",
            "upper_peak_toggle",
            "lower_peak_toggle",
            "histogram",
            "layer_stack",
            "preview",
            "preview_eventbox",
            "scroll_window",
            "open_button",
            "original_toggle",
            "tool_box_stack",
            "tool_stack",
            "open_window",
            "open_header",
            "open_cancel_button",
            "open_open_button",
            "open_chooser",
            "popovermenu",
            "show_hist",
            "export_image",
            "undo",
            "redo",
            "zoom_toggle",
            "zoom_reveal",
            "zoom",
            "reset",
            "mask_draw_toggle",
            "mask_erase_toggle",
            "mask_brush_size",
            "layers_list",
        ]

        for component in components:
            self.ui[component] = self.builder.get_object("%s_%s" % (self.id, component))

        self.menu_popover = self.ui["popovermenu"]

        # Set up tools
        self.tools = [
            Contrast.Contrast,
            Tonemap.Tonemap,
            Details.Details,
            Colours.Colours,
            HueEqualiser.HueEqualiser,
            BlackWhite.BlackWhite
        ]


        # Setup layers
        self.layers = []
        self.base_layer = self.create_layer("base", True)

        # Set the first tool to active
        # self.tools[0].tool_button.set_active(True)
        # self.ui["tools"].show_all()

        # Disable ui components by default
        self.ui["original_toggle"].set_sensitive(False)
        self.ui["export_image"].set_sensitive(False)

        # Setup editor variables
        self.is_editing = False
        self.has_loaded = False
        self.image_path = ""
        self.bit_depth = 8
        self.image = None
        self.original_image = None
        self.pwidth = 0
        self.pheight = 0
        self.awidth = 0
        self.aheight = 0
        self.pimage = None
        self.poriginal = None
        self.change_occurred = False
        self.additional_change_occurred = False
        self.running_stack = False
        self.upper_peak_on = False
        self.lower_peak_on = False
        self.is_exporting = False
        self.is_zooming = False
        self.undo_stack = []
        self.undo_position = 0
        self.undoing = False

        # Setup Open Dialog
        self.ui["open_window"].set_transient_for(self.root)
        self.ui["open_window"].set_titlebar(self.ui["open_header"])

        # Connect UI signals
        self.ui["open_button"].connect("clicked", self.on_open_clicked)
        self.ui["preview"].connect("draw", self.on_preview_draw)
        self.ui["original_toggle"].connect("toggled", self.on_preview_toggled)
        self.ui["upper_peak_toggle"].connect("toggled", self.on_upper_peak_toggled)
        self.ui["lower_peak_toggle"].connect("toggled", self.on_lower_peak_toggled)
        self.ui["show_hist"].connect("toggled", self.toggle_hist)
        self.ui["export_image"].connect("clicked", self.on_export_clicked)
        self.ui["open_open_button"].connect("clicked", self.on_file_opened)
        self.ui["open_cancel_button"].connect("clicked", self.on_file_canceled)
        self.ui["zoom_toggle"].connect("toggled", self.on_zoom_toggled)
        self.ui["zoom"].connect("value-changed", self.on_zoom_changed)
        self.ui["undo"].connect("clicked", self.on_undo)
        self.ui["redo"].connect("clicked", self.on_redo)
        self.ui["reset"].connect("clicked", self.on_reset)

        self.ui["preview_eventbox"].connect('motion-notify-event', self.preview_dragged)
        self.ui["mask_draw_toggle"].connect("toggled", self.mask_draw_toggled)
        self.ui["mask_erase_toggle"].connect("toggled", self.mask_erase_toggled)



    def on_open_clicked(self, sender):
        self.ui["open_window"].show_all()

    def on_file_opened(self, sender, path=None):
        self.has_loaded = False
        self.image = None
        self.undo_position = 0
        self.undo_stack = []
        self.update_undo_state()
        self.ui["open_window"].hide()
        self.ui["control_reveal"].set_reveal_child(True)
        self.ui["control_reveal"].set_sensitive(True)
        self.ui["original_toggle"].set_sensitive(True)
        self.ui["export_image"].set_sensitive(True)
        self.ui["reset"].set_sensitive(True)
        self.is_editing = True
        if(path == None):
            self.image_path = self.ui["open_chooser"].get_filename()
        else:
            self.image_path = path

        w = (self.ui["scroll_window"].get_allocated_width() - 12) * self.ui["zoom"].get_value()
        h = (self.ui["scroll_window"].get_allocated_height() - 12) * self.ui["zoom"].get_value()

        self.show_message("Loading Photo…", "Please wait while PhotoFiddle loads your photo", True)
        self.root.get_titlebar().set_subtitle("%s…" % (self.image_path))

        thread = threading.Thread(target=self.open_image,
                                  args=(w, h))
        thread.start()

    def on_zoom_toggled(self, sender):
        state = sender.get_active()
        self.ui["zoom_reveal"].set_reveal_child(state)
        if(not state):
            self.ui["zoom"].set_value(1)

    def on_zoom_changed(self, sender):
        threading.Thread(target=self.zoom_delay).start()


    def zoom_delay(self):
        if(not self.is_zooming):
            self.is_zooming = True
            time.sleep(0.5)
            GLib.idle_add(self.on_preview_draw, None, None)
            self.is_zooming = False



    def on_file_canceled(self, sender):
        self.ui["open_window"].hide()

    def on_preview_draw(self, sender, arg):
        if(self.is_editing):
            w = (self.ui["scroll_window"].get_allocated_width() - 12) * self.ui["zoom"].get_value()
            h = (self.ui["scroll_window"].get_allocated_height() - 12) * self.ui["zoom"].get_value()
            if(self.pheight != h) or (self.pwidth != w):
                thread = threading.Thread(target=self.resize_preview,
                                          args=(w, h))
                thread.start()

    def on_preview_toggled(self, sender):
        if(sender.get_active()):
            threading.Thread(target=self.draw_hist, args=(self.original_image,)).start()
            self.show_original()
        else:
            threading.Thread(target=self.draw_hist, args=(self.image,)).start()
            self.show_current()

    def toggle_hist(self, sender):
        show = sender.get_active()
        self.ui["histogram_reveal"].set_reveal_child(show)


    def on_open(self, path):
        self.root.get_titlebar().set_subtitle("Raster Editor")
        if(path != None):
            # We have been sent here from another
            # activity, clear any existing profiles
            self.image_path = path
            dataPath = self.get_data_path()
            if(os.path.exists(dataPath)):
                os.unlink(dataPath)

            self.on_file_opened(None, path)

    def on_exit(self):
        if(self.is_exporting):
            return False
        else:
            fname = "/tmp/phf2-preview-%s.png" % getpass.getuser()
            if (os.path.exists(fname)):
                os.unlink(fname)

            self.root.get_titlebar().set_subtitle("")
            self.on_init()
            return True


    def show_original(self):
        self.ui["preview"].set_from_pixbuf(self.poriginal)
        if (not self.ui["original_toggle"].get_active()):
            self.ui["original_toggle"].set_active(True)

    def show_current(self):
        self.ui["preview"].set_from_pixbuf(self.pimage)
        if (self.ui["original_toggle"].get_active()):
            self.ui["original_toggle"].set_active(False)


    def on_layer_change(self, layer):
        if(self.has_loaded):
            if(not self.change_occurred):
                self.change_occurred = True
                thread = threading.Thread(target=self.update_image)
                thread.start()
            else:
                self.additional_change_occurred = True

    def on_lower_peak_toggled(self, sender):
        self.lower_peak_on = sender.get_active()
        if (self.lower_peak_on):
            thread = threading.Thread(target=self.process_peaks, args=(True,))
            thread.start()
        else:
            thread = threading.Thread(target=self.update_image, args=(True,))
            thread.start()

    def on_upper_peak_toggled(self, sender):
        self.upper_peak_on = sender.get_active()
        if (self.lower_peak_on):
            thread = threading.Thread(target=self.process_peaks, args=(True,))
            thread.start()
        else:
            thread = threading.Thread(target=self.update_image, args=(True,))
            thread.start()

    def image_opened(self, depth):
        self.root.get_titlebar().set_subtitle("%s (%s Bit)" % (self.image_path, depth))
        self.hide_message()


    def on_export_clicked(self, sender):
        Export.ExportDialog(self.root, self.builder, self.awidth, self.aheight, self.get_export_image, self.on_export_complete, self.image_path)

    def on_export_complete(self, filename):
        self.is_exporting = False
        self.on_export_state_change()
        self.show_message("Export Complete!", "Your photo has been exported to '%s'" % filename)

    def on_export_state_change(self):
        self.ui["control_reveal"].set_sensitive(not self.is_exporting)
        self.ui["export_image"].set_sensitive(not self.is_exporting)
        self.ui["open_button"].set_sensitive(not self.is_exporting)

    def on_export_started(self):
        self.is_exporting = True
        self.on_export_state_change()

    def update_undo_state(self):
        self.ui["undo"].set_sensitive(self.undo_position > 0)
        self.ui["redo"].set_sensitive(len(self.undo_stack)-1 > self.undo_position)

    def on_undo(self, sender):
        self.undo_position -= 1
        self.update_undo_state()
        self.update_from_undo_stack(self.undo_stack[self.undo_position])

    def on_redo(self, sender):
        self.undo_position += 1
        self.update_undo_state()
        self.update_from_undo_stack(self.undo_stack[self.undo_position])

    def on_reset(self, sender):
        for tool in self.tools:
            tool.reset()



    ## Background Tasks ##
    def open_image(self, w, h):
        self.load_image_data()
        try:
            self.resize_preview(w, h)
        except:
            pass
        while(self.image == None):
            time.sleep(1)
        GLib.idle_add(self.image_opened, str(self.image.dtype).replace("uint", "").replace("float", ""))
        time.sleep(1)
        self.has_loaded = True



    def resize_preview(self, w, h):
        # Inhibit undo stack to prevent
        # Adding an action on resize
        self.undoing = True

        self.original_image = cv2.imread(self.image_path, 2 | 1)
        height, width = self.original_image.shape[:2]

        self.aheight = height
        self.awidth = width

        self.pheight = h
        self.pwidth = w

        # Get fitting size
        ratio = float(w)/width
        if(height*ratio > h):
            ratio = float(h)/height

        nw = width * ratio
        nh = height * ratio

        # Do quick ui resize
        if(self.image != None) and (os.path.exists("/tmp/phf2-preview-%s.png" % getpass.getuser())):
            # If we have an edited version, show that
            self.pimage = GdkPixbuf.Pixbuf.new_from_file_at_scale("/tmp/phf2-preview-%s.png" % getpass.getuser(),
                                                                         int(nw), int(nh), True)
            GLib.idle_add(self.show_current)

        self.poriginal = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.image_path,
                                                            int(nw), int(nh), True)
        if(self.image == None):
            # Otherwise show the original
            GLib.idle_add(self.show_original)


        # Resize OPENCV Copy
        self.original_image = cv2.resize(self.original_image, (int(nw), int(nh)), interpolation = cv2.INTER_AREA)

        self.image = numpy.copy(self.original_image)

        # Update image
        if (not self.change_occurred):
            self.change_occurred = True
            self.update_image()
        else:
            self.additional_change_occurred = True

    def update_image(self, immediate=False):
        if(not immediate):
            time.sleep(0.5)
        self.additional_change_occurred = False
        GLib.idle_add(self.start_work)
        self.image = numpy.copy(self.original_image)
        self.image = self.run_stack(self.image)
        if(self.additional_change_occurred):
            self.update_image()
        else:
            self.save_image_data()
            self.draw_hist(self.image)
            self.process_peaks()
            self.update_preview()
            GLib.idle_add(self.stop_work)
            self.change_occurred = False
            self.undoing = False



    def run_stack(self, image, callback=None):
        if(not self.running_stack):
            self.running_stack = True

            baseImage = image.copy()

            for layer in self.layers:
                print(layer)
                image = layer.render_layer(baseImage, image, callback)

            self.running_stack = False
            return image

        else:
            while(self.running_stack):
                time.sleep(1)

            return self.run_stack(image, callback)

    def update_preview(self):
        fname = "/tmp/phf2-preview-%s.png" % getpass.getuser()
        if(os.path.exists(fname)):
            os.unlink(fname)
        cv2.imwrite(fname, self.image)
        self.pimage = GdkPixbuf.Pixbuf.new_from_file(fname)
        GLib.idle_add(self.show_current)

    def draw_hist(self, image):
        path = "/tmp/phf2-hist-%s.png" % getpass.getuser()
        Histogram.Histogram.draw_hist(image, path)
        GLib.idle_add(self.update_hist_ui, path)

    def update_hist_ui(self, path):
        try:
            self.ui["histogram"].set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(path))
        except:
            pass


    def process_peaks(self, do_update=False):
        bpp = float(str(self.image.dtype).replace("uint", "").replace("float", ""))
        if(self.upper_peak_on):
            self.image[(self.image == 2 ** bpp - 1).all(axis=2)] = 1
        if(self.lower_peak_on):
            self.image[(self.image == 0).all(axis=2)] = 2 ** bpp - 2

        if(do_update):
            self.update_preview()


    ## FILE STUFF ##

    def get_data_path(self):
        return "%s/.%s.pf2" % ("/".join(self.image_path.split("/")[:-1]), self.image_path.split("/")[-1:][0])

    def save_image_data(self):
        path = self.get_data_path()
        print(path)
        f = open(path, "w")

        layerDict = {}
        for layer in self.layers:
            layerDict[layer.name] = layer.get_layer_dict()

        if(not self.undoing) and (self.has_loaded):
            if(len(self.undo_stack)-1 != self.undo_position):
                self.undo_stack = self.undo_stack[:self.undo_position+1]
            if(self.undo_stack[self.undo_position] != layerDict):
                self.undo_stack += [layerDict,]
                self.undo_position = len(self.undo_stack)-1
                GLib.idle_add(self.update_undo_state)

        data = {
            "path":self.image_path,
            "format-revision":1,
            "layers": layerDict
        }

        f.write(str(data))
        f.close()

    def load_image_data(self):
        path = self.get_data_path()
        loadDefaults = True
        if(os.path.exists(path)):
            f = open(path, 'r')
            sdata = f.read()
            if(True):
            #try:
                data = ast.literal_eval(sdata)
                if(data["format-revision"] == 1):
                    for layer in data["layers"]:
                        if(layer == "base"):
                            self.base_layer.set_from_layer_dict(data["layers"][layer])
                        else:
                            ilayer = self.create_layer(layer, False)
                            ilayer.set_from_layer_dict(data["layers"][layer])

                    self.undo_stack = [data["layers"],]
                    self.undo_position = 0
                    loadDefaults = False
            #except:
            #    GLib.idle_add(self.show_message,"Unable to load previous edits…",
            #                                    "The edit file for this photo is corrupted and could not be loaded.")

        if(loadDefaults):
            for layer in self.layers:
                for tool in layer.tools:
                    GLib.idle_add(tool.reset)

            layerDict = {}
            for layer in self.layers:
                layerDict[layer.name] = layer.get_layer_dict()

            self.undo_stack = [layerDict, ]
            self.undo_position = 0

        GLib.idle_add(self.update_undo_state)
        time.sleep(2)
        self.undoing = False


    def update_from_undo_stack(self, data):
        self.undoing = True
        for layer in data:
            if (layer == "base"):
                self.base_layer.set_from_layer_dict(data[layer])
            else:
                ilayer = self.create_layer(layer, False)
                ilayer.set_from_layer_dict(data[layer])


    def get_export_image(self, w, h):
        GLib.idle_add(self.on_export_started)
        GLib.idle_add(self.show_message, "Exporting Photo", "Please wait…", True, True)
        img = cv2.imread(self.image_path, 2 | 1)
        img = cv2.resize(img, (int(w), int(h)), interpolation=cv2.INTER_AREA)
        img = self.run_stack(img, self.export_progress_callback)
        GLib.idle_add(self.show_message, "Exporting Photo", "Saving to filesystem…", True, True)
        GLib.idle_add(self.update_message_progress, 1, 1)
        return img

    def export_progress_callback(self, name, count, current):
        GLib.idle_add(self.show_message, "Exporting Photo", "Processing: %s" % name, True, True)
        GLib.idle_add(self.update_message_progress, current, count)



    ## Layers Stuff ##

    def preview_dragged(self, widget, event):
        print(event.x, event.y)

    def mask_draw_toggled(self, widget):
        if(widget.get_active()):
            self.ui["mask_erase_toggle"].set_active(False)

    def mask_erase_toggled(self, widget):
        if(widget.get_active()):
            self.ui["mask_draw_toggle"].set_active(False)


    def create_layer(self, layer_name, is_base):
        layer = Layer.Layer(is_base, layer_name, self.on_layer_change)
        for tool in self.tools:
            tool_instance = tool()
            layer.add_tool(tool_instance)

        self.layers += [layer,]

        self.create_layer_ui(layer)

        return layer

    def create_layer_ui(self, layer):
        layer_box = Gtk.HBox()
        layer_toggle = Gtk.CheckButton()
        layer_toggle.set_sensitive(not layer.editable)
        layer_toggle.set_active(layer.enabled)
        layer_label = Gtk.Label()
        layer_label.set_label(layer.name)

        layer_box.add(layer_toggle)
        layer_box.add(layer_label)

        self.ui["layers_list"].add(layer_box)

        self.ui["tool_box_stack"].add(layer.tool_box)
        self.ui["tool_stack"].add(layer.tool_stack)