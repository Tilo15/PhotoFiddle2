import cv2
import numpy

import Tool
from PF2.Tools import Contrast


class Blur(Tool.Tool):
    def on_init(self):
        self.id = "blur"
        self.name = "Blur"
        self.icon_path = "ui/PF2_Icons/Blur.png"
        self.properties = [
            # Detailer
            Tool.Property("enabled", "Blur", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("method", "Method", "Combo", 1, options=[
                "Guassian",
                "Average",
                # "Median"
            ]),
            Tool.Property("strength", "Strength", "Slider", 5, max=100, min=0),

        ]

    def on_update(self, image):
        im = image.image
        if(self.props["enabled"].get_value()):
            strength = self.props["strength"].get_value()
            method = self.props["method"].get_value()

            size = (image.height*image.width)
            mul = numpy.math.sqrt(size) / 1064.416 #numpy.math.sqrt(1132982.0)

            if (strength > 0):
                blur_size = abs(2 * round((round(strength*mul) + 1) / 2) - 1)
                if(method == 0):
                    im = cv2.GaussianBlur(im, (int(blur_size), int(blur_size)), 0)

                elif(method == 1):
                    im = cv2.blur(im, (int(blur_size), int(blur_size)))

                # elif(method == 2):
                #     im = cv2.medianBlur(im, int(blur_size))
        return im



