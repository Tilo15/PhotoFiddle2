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
import traceback
import uuid

from PF2 import Histogram, Layer
from PF2.Tools import BlackWhite
from PF2.Tools import Colours
from PF2.Tools import Contrast
from PF2.Tools import Details
from PF2.Tools import Tonemap
from PF2.Tools import HueEqualiser
from PF2.Tools import Blur


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
            "main",
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
            "new_layer",
            "layer_mask_reveal",
            "add_layer_button",
            "remove_layer_button",
            "mask_brush_feather",
            "mask_brush_feather_scale",
            "edit_layer_mask_button",
            "layer_opacity",
            "layer_opacity_scale",
            "layer_blend_mode",
            "viewport"
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
            BlackWhite.BlackWhite,
            Blur.Blur
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
        self.image_is_dirty = True
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
        self.current_layer_path = None
        self.mousex = 0
        self.mousey = 0
        self.mousedown = False
        self.layer_order = []
        self.pre_undo_layer_name = "base"
        self.pre_undo_editing = False
        self.pre_undo_erasing = False
        self.last_selected_layer = None
        self.was_editing_mask = False
        self.source_image = None
        self.is_scaling = False
        self.current_processing_layer_name = "base"
        self.current_processing_layer_index = 0
        self.update_image_task_id = ""

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
        self.ui["preview_eventbox"].connect('button-press-event', self.new_path)
        self.ui["mask_draw_toggle"].connect("toggled", self.mask_draw_toggled)
        self.ui["mask_erase_toggle"].connect("toggled", self.mask_erase_toggled)
        self.ui["new_layer"].connect("clicked", self.new_layer_button_clicked)
        self.ui["layers_list"].connect("row-activated", self.layer_ui_activated)
        self.ui["add_layer_button"].connect("clicked", self.new_layer_button_clicked)
        self.ui["remove_layer_button"].connect("clicked", self.remove_layer_button_clicked)
        self.ui["edit_layer_mask_button"].connect("toggled", self.edit_mask_toggled)
        self.ui["layer_opacity"].connect("value-changed", self.update_layer_opacity)
        self.ui["scroll_window"].connect_after("draw", self.draw_ui_brush_circle)
        self.ui["scroll_window"].connect_after('motion-notify-event', self.mouse_coords_changed)
        self.ui["mask_brush_size"].connect("value-changed", self.brush_size_changed)
        self.ui["layer_blend_mode"].connect("changed", self.layer_blend_mode_changed)



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
        self.ui["new_layer"].set_sensitive(True)
        self.ui["layers_reveal"].set_reveal_child(False)
        self.is_editing = True
        if(path == None):
            self.image_path = self.ui["open_chooser"].get_filename()
        else:
            self.image_path = path

        self.show_message("Loading Photo…", "Please wait while PhotoFiddle loads your photo", True)
        self.root.get_titlebar().set_subtitle("%s…" % (self.image_path))

        # Delete all layers, except the base
        for layer in self.layers:
            if(layer.name != "base"):
                self.ui["layers_list"].remove(layer.selector_row)

        self.layers = [self.base_layer,]

        self.select_layer(self.base_layer)

        w = (self.ui["scroll_window"].get_allocated_width() - 12) * self.ui["zoom"].get_value()
        h = (self.ui["scroll_window"].get_allocated_height() - 12) * self.ui["zoom"].get_value()
        
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
        # TODO remove
        cv2.namedWindow( "Display window", cv2.WINDOW_AUTOSIZE );
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
            fname = "/dev/shm/phf2-preview-%s.png" % getpass.getuser()
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
        print(layer, "changed")
        if(self.has_loaded):
            if(not self.change_occurred):
                self.change_occurred = True
                thread = threading.Thread(target=self.update_image, args=(False, layer))
                thread.start()
            else:
                self.additional_change_occurred = True

    def on_layer_mask_change(self, layer):
        if(self.has_loaded):
            if(not self.change_occurred):
                self.change_occurred = True
                threading.Thread(target=self.__on_layer_mask_change).start()
                self.save_image_data()

    def __on_layer_mask_change(self):
        image = self.get_selected_layer().layer_copy.copy()
        image = self.get_selected_layer().get_layer_mask_preview(image)
        self.image_is_dirty = True
        self.image = image
        self.update_preview()
        self.change_occurred = False
        self.image_is_dirty = False


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

    def image_opened(self): 
        self.root.get_titlebar().set_subtitle("%s (%s Bit)" % (self.image_path, self.bit_depth))
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
        self.ui["undo"].set_sensitive((self.undo_position > 0) and (not self.is_working))
        self.ui["redo"].set_sensitive((len(self.undo_stack)-1 > self.undo_position)  and (not self.is_working))

    def on_undo(self, sender):
        self.pre_undo_layer_name = self.get_selected_layer().name
        self.pre_undo_erasing = self.ui["mask_erase_toggle"].get_active()
        self.pre_undo_editing = self.ui["edit_layer_mask_button"].get_active()
        self.undo_position -= 1
        self.update_undo_state()
        self.update_from_undo_stack(self.undo_stack[self.undo_position])

    def on_redo(self, sender):
        self.pre_undo_layer_name = self.get_selected_layer().name
        self.pre_undo_erasing = self.ui["mask_erase_toggle"].get_active()
        self.pre_undo_editing = self.ui["edit_layer_mask_button"].get_active()
        self.undo_position += 1
        self.update_undo_state()
        self.update_from_undo_stack(self.undo_stack[self.undo_position])

    def on_reset(self, sender):
        for layer in self.layers:
            layer.reset_tools()



    ## Background Tasks ##
    def open_image(self, w, h):

        self.load_image_data()
        try:
            # Get Bit Depth
            imdepth = cv2.imread(self.image_path, 2 | 1)
            self.bit_depth = str(imdepth.dtype).replace("uint", "").replace("float", "")

            # Read the 8Bit Preview
            self.source_image = cv2.imread(self.image_path).astype(numpy.uint8)
            
            # Load the image
            self.resize_preview(w, h)
        except:
            pass
        while(type(self.image) != numpy.ndarray):
            time.sleep(1)
            
        self.pwidth = 0
        self.pheight = 0
           
        GLib.idle_add(self.image_opened)
        time.sleep(1)
        self.has_loaded = True



    def resize_preview(self, w, h):
        print(w, h)
        if(type(self.source_image) == numpy.ndarray):
            # Inhibit undo stack to prevent
            # Adding an action on resize
            self.undoing = True



            self.original_image = self.source_image.copy()

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
            # if(self.image != None):
            #     # If we have an edited version, show that
            #     image = cv2.resize(self.image, (int(nw), int(nh)), interpolation=cv2.INTER_NEAREST)
            #     self.pimage = self.pimage = self.create_pixbuf(image)
            #     GLib.idle_add(self.show_current)

            if(type(self.pimage) == numpy.ndarray and not self.is_scaling):
                self.is_scaling = True
                # If we have an edited version, show that
                image = self.pimage.scale_simple(int(nw), int(nh), GdkPixbuf.InterpType.NEAREST)
                self.pimage = image
                GLib.idle_add(self.show_current)
                self.is_scaling = False

            self.poriginal = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.image_path,
                                                                int(nw), int(nh), True)
            if(type(self.pimage) != numpy.ndarray):
                # Otherwise show the original
                GLib.idle_add(self.show_original)


            # Resize OPENCV Copy
            self.original_image = cv2.resize(self.original_image, (int(nw), int(nh)), interpolation = cv2.INTER_AREA)

            self.image_is_dirty = True

            self.image = self.original_image.copy()

            # Update image
            if (not self.change_occurred):
                self.change_occurred = True
                self.update_image()
            else:
                self.additional_change_occurred = True



    def update_image(self, immediate=False, changed_layer=None):
        if(not immediate):
            time.sleep(0.5)
        self.additional_change_occurred = False
        self.is_working = True
        GLib.idle_add(self.update_undo_state)
        GLib.idle_add(self.start_work)
        image = numpy.copy(self.original_image)
        rst = time.time()
        task_id = uuid.uuid4()
        self.update_image_task_id = task_id
        image = self.run_stack(image, changed_layer=changed_layer)
        if(task_id == self.update_image_task_id):
            self.image = image
            if(type(self.image) != numpy.ndarray):
                GLib.idle_add(self.stop_work)
                self.is_working = False
                self.change_occurred = False
                GLib.idle_add(self.update_undo_state)
                print("self.image == None")
                GLib.idle_add(self.show_message, "Image Render Failed…",
                              "PhotoFiddle encountered an internal error and was unable to render the image… Please try again.")
                raise Exception()

            self.process_mask()
            self.image_is_dirty = False
            if(self.additional_change_occurred):
                self.update_image()
            else:
                self.save_image_data()
                threading.Thread(target=self.draw_hist, args=(self.image,)).start()

                self.process_peaks()
                self.update_preview()
                GLib.idle_add(self.stop_work)
                self.is_working = False
                GLib.idle_add(self.update_undo_state)
                self.change_occurred = False
                self.undoing = False



    def run_stack(self, image, callback=None, changed_layer=None):
        if(not self.running_stack):
            self.running_stack = True

            baseImage = image.copy()

            try:

                image = None

                carry = True
                if(type(self.image) == numpy.ndarray) and (baseImage.shape == self.image.shape) and (changed_layer != None) and (changed_layer in self.layers):
                    changed_layer_index = self.layers.index(changed_layer)
                    if(changed_layer_index > 0):
                        carry = False
                        layer_under = self.layers[changed_layer_index -1]
                        image = layer_under.layer_copy.copy()
                        for layer in self.layers[changed_layer_index: ]:
                            self.current_processing_layer_name = layer.name
                            self.current_processing_layer_index = self.layers.index(layer)
                            if(self.additional_change_occurred):
                                break
                            print(layer)
                            image = layer.render_layer(baseImage, image, callback)


                if(carry):
                    for layer in self.layers:
                        self.current_processing_layer_name = layer.name
                        self.current_processing_layer_index = self.layers.index(layer)
                        if (self.additional_change_occurred):
                            break
                        print(layer)
                        image = layer.render_layer(baseImage, image, callback)




                self.running_stack = False
                return image

            except Exception as e:
                print(e)
                traceback.print_exc()
                GLib.idle_add(self.show_message, "Image Render Failed…",
                              "PhotoFiddle encountered an internal error and was unable to render the image.")


        else:
            while(self.running_stack):
                time.sleep(1)

            return self.run_stack(image, callback)

    def update_preview(self):
        image = self.create_pixbuf(self.image)
        self.pimage = image
        GLib.idle_add(self.show_current)



    def create_pixbuf(self, im):
        pb = None
        write_id = uuid.uuid4()
        cv2.imwrite("/dev/shm/phf2-preview-%s-update.png" % write_id, im)
        pb = GdkPixbuf.Pixbuf.new_from_file("/dev/shm/phf2-preview-%s-update.png" % write_id)
        os.unlink("/dev/shm/phf2-preview-%s-update.png" % write_id)

        return pb


    def draw_hist(self, image):
        path = "/dev/shm/phf2-hist-%s.png" % getpass.getuser()
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

    def process_mask(self, do_update=False):
        if(self.ui["edit_layer_mask_button"].get_active()):
            self.image = self.get_selected_layer().get_layer_mask_preview(self.image)

        if (do_update):
            self.update_preview()



    ## FILE STUFF ##

    def get_data_path(self):
        return "%s/.%s.pf2" % ("/".join(self.image_path.split("/")[:-1]), self.image_path.split("/")[-1:][0])

    def save_image_data(self):
        path = self.get_data_path()
        print(path)
        f = open(path, "w")

        layerDict = {}
        layerOrder = []
        for layer in self.layers:
            layerDict[layer.name] = layer.get_layer_dict()
            layerOrder.append(layer.name)

        if(not self.undoing) and (self.has_loaded):
            if(len(self.undo_stack)-1 != self.undo_position):
                self.undo_stack = self.undo_stack[:self.undo_position+1]
            if(self.undo_stack[self.undo_position] != {"layers": layerDict, "layer-order": layerOrder}):
                self.undo_stack += [{"layers": layerDict, "layer-order": layerOrder},]
                self.undo_position = len(self.undo_stack)-1
                GLib.idle_add(self.update_undo_state)


        data = {
            "path":self.image_path,
            "format-revision":1,
            "layers": layerDict,
            "layer-order": layerOrder
        }

        f.write(str(data))
        f.close()

    def load_image_data(self):
        path = self.get_data_path()
        loadDefaults = True
        if(os.path.exists(path)):
            f = open(path, 'r')
            sdata = f.read()
            try:
                data = ast.literal_eval(sdata)
                if(data["format-revision"] == 1):
                    if("layer-order" not in data):
                        # Backwards compatability
                        data["layer-order"] = ["base",]
                    for layer_name in data["layer-order"]:
                        GLib.idle_add(self.create_layer_with_data, layer_name, data["layers"][layer_name])

                    self.undo_stack = [data,]
                    self.undo_position = 0
                    loadDefaults = False
            except:
                GLib.idle_add(self.show_message,"Unable to load previous edits…",
                                                "The edit file for this photo is corrupted and could not be loaded.")

        if(loadDefaults):
            for layer in self.layers:
                for tool in layer.tools:
                    GLib.idle_add(tool.reset)

            layerDict = {}
            layerOrder = []
            for layer in self.layers:
                layerDict[layer.name] = layer.get_layer_dict()
                layerOrder.append(layer.name)


            self.undo_stack = [{"layers": layerDict, "layer-order": layerOrder}, ]
            self.undo_position = 0

        GLib.idle_add(self.update_undo_state)
        #time.sleep(2)
        self.undoing = False


    def create_layer_with_data(self, layer, data):
        if (layer == "base"):
            self.base_layer.set_from_layer_dict(data)
        else:
            GLib.idle_add(self.show_layers)
            ilayer = self.create_layer(layer, False)
            ilayer.set_from_layer_dict(data)


    def update_from_undo_stack(self, data):
        self.undoing = True
        self.delete_all_editable_layers()
        print(data["layer-order"])
        for layer_name in data["layer-order"]:
            if (layer_name == "base"):
                self.base_layer.set_from_layer_dict(data["layers"][layer_name])
            else:
                ilayer = self.create_layer(layer_name, False, layer_name == self.pre_undo_layer_name, True)
                ilayer.set_from_layer_dict(data["layers"][layer_name])
                self.show_layers()



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
        layer_name = self.current_processing_layer_name
        if(layer_name == "base"):
            layer_name = "Base Layer"
        GLib.idle_add(self.show_message, "Exporting Photo", "%s: %s" % (layer_name,
                                                                                    name), True, True)
        GLib.idle_add(self.update_message_progress, current+(self.current_processing_layer_index*count),
                      count*len(self.layers))



    ## Layers Stuff ##

    def preview_dragged(self, widget, event):

        x, y = widget.translate_coordinates(self.ui["preview"], event.x, event.y)

        draw = self.ui["mask_draw_toggle"].get_active()
        erase = self.ui["mask_erase_toggle"].get_active()
        layer = self.get_selected_layer()
        if((draw or erase) and layer.editable and self.current_layer_path):

            if (x < 0.0):
                x = 0
            if (y < 0.0):
                y = 0

            pwidth = self.pimage.get_width()
            pheight = self.pimage.get_height()

            if (x > pwidth):
                x = pwidth
            if (y > pheight):
                y = pheight

            print(x, y)

            fill = (0, 0, 255)
            if(erase):
                fill = (255, 0, 0)

            self.draw_path(x, y, pheight, pwidth, fill)

            self.on_layer_mask_change(layer)

            self.mouse_down_coords_changed(widget, event)
            return True


    def draw_path(self, x, y, pheight, pwidth, fill):
        preview = self.current_layer_path.add_point(int(x), int(y), (pheight, pwidth, 3), fill)

        # Bits per pixel
        bpp = float(str(self.image.dtype).replace("uint", "").replace("float", ""))
        # Pixel value range
        np = float(2 ** bpp - 1)

        self.image[preview == 255] = np
        cv2.imwrite("/dev/shm/phf2-preview-%s-drag.png" % getpass.getuser(), self.image)
        temppbuf = GdkPixbuf.Pixbuf.new_from_file("/dev/shm/phf2-preview-%s-drag.png" % getpass.getuser())
        self.ui["preview"].set_from_pixbuf(temppbuf)


    def new_path(self, widget, event):
        draw = self.ui["mask_draw_toggle"].get_active()
        erase = self.ui["mask_erase_toggle"].get_active()
        layer = self.get_selected_layer()
        if((draw or erase) and layer.editable):
            print(self.pimage.get_width(), self.pimage.get_height())
            width = self.pimage.get_width()
            size = self.ui["mask_brush_size"].get_value()
            feather = self.ui["mask_brush_feather"].get_value()
            self.current_layer_path = layer.mask.get_new_path(size, feather, float(self.awidth)/float(width), draw)


    def mask_draw_toggled(self, widget):
        self.ui["mask_erase_toggle"].set_active(not widget.get_active())

    def mask_erase_toggled(self, widget):
        self.ui["mask_draw_toggle"].set_active(not widget.get_active())
        self.ui["mask_brush_feather_scale"].set_sensitive(not widget.get_active())


    def edit_mask_toggled(self, widget):
        self.ui["layer_mask_reveal"].set_reveal_child(widget.get_active())
        self.ui["mask_draw_toggle"].set_active(widget.get_active())
        self.ui["mask_erase_toggle"].set_active(False)
        self.ui["scroll_window"].queue_draw()
        if (widget.get_active()):
            thread = threading.Thread(target=self.process_mask, args=(True,))
            thread.start()
        elif(self.was_editing_mask):
            self.on_layer_change(self.get_selected_layer())

        self.was_editing_mask = widget.get_active()

    def update_layer_opacity(self, sender):
        layer = self.get_selected_layer()
        if(layer.opacity != sender.get_value()):
            layer.set_opacity(sender.get_value())


    def create_layer(self, layer_name, is_base, select = False, set_pre_undo_draw_state = False):
        layer = Layer.Layer(is_base, layer_name, self.on_layer_change)
        for tool in self.tools:
            tool_instance = tool()
            layer.add_tool(tool_instance)

        self.layers += [layer,]

        GLib.idle_add(self.create_layer_ui, layer, select, set_pre_undo_draw_state)

        return layer

    def create_layer_ui(self, layer, select, set_pre_undo_draw_state = False):
        layer_box = Gtk.HBox()
        layer_box.set_hexpand(False)
        layer_box.set_halign(Gtk.Align.START)

        layer_toggle = Gtk.CheckButton()
        layer_toggle.set_sensitive(layer.editable)
        layer_toggle.set_active(layer.enabled)
        layer_toggle.set_hexpand(False)
        layer_toggle.set_halign(Gtk.Align.START)
        layer_toggle.set_margin_right(8)
        layer_toggle.set_margin_left(8)
        layer_toggle.set_margin_top(4)
        layer_toggle.set_margin_bottom(4)
        layer_toggle.connect("toggled", self.toggle_layer, layer)

        layer_label = Gtk.Label()
        layer_label.set_label(layer.name)
        if(layer.name == "base"):
            layer_label.set_label("Base Layer")
        layer_label.set_hexpand(True)
        layer_label.set_halign(Gtk.Align.FILL)
        layer_label.set_margin_top(4)
        layer_label.set_margin_bottom(4)

        layer_box.add(layer_toggle)
        layer_box.add(layer_label)

        layer.show_all()
        layer_box.show_all()

        self.ui["layers_list"].add(layer_box)

        layer.selector_row = layer_box.get_parent()

        self.ui["tool_box_stack"].add(layer.tool_box)
        self.ui["tool_stack"].add(layer.tool_stack)

        if(select):
            self.select_layer(layer)

        if(set_pre_undo_draw_state) and self.get_selected_layer().editable:
            print(self.pre_undo_editing, self.pre_undo_erasing)
            self.ui["mask_erase_toggle"].set_active(self.pre_undo_erasing)
            self.ui["edit_layer_mask_button"].set_active(self.pre_undo_editing)


    def layer_ui_activated(self, widget, row):
        layer_index = row.get_index()
        self.ui["tool_stack"].set_visible_child(self.layers[layer_index].tool_stack)
        self.ui["tool_box_stack"].set_visible_child(self.layers[layer_index].tool_box)
        self.ui["remove_layer_button"].set_sensitive(self.layers[layer_index].editable)
        self.ui["edit_layer_mask_button"].set_sensitive(self.layers[layer_index].editable)
        self.ui["layer_opacity_scale"].set_sensitive(self.layers[layer_index].editable)
        self.ui["layer_blend_mode"].set_sensitive(self.layers[layer_index].editable)
        self.ui["layer_blend_mode"].set_active(["additive", "overlay"].index(self.layers[layer_index].blend_mode))
        self.ui["layer_opacity"].set_value(self.layers[layer_index].opacity)
        if(self.ui["edit_layer_mask_button"].get_active()):
            self.ui["edit_layer_mask_button"].set_active(self.layers[layer_index].editable)
            self.on_layer_change(self.last_selected_layer)
            self.last_selected_layer = self.get_selected_layer()

    def toggle_layer(self, sender, layer):
        layer.set_enabled(sender.get_active())


    def new_layer_button_clicked(self, widget):
        self.show_layers()
        # Allocate an un-used layer name
        layer_number = len(self.layers)
        layer_name = "Layer %i" % layer_number

        while(self.layer_exists(layer_name)):
            layer_number += 1
            layer_name = "Layer %i" % layer_number

        # Create the layer
        layer = self.create_layer(layer_name, False)
        layer.set_size(self.awidth, self.aheight)

        # Save changes
        threading.Thread(target=self.save_image_data).start()
        self.on_layer_change(layer)


    def remove_layer_button_clicked(self, widget):
        layer_row = self.ui["layers_list"].get_selected_row()

        selected_index = 1

        new_layers = []
        for layer in self.layers:
            if(layer.selector_row != layer_row):
                new_layers += [layer]
            else:
                selected_index = self.layers.index(layer)

        self.ui["layers_list"].remove(layer_row)
        self.layers = new_layers

        # Select next layer
        self.select_layer(self.layers[selected_index -1])

        if (len(self.layers) == 1):
            self.ui["layers_reveal"].set_reveal_child(False)

        if(widget != None):
            # Only do this if the layer was actualy deleted by the user
            # and not by the undo-redo system for example

            # Save changes
            threading.Thread(target=self.save_image_data).start()

            self.on_layer_change(self.get_selected_layer())


    def get_selected_layer(self):
        layer_row = self.ui["layers_list"].get_selected_row()

        for layer in self.layers:
            if (layer.selector_row == layer_row):
                return layer

    def layer_exists(self, layer_name):
        for layer in self.layers:
            if(layer.name == layer_name):
                return True
        return False

    def show_layers(self):
        self.ui["layers_reveal"].set_reveal_child(True)

    def select_layer(self, layer):
        self.ui["layers_list"].select_row(layer.selector_row)
        self.layer_ui_activated(self.ui["layers_list"], layer.selector_row)

    def delete_all_editable_layers(self):
        count = len(self.layers) -1
        while(len(self.layers) != 1):
            self.select_layer(self.layers[1])
            self.remove_layer_button_clicked(None)


    def draw_ui_brush_circle(self, widget, context):
        drawing = self.ui["edit_layer_mask_button"].get_active()
        if(drawing):
            size = self.ui["mask_brush_size"].get_value()
            if(self.mousedown):
                context.set_source_rgb(255, 0, 0)
            else:
                context.set_source_rgb(255, 255, 255)
            context.arc(self.mousex, self.mousey, size/2.0, 0.0, 2 * numpy.pi)
            context.stroke()

    def mouse_coords_changed(self, widget, event):
        self.mousedown = False
        self.mousex, self.mousey = event.x, event.y
        widget.queue_draw()

    def mouse_down_coords_changed(self, widget, event):
        self.mousedown = True
        self.mousex, self.mousey = widget.translate_coordinates(self.ui["scroll_window"], event.x, event.y)
        widget.queue_draw()

    def brush_size_changed(self, sender):
        self.ui["scroll_window"].queue_draw()

    def layer_blend_mode_changed(self, sender):
        layer = self.get_selected_layer()
        if(layer.blend_mode != sender.get_active_text().lower()):
            layer.set_blending_mode(sender.get_active_text().lower())
