from gi.repository import Gtk, GLib

class Layer:
    def __init__(self, base, name, on_change):
        print("init", name)
        self.mask = []
        self.tools = []
        self.tool_map = {}
        self.name = name
        self.enabled = True
        self.selected_tool = 0
        self.editable = not base

        self.selector_row = None

        self.tool_box = Gtk.FlowBox()
        self.tool_box.set_orientation(1)

        self.tool_stack = Gtk.Stack()
        self.tool_stack.set_transition_type(6)
        self.tool_stack.set_homogeneous(False)


        self.layer_changed = on_change


    def add_tool(self, tool):
        print("add tool", tool)
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
        layerDict["mask"] = self.mask
        layerDict["enabled"] = self.enabled

        return layerDict

    def set_from_layer_dict(self, dict):
        print("set_from_layer_dict", dict)
        # Load Tool Data
        for tool in self.tools:
            if(tool.id in dict["tools"]):
                GLib.idle_add(tool.load_properties, dict["tools"][tool.id])

        # The base layer only has tools.
        if(self.editable):
            # Load Mask Vectors
            self.mask = dict["mask"]

            # Load Layer Name
            self.name = dict["name"]

            # Load Enabled State
            self.enabled = dict["enabled"]


    def render_layer(self, baseImage, image, callback=None):
        # We are passed a base image (original)
        # Make a copy of this to pass through the tools
        layer = baseImage.copy()

        # Base layer needs no mask processing
        if(not self.editable):
            ntools = len(self.tools)
            count = 1
            for tool in self.tools:
                if (callback != None):
                    # For showing progress
                    callback(tool.name, ntools, count - 1)

                # Call the tool's image processing function
                layer = tool.on_update(layer)
                count += 1

            image = layer

        ## Here we would blend with the mask

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

