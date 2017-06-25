import cv2
import numpy

import Tool

class WhiteBalance(Tool.Tool):
    def on_init(self):
        self.id = "whitebalance"
        self.name = "Colour Temperature"
        self.icon_path = "ui/PF2_Icons/WhiteBalance.png"
        self.properties = [
            Tool.Property("enabled", "Colour Temperature", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("kelvin", "Kelvins", "Slider", 6500, max=15000, min=1000),
            Tool.Property("strength", "Strength", "Slider", 25, max=100, min=0),
        ]

    def on_update(self, image):
        if(self.props["enabled"].get_value()):
            ct = self.props["kelvin"].get_value()/100.0
            st = self.props["strength"].get_value()

            bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
            np = float(2 ** bpp - 1)

            r = 0
            print(ct)
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

            print(r, g, b)

            # Red
            # image[0:, 0:, 2] = (image[0:, 0:, 2] * (((st / 100.0)*-1)+1)) + ((st / 100.0) * (r - np/2.0))
            image[0:, 0:, 2] = image[0:, 0:, 2] * r
            # # Green
            # image[0:, 0:, 1] = (image[0:, 0:, 1] * (((st / 100.0)*-1)+1)) + ((st / 100.0) * (g - np/2.0))
            image[0:, 0:, 1] = image[0:, 0:, 1] * g
            # # Blue
            # image[0:, 0:, 0] = (image[0:, 0:, 0] * (((st / 100.0)*-1)+1)) + ((st / 100.0) * (b - np/2.0))
            image[0:, 0:, 0] = image[0:, 0:, 0] * b

            image[image < 0.0] = 0.0
            image[image > np] = np

        return image

