import cv2

import Tool
from scipy import ndimage

class Denoise(Tool.Tool):
    def on_init(self):
        self.id = "denoise"
        self.name = "Denoise"
        self.icon_path = "ui/PF2_Icons/Denoise.png"
        self.properties = [
            # Detailer
            Tool.Property("enabled", "Denoise", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("strength", "Strength", "Slider", 0, max=100, min=0),
            Tool.Property("w_strength", "White Strength", "Slider", 20, max=100, min=0),
            Tool.Property("b_strength", "Black Strength", "Slider", 70, max=100, min=0),
            Tool.Property("method", "Method", "Combo", 0, options=[
                "Mean",
                "Gaussian",
            ]),
        ]

    def on_update(self, image):
        im = image
        if(self.props["enabled"].get_value()):
            bpp = int(str(im.dtype).replace("uint", "").replace("float", ""))
            np = float(2 ** bpp - 1)

            method = self.props["method"].get_value()
            strength = self.props["strength"].get_value()
            b_strength = self.props["b_strength"].get_value()
            w_strength = self.props["w_strength"].get_value()

            filtered = None
            if(method == 0):
                filtered = ndimage.median_filter(im, 3)
            elif(method == 1):
                filtered = ndimage.gaussian_filter(im, 2)

            w_filter = im
            w_filter[im > (float(np) / 10) * 9] = filtered[im > (float(np) / 10) * 9]

            b_filter = im
            b_filter[im < (float(np) / 10)] = filtered[im < (float(np) / 10)]

            # Blend
            im = cv2.addWeighted(filtered, (strength / 100), im, 1 - (strength / 100), 0)
            im = cv2.addWeighted(w_filter, (w_strength / 100), im, 1 - (w_strength / 100), 0)
            im = cv2.addWeighted(b_filter, (b_strength / 100), im, 1 - (b_strength / 100), 0)

        return im
