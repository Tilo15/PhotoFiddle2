import cv2
import numpy

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
            im = image
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

            bpp = float(str(im.dtype).replace("uint", "").replace("float", ""))
            np = float(2 ** bpp - 1)

            out = im.astype(numpy.float32)
            isHr = self._is_highlight(out, (3.00 / chbl))
            isMr = self._is_midtone(out, (3.00 / cmbl))
            isSr = self._is_shadow(out, (3.00 / csbl))

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

                # Red
                out[0:, 0:, 2] = out[0:, 0:, 2] * r
                # Green
                out[0:, 0:, 1] = out[0:, 0:, 1] * g
                # Blue
                out[0:, 0:, 0] = out[0:, 0:, 0] * b



            #Converting to HSV

            out = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)

            #Hue...
            if (hue != 0.0):
                out[0:, 0:, 0] = out[0:, 0:, 0] + (hue / 100.0) * 255

            #Saturation...
            if (saturation != 0.0):
                out[0:, 0:, 1] = out[0:, 0:, 1] + (saturation / 10000.0) * 255

            #Saturation Highlights...
            if (hs != 0.0):
                out[0:, 0:, 1] = (out[0:, 0:, 1] + ((hs * isHr[0:, 0:, 1]) / 10000.0) * 255)

            #Saturation Midtones...
            if (ms != 0.0):
                out[0:, 0:, 1] = (out[0:, 0:, 1] + ((ms * isMr[0:, 0:, 1]) / 10000.0) * 255)

            #Saturation Shadows...
            if (ss != 0.0):
                out[0:, 0:, 1] = (out[0:, 0:, 1] + ((ss * isSr[0:, 0:, 1]) / 10000.0) * 255)

            out[out < 0.0] = 0.0
            out[out > 4294967296.0] = 4294967296.0

            out = cv2.cvtColor(out, cv2.COLOR_HSV2BGR)

            #Red...
            if (rob != 0.0):
                out[0:, 0:, 2] = out[0:, 0:, 2] + (rob / 100.0) * np

            # Highlights
            if (rhb != 0.0):
                out[0:, 0:, 2] = (out[0:, 0:, 2] + ((rhb * isHr[0:, 0:, 1]) / 100.0) * np)

            # Midtones
            if (rmb != 0.0):
                out[0:, 0:, 2] = (out[0:, 0:, 2] + ((rmb * isMr[0:, 0:, 1]) / 100.0) * np)

            # Shadows
            if (rsb != 0.0):
                out[0:, 0:, 2] = (out[0:, 0:, 2] + ((rsb * isSr[0:, 0:, 1]) / 100.0) * np)

            #Green...
            if (gob != 0.0):
                out[0:, 0:, 1] = out[0:, 0:, 1] + (gob / 100.0) * np

            # Highlights
            if (ghb != 0.0):
                out[0:, 0:, 1] = (out[0:, 0:, 1] + ((ghb * isHr[0:, 0:, 1]) / 100.0) * np)

            # Midtones
            if (gmb != 0.0):
                out[0:, 0:, 1] = (out[0:, 0:, 1] + ((gmb * isMr[0:, 0:, 1]) / 100.0) * np)

            # Shadows
            if (gsb != 0.0):
                out[0:, 0:, 1] = (out[0:, 0:, 1] + ((gsb * isSr[0:, 0:, 1]) / 100.0) * np)

            #Blue...
            if (bob != 0.0):
                out[0:, 0:, 0] = out[0:, 0:, 0] + (bob / 100.0) * np

            # Highlights
            if (bhb != 0.0):
                out[0:, 0:, 0] = (out[0:, 0:, 0] + ((bhb * isHr[0:, 0:, 1]) / 100.0) * np)

            # Midtones
            if (bmb != 0.0):
                out[0:, 0:, 0] = (out[0:, 0:, 0] + ((bmb * isMr[0:, 0:, 1]) / 100.0) * np)

            # Shadows
            if (bsb != 0.0):
                out[0:, 0:, 0] = (out[0:, 0:, 0] + ((bsb * isSr[0:, 0:, 1]) / 100.0) * np)


            out[out < 0.0] = 0.0
            out[out > np] = np
            return out.astype(im.dtype)
        else:
            return image.image

    def _is_highlight(self, image, bleed_value = 6.0):
        bleed = float(image.max() / bleed_value)
        mif = image.max() / 3.0 * 2.0
        icopy = image.copy()

        icopy[icopy < mif - bleed] = 0.0
        icopy[(icopy < mif) * (icopy != 0.0)] = ((mif - (icopy[(icopy < mif) * (icopy != 0.0)])) / bleed) * -1 + 1
        icopy[icopy >= mif] = 1.0
        return icopy

    def _is_midtone(self, image, bleed_value = 6.0):
        bleed = float(image.max() / bleed_value)
        mif = image.max() / 3.0
        mir = image.max() / 3.0 * 2.0
        icopy = image.copy()

        icopy[icopy < mif - bleed] = 0.0
        icopy[icopy > mir + bleed] = 0.0

        icopy[(icopy < mif) * (icopy != 0.0)] = ((mif - (icopy[(icopy < mif) * (icopy != 0.0)])) / bleed) * -1 + 1
        icopy[(icopy > mir) * (icopy != 0.0)] = (((icopy[(icopy > mir) * (icopy != 0.0)]) - mir) / bleed) * -1 + 1
        icopy[(icopy >= mif) * (icopy <= mir)] = 1.0
        return icopy

    def _is_shadow(self, image, bleed_value=6.0):
        bleed = float(image.max() / bleed_value)
        mir = image.max() / 3.0
        icopy = image.copy()

        icopy[icopy <= mir] = 1.0
        icopy[icopy > mir + bleed] = 0.0
        icopy[icopy > mir] = (((icopy[(icopy > mir) * (icopy != 0.0)]) - mir) / bleed) * -1 + 1
        return icopy
