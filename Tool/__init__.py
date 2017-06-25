from gi.repository import GLib, Gtk

class Tool:
    def __init__(self):
        self.id = ""
        self.name = ""
        self.properties = []
        self.icon_path = ""
        self.on_change_callback = None

        # Let the tool set values
        self.on_init()

        self.props = {}
        for property in self.properties:
            self.props[property.id] = property

        # Create widget for tool

        self.widget = Gtk.Grid()
        self.widget.set_column_spacing(8)
        self.widget.set_row_spacing(6)
        self.widget.set_halign(Gtk.Align.FILL)
        self.widget.set_hexpand(True)

        vpos = 0
        for property in self.properties:
            # Create Header
            if(property.type == "Header"):
                header = Gtk.HBox()
                header.set_margin_top(6)

                if(vpos != 0):
                    # Add a Separator
                    separator = Gtk.Separator()
                    separator.set_margin_top(6)
                    separator.show()
                    self.widget.attach(separator, 0, vpos, 3, 1)
                    vpos += 1

                title = Gtk.Label()
                title.set_halign(Gtk.Align.START)
                if(property.is_subheading):
                    title.set_markup("<i>%s</i>" % property.name)
                else:
                    title.set_markup("<b>%s</b>" % property.name)

                header.add(title)

                if(property.has_toggle):
                    toggle = Gtk.Switch()
                    toggle.set_halign(Gtk.Align.END)
                    header.add(toggle)
                    property.on_toggle_callback = self.on_toggled
                    property.set_widget(toggle)

                elif(property.has_button):
                    button = Gtk.Button()
                    button.set_halign(Gtk.Align.END)
                    button.set_label(property.button_label)
                    header.add(button)
                    property.set_widget(button)

                self.widget.attach(header, 0, vpos, 3, 1)

            # Create Combo
            elif(property.type == "Combo"):
                label = Gtk.Label()
                label.set_halign(Gtk.Align.END)
                label.set_justify(Gtk.Justification.RIGHT)
                label.set_text(property.name)
                self.widget.attach(label, 0, vpos, 1, 1)

                combo = Gtk.ComboBoxText()
                combo.set_hexpand(True)
                self.widget.attach(combo, 1, vpos, 1, 1)
                for option in property.options:
                    combo.append_text(option)

                property.set_widget(combo)


            # Create Spin
            elif (property.type == "Spin"):
                label = Gtk.Label()
                label.set_halign(Gtk.Align.END)
                label.set_justify(Gtk.Justification.RIGHT)
                label.set_text(property.name)
                self.widget.attach(label, 0, vpos, 1, 1)

                adjustment = Gtk.Adjustment()
                adjustment.set_lower(property.min)
                adjustment.set_upper(property.max)
                adjustment.set_step_increment((property.max - property.min) / 100)
                property.set_widget(adjustment)

                spin = Gtk.SpinButton()
                spin.set_adjustment(adjustment)
                spin.set_hexpand(True)
                spin.set_digits(3)
                property.ui_widget = spin

                self.widget.attach(spin, 1, vpos, 1, 1)

            # Create Toggle
            elif(property.type == "Toggle"):
                label = Gtk.Label()
                label.set_halign(Gtk.Align.END)
                label.set_justify(Gtk.Justification.RIGHT)
                label.set_text(property.name)
                self.widget.attach(label, 0, vpos, 1, 1)

                toggle = Gtk.ToggleButton()
                toggle.set_label("Enable")
                toggle.set_hexpand(True)
                self.widget.attach(toggle, 1, vpos, 1, 1)

                property.set_widget(toggle)

            # Create Slider
            elif (property.type == "Slider"):
                label = Gtk.Label()
                label.set_halign(Gtk.Align.END)
                label.set_justify(Gtk.Justification.RIGHT)
                label.set_text(property.name)
                self.widget.attach(label, 0, vpos, 1, 1)

                adjustment = Gtk.Adjustment()
                adjustment.set_lower(property.min)
                adjustment.set_upper(property.max)
                adjustment.set_step_increment((property.max - property.min)/100)
                property.set_widget(adjustment)

                slider = Gtk.Scale()
                slider.set_adjustment(adjustment)
                slider.set_hexpand(True)
                slider.set_value_pos(Gtk.PositionType.RIGHT)
                property.ui_widget = slider

                self.widget.attach(slider, 1, vpos, 1, 1)

            if(property.type != "Header"):
                # Create reset button
                icon = Gtk.Image()
                icon.set_from_icon_name("edit-clear-symbolic", Gtk.IconSize.BUTTON)
                reset_button = Gtk.Button()
                reset_button.set_image(icon)
                reset_button.connect("clicked", property.reset_value)
                property.reset_button = reset_button
                self.widget.attach(reset_button, 2, vpos, 1, 1)

            # Connect on change
            property.connect_on_change(self.on_change)
            vpos += 1

        for property in self.properties:
            if(property.type == "Header") and (property.has_toggle):
                self.on_toggled(property, property.widget.get_active())

        separator = Gtk.Separator()
        separator.set_margin_top(6)
        separator.show()
        self.widget.attach(separator, 0, vpos, 3, 1)

        self.widget.show_all()

        self.tool_button = Gtk.ToggleButton()
        self.tool_button.set_tooltip_text(self.name)
        icon = Gtk.Image()
        icon.set_from_file(self.icon_path)
        self.tool_button.set_image(icon)


    def on_toggled(self, sender, value):
        si = self.properties.index(sender)
        for property in self.properties[si+1:]:
            if(property.type == "Header") and (property.has_toggle):
                break
            else:
                property.set_enabled(value)

    def is_default(self):
        res = True
        for prop in self.properties:
            if(prop.get_value() != prop.default):
                res = False
                break

        return res

    def connect_on_change(self, callback):
        self.on_change_callback = callback

    def on_change(self, sender):
        if(self.on_change_callback != None):
            self.on_change_callback(self, sender)


    def on_init(self):
        raise NotImplementedError()

    def on_button_pressed(self):
        raise NotImplementedError()

    def on_update(self, image):
        raise NotImplementedError()

    def load_properties(self, dict):
        for key in dict:
            if(key in self.props):
                self.props[key].set_value(dict[key])

    def get_properties_as_dict(self):
        dict = {}
        for prop in self.properties:
            dict[prop.id] = prop.get_value()
        return dict

    def reset(self):
        for prop in self.properties:
            prop.reset_value()



class Property:
    def __init__(self, id, name, type, default, **kwargs):
        self.id = id
        self.name = name
        self.type = type
        self.on_change_callback = None
        # Types Include:
        #   Slider,
        #   Toggle,
        #   Spin,
        #   Combo,
        #   Header

        if(self.type == "Slider") or (self.type == "Spin"):
            # Slider and Spinner
            self.max = kwargs["max"]
            self.min = kwargs["min"]
            self.ui_widget = None

        if(self.type == "Combo"):
            self.options = kwargs["options"]

        if(self.type == "Header"):
            self.has_toggle = kwargs["has_toggle"]
            self.has_button = kwargs["has_button"]
            if(self.has_button):
                self.button_callback = kwargs["button_callback"]
                self.button_label = kwargs["button_label"]

            if("is_subheading" in kwargs):
                self.is_subheading = kwargs["is_subheading"]
            else:
                self.is_subheading = False

        self.value = default
        self.default = default

        self.widget = None
        self.reset_button = None
        self.on_toggle_callback = None

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value
        if(self.type == "Header") and (self.has_toggle):
            self.widget.set_active(value)

        if(self.type == "Slider") or (self.type == "Spin"):
            self.widget.set_value(value)

        if(self.type == "Toggle") or (self.type == "Combo"):
            self.widget.set_active(value)

        self.on_change()

    def reset_value(self, sender=None):
        self.set_value(self.default)
        return self.default

    def update_value(self, sender, arg=None):
        if(self.type == "Header") and (self.has_toggle):
            self.set_value(arg)
            if(self.on_toggle_callback != None):
                self.on_toggle_callback(self, arg)

        if(self.type == "Header") and (self.has_button):
            self.button_callback()

        if(self.type == "Slider") or (self.type == "Spin"):
            self.set_value(sender.get_value())

        if(self.type == "Toggle") or (self.type == "Combo"):
            self.set_value(sender.get_active())

    def set_widget(self, object):
        self.widget = object
        self.reset_value()

        if(self.type == "Header") and (self.has_toggle):
            object.connect("state-set", self.update_value)

        if(self.type == "Header") and (self.has_button):
            object.connect("clicked", self.update_value)

        if(self.type == "Slider") or (self.type == "Spin"):
            object.connect("value-changed", self.update_value)

        if(self.type == "Toggle"):
            object.connect("toggled", self.update_value)

        if(self.type == "Combo"):
            object.connect("changed", self.update_value)

    def set_enabled(self, enabled):
        if(self.type == "Slider") or (self.type == "Spin"):
            self.ui_widget.set_sensitive(enabled)
        elif(self.widget != None):
            self.widget.set_sensitive(enabled)

        if(self.reset_button != None):
            self.reset_button.set_sensitive(enabled)

    def connect_on_change(self, callback):
        self.on_change_callback = callback

    def on_change(self):
        if(self.on_change_callback != None):
            self.on_change_callback(self)


