import cv2
import numpy

import Tool

class HueEqualiser(Tool.Tool):
    def on_init(self):
        self.id = "hueequaliser"
        self.name = "Hue Equaliser"
        self.icon_path = "ui/PF2_Icons/HueEqualiser.png"
        self.properties = [
            Tool.Property("header", "Hue Equaliser", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("bleed", "Hue Bleed", "Slider", 0.5, max=2.0, min=0.01),
            Tool.Property("neighbour_bleed", "Neighbour Bleed", "Slider", 0.25, max=2.0, min=0.0),
            # Red
            Tool.Property("header_red", "Red", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("red_value", "Value", "Slider", 0, max=50, min=-50),
            Tool.Property("red_saturation", "Saturation", "Slider", 0, max=50, min=-50),
            # Yellow
            Tool.Property("header_yellow", "Yellow", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("yellow_value", "Value", "Slider", 0, max=50, min=-50),
            Tool.Property("yellow_saturation", "Saturation", "Slider", 0, max=50, min=-50),
            # Green
            Tool.Property("header_green", "Green", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("green_value", "Value", "Slider", 0, max=50, min=-50),
            Tool.Property("green_saturation", "Saturation", "Slider", 0, max=50, min=-50),
            # Cyan
            Tool.Property("header_cyan", "Cyan", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("cyan_value", "Value", "Slider", 0, max=50, min=-50),
            Tool.Property("cyan_saturation", "Saturation", "Slider", 0, max=50, min=-50),
            # Blue
            Tool.Property("header_blue", "Blue", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("blue_value", "Value", "Slider", 0, max=50, min=-50),
            Tool.Property("blue_saturation", "Saturation", "Slider", 0, max=50, min=-50),
            # Violet
            Tool.Property("header_violet", "Violet", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("violet_value", "Value", "Slider", 0, max=50, min=-50),
            Tool.Property("violet_saturation", "Saturation", "Slider", 0, max=50, min=-50),
        ]

    def on_update(self, image):
        hues = {
            "red": 0,
            "yellow": 60,
            "green": 120,
            "cyan": 180,
            "blue": 240,
            "violet": 300,
            "_red": 360,
        }


        if(not self.is_default()):
            # TODO update this tool to be GPU enabled
            out = image.get()

            bleed = self.props["bleed"].get_value()
            neighbour_bleed = self.props["neighbour_bleed"].get_value()

            out = out.astype(numpy.float32)

            # Convert to HSV colorspace
            out = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)

            # Bits per pixel
            bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
            # Pixel value range
            np = float(2 ** bpp - 1)

            imhue = out[0:, 0:, 0]
            imsat = out[0:, 0:, 1]
            imval = out[0:, 0:, 2]

            for hue in hues:
                hsat = self.props["%s_saturation" % hue.replace('_', '')].get_value()
                hval = self.props["%s_value" % hue.replace('_', '')].get_value()

                isHue = self._is_hue(imhue, hues[hue], (3.5/bleed))

                isHue = self._neighbour_bleed(isHue, neighbour_bleed)

                imsat = imsat + ((hsat / 10000) * 255) * isHue
                imval = imval + ((hval / 1000) * np) * isHue

                # Clip any values out of bounds
                imval[imval < 0.0] = 0.0
                imval[imval > np] = np

                imsat[imsat < 0.0] = 0.0
                imsat[imsat > 1.0] = 1.0




            out[0:, 0:, 1] = imsat
            out[0:, 0:, 2] = imval


            # Convert back to BGR colorspace
            out = cv2.cvtColor(out, cv2.COLOR_HSV2BGR)

            out = out.astype(image.dtype)

            image.set(out)

        return image.image


    def _is_hue(self, image, hue_value, bleed_value = 3.5):
        mif = hue_value - 30
        mir = hue_value + 30
        if (mir > 360):
            mir = 360
        if (mif < 0):
            mif = 0

        bleed = float(360 / bleed_value)
        icopy = image.copy()

        print(bleed, mif, mir)

        if(mif != 0):
            icopy[icopy < mif - bleed] = 0.0
            icopy[icopy > mir + bleed] = 0.0

            icopy[(icopy < mif) * (icopy != 0.0)] = (((mif - (icopy[(icopy < mif) * (icopy != 0.0)]))/360.0) / (bleed/360.0)) * -1 + 1

            icopy[(icopy > mir) * (icopy != 0.0)] = ((((icopy[(icopy > mir) * (icopy != 0.0)]) - mir)/360.0) / (bleed/360.0)) * -1 + 1

        icopy[(icopy >= mif) * (icopy <= mir)] = 1.0

        if(mif == 0):
            icopy[icopy > mir + bleed] = 0.0

            icopy[(icopy > mir) * (icopy != 0.0)] = ((((icopy[(icopy > mir) * (icopy != 0.0)]) - mir) / 360.0) / (bleed/360.0)) * -1 + 1

        return icopy

    def _neighbour_bleed(self, map, bleed):
        strength = bleed*30

        if (strength > 0):
            height, width = map.shape[:2]
            size = (height * width)
            mul = numpy.math.sqrt(size) / 1064.416  # numpy.math.sqrt(1132982.0)

            map = map*255

            blur_size = abs(2 * round((round(strength * mul) + 1) / 2) - 1)
            im = cv2.blur(map, (int(blur_size), int(blur_size)))
            return im/255.0

        return map