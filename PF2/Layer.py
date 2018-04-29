from gi.repository import Gtk, GLib
import PF2.VectorMask as VectorMask
import cv2, numpy
from PF2.Image import Image

class Layer:
    def __init__(self, base, name, on_change):
        self.mask = VectorMask.VectorMask()
        self.tools = []
        self.tool_map = {}
        self.name = name
        self.enabled = True
        self.selected_tool = 0
        self.editable = not base
        self.opacity = 1.0
        self.blend_mode = "additive"
        if(not self.editable):
            self.blend_mode = "overlay"

        self.selector_row = None

        self.tool_box = Gtk.FlowBox()
        self.tool_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.tool_box.set_orientation(1)

        self.tool_stack = Gtk.Stack()
        self.tool_stack.set_transition_type(6)
        self.tool_stack.set_homogeneous(False)

        self.layer_copy = None


        self.layer_changed = on_change


    def add_tool(self, tool):
        self.tool_box.add(tool.tool_button)
        self.tool_stack.add(tool.widget)
        self.tool_map[tool.tool_button] = tool

        tool.tool_button.connect("clicked", self.on_tool_button_clicked)
        tool.connect_on_change(self.on_tool_change)

        self.tools += [tool,]

        if(len(self.tools) == 1):
            tool.tool_button.set_active(True)


    def on_tool_change(self, tool, prop):
        self.layer_changed(self)


    def on_tool_button_clicked(self, sender):
        if(sender.get_active()):
            self.tool_stack.set_visible_child(self.tool_map[sender].widget)
            for key in self.tool_map:
                if(key != sender):
                    key.set_active(False)

        elif(self.tool_stack.get_visible_child() == self.tool_map[sender].widget):
            sender.set_active(True)

    def get_layer_dict(self):
        layerDict = {}

        # Get tool values
        toolDict = {}
        for tool in self.tools:
            toolDict[tool.id] = tool.get_properties_as_dict()

        layerDict["tools"] = toolDict
        layerDict["name"] = self.name
        layerDict["mask"] = self.mask.get_vector_mask_dict()
        layerDict["enabled"] = self.enabled
        layerDict["opacity"] = self.opacity
        layerDict["blend-mode"] = self.blend_mode

        return layerDict

    def set_from_layer_dict(self, dict):
        # Load Tool Data
        for tool in self.tools:
            if(tool.id in dict["tools"]):
                GLib.idle_add(tool.load_properties, dict["tools"][tool.id])

        # The base layer only has tools.
        if(self.editable):
            # Load Mask Vectors
            self.mask.set_from_vector_mask_dict(dict["mask"])

            # Load Layer Name
            self.name = dict["name"]

            # Load Enabled State
            self.enabled = dict["enabled"]

            # Load Opacity Fraction
            self.opacity = dict["opacity"]

            # Load Blend Mode
            self.blend_mode = dict["blend-mode"]


    def render_layer(self, baseImage, image, callback=None):
        # Only process if the layer is enabled
        if(self.enabled and self.opacity != 0.0):
            layer = None

            if(self.blend_mode == "overlay"):
                # We are passed a base image (original)
                # Make a copy of this to pass through the tools
                layer = baseImage.copy()
            else: # if(self.blend_mode == "additive"):
                # Layer is additive, make copy of current working image
                layer = image.copy()

            layerImage = Image(layer)

            # Process the Layer
            ntools = len(self.tools)
            count = 1
            for tool in self.tools:
                if (callback != None):
                    # For showing progress
                    callback(tool.name, ntools, count - 1)

                # Call the tool's image processing function
                layerImage.image = tool.on_update(layerImage)
                assert type(layerImage.image) == cv2.UMat or type(layerImage.image) == numpy.ndarray
                count += 1

            layer = layerImage.get()

            # Base layer needs no mask processing
            if(not self.editable):
                image = layer

            # Here we would blend with the mask
            else:
                mask_map = self.mask.get_mask_map()
                if(type(mask_map) == numpy.ndarray):
                    # Only process if there is actually an existing mask
                    height, width = layer.shape[:2]

                    mask_map = cv2.resize(mask_map, (width, height), interpolation=cv2.INTER_AREA)
                    mask_map = mask_map * self.opacity

                    inverted_map = (mask_map * -1) + 1
                    for i in range(0,3):
                        image[0:, 0:, i] = (layer[0:, 0:, i] * mask_map) + (image[0:, 0:, i] * inverted_map)

        self.layer_copy = image.copy()

        return image

    def get_layer_mask_preview(self, image):
        mask =  self.mask.get_mask_map()

        if(type(mask) == numpy.ndarray):
            w, h = image.shape[:2]

            # Bits per pixel
            bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
            # Pixel value range
            np = float(2 ** bpp - 1)

            mask = cv2.resize(mask, (h, w), interpolation=cv2.INTER_AREA)
            inverted_map = (mask * -1) + 1
            image[0:, 0:, 2] = (np * mask) + (image[0:, 0:, 2] * inverted_map)

        return image







    def show_all(self):

        self.tool_box.show_all()
        self.tool_stack.show_all()

        for tool in self.tools:
            tool.widget.show_all()
            tool.tool_button.show_all()


    def reset_tools(self):
        for tool in self.tools:
            tool.reset()


    def set_size(self, width, height):
        self.mask.set_dimentions(width, height)

    def set_opacity(self, opacity):
        self.opacity = opacity
        self.on_tool_change(None, None)

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.on_tool_change(None, None)

    def set_blending_mode(self, mode):
        self.blend_mode = mode
        self.on_tool_change(None, None)
