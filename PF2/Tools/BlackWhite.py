import cv2
import numpy

import Tool

class BlackWhite(Tool.Tool):
    def on_init(self):
        self.id = "black_white"
        self.name = "Black and White"
        self.icon_path = "ui/PF2_Icons/BlackWhite.png"
        self.properties = [
            Tool.Property("enabled", "Black and White", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("method", "Method", "Combo", 0, options=[
                "Average",
                "Weighted Average",
                "Luma",
                "Custom Weight"
            ]),
            Tool.Property("customHeader", "Custom Weight", "Header", None, has_toggle=False, has_button=False, is_subheading=True),
            Tool.Property("red", "Red Value", "Spin", 0.333, max=1, min=0),
            Tool.Property("green", "Green Value", "Spin", 0.333, max=1, min=0),
            Tool.Property("blue", "Blue Value", "Spin", 0.333, max=1, min=0),
        ]

    def on_update(self, image):
        if(self.props["enabled"].get_value()):
            mode = self.props["method"].get_value()

            bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
            np = float(2 ** bpp - 1)
            out = image.astype(numpy.float32)

            if(mode == 0):
                bc = out[0:, 0:, 0]
                gc = out[0:, 0:, 1]
                rc = out[0:, 0:, 2]

                out = (bc + gc + rc) / 3

            elif(mode == 1):
                bc = out[0:, 0:, 0]
                gc = out[0:, 0:, 1]
                rc = out[0:, 0:, 2]

                out = 0.114 * bc + 0.587 * gc + 0.299 * rc

            elif(mode == 2):
                hsl = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
                out = hsl[0:, 0:, 2]

            elif(mode == 3):
                r = self.props["red"].get_value()
                g = self.props["green"].get_value()
                b = self.props["blue"].get_value()

                bc = out[0:, 0:, 0]
                gc = out[0:, 0:, 1]
                rc = out[0:, 0:, 2]

                out = b * bc + g * gc + r * rc

            out[out < 0.0] = 0.0
            out[out > np] = np

            out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)

            return out.astype(image.dtype)
        else:
            return image.image

