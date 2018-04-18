import cv2
import numpy

import Tool


class Tonemap(Tool.Tool):
    def on_init(self):
        self.id = "tonemap"
        self.name = "Tone Mapping"
        self.icon_path = "ui/PF2_Icons/Tonemap.png"
        self.properties = [
            Tool.Property("enabled", "Tone Mapping", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("strength", "Strength", "Slider", 90, max=100, min=0),
            Tool.Property("bleed", "Sharpness", "Slider", 10, max=100, min=0),
            Tool.Property("contrast", "Contrast", "Slider", 25, max=100, min=0),
            Tool.Property("two_pass", "Two Pass", "Toggle", False)
        ]

    def on_update(self, image):
        if(self.props["enabled"].get_value()):
            blur = self.props["bleed"].get_value()
            first_opacity = (self.props["contrast"].get_value() * -1) + 100
            second_opacity = self.props["strength"].get_value()
            two_pass = self.props["two_pass"].get_value()

            im = image

            iterations = 1
            if(two_pass):
                iterations = 2

            for i in range(iterations):
                # Convert to Grayscale
                gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

                # Invert Grayscale Image
                inverted = cv2.UMat(self._invert(gray))

                # Blur
                if(blur > 0):

                    height, width = image.shape[:2]
                    size = (height * width)
                    mul = numpy.math.sqrt(size) / 1064.416  # numpy.math.sqrt(1132982.0)

                    blur_size = 2 * round((round((blur/10.0) * mul) + 1) / 2) - 1
                    blurred = cv2.GaussianBlur(inverted, (int(blur_size), int(blur_size)), 0)
                else:
                    # Or, don't blur
                    blurred = inverted

                # First round of Blending
                colour = cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)
                colouredMap = cv2.addWeighted(colour, (first_opacity / 100), im, 1 - (first_opacity / 100), 0).get()

                # Overlay
                bpp = int(str(im.dtype).replace("uint", "").replace("float", ""))
                blended = self._overlay(colouredMap, im, float((2 ** bpp) - 1), im.dtype)

                # Second round of Blending
                im = cv2.addWeighted(blended, (second_opacity / 100), im, 1 - (second_opacity / 100), 0)

            return im

        else:
            return image





    def _invert(self, image):
        return image.max() - image

    def _overlay(self, B, A, bpp, utype):
        a = A / bpp
        b = B / bpp
        merged = (1 - 2 * b) * a ** 2 + 2 * a * b
        return (merged * bpp).astype(utype)
