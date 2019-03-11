import cv2
import numpy
from PF2.Scalar import Scalar
from PF2.Utilities import HMS
from PF2.Utilities import clip

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

            np = image.np
            out = image.image
            channels = cv2.split(out)

            if(mode == 0):
                out = self._weighted(channels)

            elif(mode == 1):
                out = self._weighted(channels, 0.114, 0.587, 0.299)

            elif(mode == 2):
                hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
                hsv_chans = cv2.split(hsv)
                out = hsv_chans[2]

            elif(mode == 3):
                r = self.props["red"].get_value()
                g = self.props["green"].get_value()
                b = self.props["blue"].get_value()

                out = self._weighted(channels, b, g, r)

            out = clip(out, np, 0, np)

            return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)

        else:
            return image.image

    def _weighted(self, channels, b=0.333, g=0.333, r=0.333):
        blue = cv2.multiply(channels[0], Scalar(b))
        green = cv2.multiply(channels[1], Scalar(g))
        red = cv2.multiply(channels[2], Scalar(r))

        out = cv2.add(blue, green)
        out = cv2.add(out, red)
        return out