from gi.repository import Gtk

class Method:
    def run(self, files, output, full_width, full_height):
        raise NotImplementedError()

    def stack(self, files):
        raise NotImplementedError()

    def __init__(self):
        self.id = ""
        self.name = ""
        self.properties = []

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
                slider.set_digits(2)
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

            vpos += 1


        separator = Gtk.Separator()
        separator.set_margin_top(6)
        separator.show()
        self.widget.attach(separator, 0, vpos, 3, 1)

        self.widget.show_all()

    def on_init(self):
        raise NotImplementedError()
