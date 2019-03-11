import cv2
import numpy

from PF2.Scalar import Scalar
from PF2.Utilities import HMS
from PF2.Utilities import clip

import Tool

class Colours(Tool.Tool):
    def on_init(self):
        self.id = "colours"
        self.name = "Colours"
        self.icon_path = "ui/PF2_Icons/Colours.png"
        self.properties = [
            Tool.Property("header", "Colours", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("overall_saturation", "Saturation", "Slider", 0, max=50, min=-50),
            Tool.Property("hue", "Hue", "Slider", 0, max=50, min=-50),
            Tool.Property("kelvin", "Colour Temperature", "Slider", 6500, max=15000, min=1000),
            Tool.Property("header_ts", "Tonal Saturation", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("highlight_saturation", "Highlight Saturation", "Slider", 0, max=50, min=-50),
            Tool.Property("midtone_saturation", "Midtone Saturation", "Slider", 0, max=50, min=-50),
            Tool.Property("shadow_saturation", "Shadow Saturation", "Slider", 0, max=50, min=-50),
            # Red
            Tool.Property("header_red", "Red", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("red_overall_brightness", "Overall Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("red_highlight_brightness", "Highlight Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("red_midtone_brightness", "Midtone Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("red_shadow_brightness", "Shadow Brightness", "Slider", 0, max=50, min=-50),
            # Green
            Tool.Property("header_green", "Green", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("green_overall_brightness", "Overall Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("green_highlight_brightness", "Highlight Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("green_midtone_brightness", "Midtone Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("green_shadow_brightness", "Shadow Brightness", "Slider", 0, max=50, min=-50),
            # Blue
            Tool.Property("header_blue", "Blue", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("blue_overall_brightness", "Overall Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("blue_highlight_brightness", "Highlight Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("blue_midtone_brightness", "Midtone Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("blue_shadow_brightness", "Shadow Brightness", "Slider", 0, max=50, min=-50),
            # Bleed
            Tool.Property("header_bleed", "Tonal Bleed", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("highlight_bleed", "Highlight Bleed", "Slider", 0.5, max=1, min=0.001),
            Tool.Property("midtone_bleed", "Midtone Bleed", "Slider", 0.5, max=1, min=0.001),
            Tool.Property("shadow_bleed", "Shadow Bleed", "Slider", 0.5, max=1, min=0.001),
        ]

    def on_update(self, image):
        if(not self.is_default()):
            im = image.image
            hue = self.props["hue"].get_value()
            saturation = self.props["overall_saturation"].get_value()
            ct = self.props["kelvin"].get_value()/100.0
            hs = self.props["highlight_saturation"].get_value()
            ms = self.props["midtone_saturation"].get_value()
            ss = self.props["shadow_saturation"].get_value()
            rob = self.props["red_overall_brightness"].get_value()
            rhb = self.props["red_highlight_brightness"].get_value()
            rmb = self.props["red_midtone_brightness"].get_value()
            rsb = self.props["red_shadow_brightness"].get_value()
            gob = self.props["green_overall_brightness"].get_value()
            ghb = self.props["green_highlight_brightness"].get_value()
            gmb = self.props["green_midtone_brightness"].get_value()
            gsb = self.props["green_shadow_brightness"].get_value()
            bob = self.props["blue_overall_brightness"].get_value()
            bhb = self.props["blue_highlight_brightness"].get_value()
            bmb = self.props["blue_midtone_brightness"].get_value()
            bsb = self.props["blue_shadow_brightness"].get_value()
            chbl = self.props["highlight_bleed"].get_value()
            cmbl = self.props["midtone_bleed"].get_value()
            csbl = self.props["shadow_bleed"].get_value()

            np = image.np

            out = im

            bleeds = ((3.00 / chbl), (3.00 / cmbl), (3.00 / csbl))

            # Colour Temperature
            if(int(ct) != 65):
                r = 0
                if(ct <= 66):
                    print(ct <= 66)
                    r = 255
                else:
                    r = ct - 60
                    r = 329.698727446 * numpy.math.pow(r, -0.1332047592)
                    if(r < 0):
                        r = 0
                    if(r > 255):
                        r = 255

                g = 0
                if(ct <= 66):
                    g = ct
                    g = 99.4708025861 * numpy.math.log(g) - 161.1195681661
                    if (g < 0):
                        g = 0
                    if (g > 255):
                        g = 255
                else:
                    g = ct - 60
                    g = 288.1221695283 * numpy.math.pow(g, -0.0755148492)
                    if (g < 0):
                        g = 0
                    if (g > 255):
                        g = 255


                b = 0
                if(ct >= 66):
                    b = 255
                elif(ct <= 19):
                    b = 0
                else:
                    b = ct - 10
                    b = 138.5177312231 * numpy.math.log(b) - 305.0447927307
                    if (b < 0):
                        b = 0
                    if (b > 255):
                        b = 255

                r = (r/255.0)
                g = (g / 255.0)
                b = (b / 255.0)

                chans = cv2.split(im)

                # Red
                chans[2] = cv2.multiply(chans[2], Scalar(r))
                # Green
                chans[1] = cv2.multiply(chans[1], Scalar(g))
                # Blue
                chans[0] = cv2.multiply(chans[0], Scalar(b))

                out = cv2.merge(chans)



            #Converting to HSV

            out = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
            channels = cv2.split(out)

            #Hue...
            channels[0] = cv2.add(channels[0], Scalar((hue / 100.0) * np))

            #Saturation...
            channels[1] = self._process_colour_channel(channels[1], channels[2], saturation / 100.0, hs / 100.0, ms / 100.0, ss / 100.0, np, bleeds)

            out = cv2.merge(channels)
            out = clip(out, 4294967296.0, 0.0, 4294967296.0)
            out = cv2.cvtColor(out, cv2.COLOR_HSV2BGR)

            channels = cv2.split(out)

            #Red...
            channels[2] = self._process_colour_channel(channels[2], channels[2], rob, rhb, rmb, rsb, np, bleeds)

            #Green...
            channels[1] = self._process_colour_channel(channels[1], channels[1], gob, ghb, gmb, gsb, np, bleeds)

            #Blue...
            channels[0] = self._process_colour_channel(channels[0], channels[0], bob, bhb, bmb, bsb, np, bleeds)

            out = cv2.merge(channels)

            return clip(out, np, 0, np)
        else:
            return image.image


    def _process_colour_channel(self, image, value_image, value, highlight, midtone, shadow, np, bleeds):
        # Overall Brightness
        if(value != 0.0):
            image = cv2.add(image, Scalar((value / 100.0) * np))

        # Highlights
        if(highlight != 0.0):
            isHr = HMS.is_highlight(value_image, bleeds[0], np)
            calc = cv2.multiply(isHr, Scalar(np))
            calc = cv2.multiply(calc, Scalar(highlight/100.0))
            image = cv2.add(image, calc)

        # Midtones
        if(midtone != 0.0):
            isMr = HMS.is_midtone(value_image, bleeds[0], np)
            calc = cv2.multiply(isMr, Scalar(np))
            calc = cv2.multiply(calc, Scalar(midtone/100.0))
            image = cv2.add(image, calc)

        # Shadows
        if(shadow != 0.0):
            isSr = HMS.is_shadow(value_image, bleeds[0], np)
            calc = cv2.multiply(isSr, Scalar(np))
            calc = cv2.multiply(calc, Scalar(shadow/100.0))
            image = cv2.add(image, calc)

        return image