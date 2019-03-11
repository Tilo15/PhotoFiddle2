import cv2
import numpy

import Tool
from PF2.Tools import Contrast
from PF2.Utilities import Blending
from PF2.Utilities import invert
from PF2.Scalar import Scalar


class Details(Tool.Tool):
    def on_init(self):
        self.id = "details"
        self.name = "Details and Edges"
        self.icon_path = "ui/PF2_Icons/Details.png"
        self.properties = [
            # Detailer
            Tool.Property("d_enabled", "Detailer", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("d_strength", "Strength", "Slider", 30, max=100, min=0),
            Tool.Property("d_detail", "Detail", "Slider", 15, max=100, min=0),
            Tool.Property("d_sint", "Highlight Intensity", "Slider", 0, max=100, min=-100),
            Tool.Property("d_mint", "Midtone Intensity", "Slider", 0, max=100, min=-100),
            Tool.Property("d_hint", "Shadow Intensity", "Slider", 0, max=100, min=-100),
            Tool.Property("d_slum", "Highlight Luminosity", "Slider", 0, max=100, min=-100),
            Tool.Property("d_mlum", "Midtone Luminosity", "Slider", 0, max=100, min=-100),
            Tool.Property("d_hlum", "Shadow Luminosity", "Slider", 0, max=100, min=-100),
            Tool.Property("d_pcont", "Restorative Contrast", "Slider", 0, max=100, min=0),
            # Edges
            Tool.Property("e_enabled", "Edges", "Header", False, has_toggle=True, has_button=False),
            Tool.Property("e_strength", "Strength", "Slider", 30, max=100, min=0),
            Tool.Property("e_fthresh", "First Threshold", "Slider", 100, max=1000, min=0),
            Tool.Property("e_sthresh", "Second Threshold", "Slider", 200, max=1000, min=0),
        ]

        self.contrast_tool = Contrast.Contrast()
        self.contrast_tool_restore = Contrast.Contrast()

    def on_update(self, image):
        im = image.image
        if(self.props["d_enabled"].get_value()):
            strength = self.props["d_strength"].get_value()
            detail = self.props["d_detail"].get_value()
            self.contrast_tool.props["highlight_contrast"].set_value(self.props["d_hint"].get_value())
            self.contrast_tool.props["midtone_contrast"].set_value(self.props["d_mint"].get_value())
            self.contrast_tool.props["shadow_contrast"].set_value(self.props["d_sint"].get_value())
            self.contrast_tool.props["highlight_brightness"].set_value(self.props["d_hlum"].get_value())
            self.contrast_tool.props["midtone_brightness"].set_value(self.props["d_mlum"].get_value())
            self.contrast_tool.props["shadow_brightness"].set_value(self.props["d_slum"].get_value())
            pcont = self.props["d_pcont"].get_value()

            # Convert to Grayscale
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

            # Invert
            edged = invert(gray, image.np)

            # Apply Brightness and Contrast
            image.image = edged
            edged = self.contrast_tool.on_update(image)

            # Blur
            if(detail > 0):
                size = (image.height * image.width)
                mul = numpy.math.sqrt(size) / 1064.416

                blur_size = abs(2 * round((round(detail*mul) + 1) / 2) - 1)
                blurred = cv2.GaussianBlur(edged, (int(blur_size), int(blur_size)), 0)
            else:
                blurred = edged


            # Overlay
            colour = cv2.cvtColor(blurred, cv2.COLOR_GRAY2BGR)
            blended = Blending.overlay(im, colour, image.np)

            # Restore Contrast
            self.contrast_tool_restore.props["highlight_contrast"].set_value(pcont * 0.25)
            self.contrast_tool_restore.props["midtone_contrast"].set_value(pcont * 0.5)
            self.contrast_tool_restore.props["shadow_contrast"].set_value(pcont * 0.25)
            image.image = blended
            cfixed = self.contrast_tool_restore.on_update(image)

            # Blend
            if(strength != 100):
                im = cv2.addWeighted(cfixed, (strength/100), im, 1 - (strength/100), 0)
            else:
                im = cfixed


        if(self.props["e_enabled"].get_value()):
            strength = self.props["e_strength"].get_value()
            t1 = self.props["e_fthresh"].get_value()
            t2 = self.props["e_sthresh"].get_value()
            # TODO
            # Convert to 8 Bit
            # eight = cv2.
            # eight = cv2.add(Scalar(0), im, dtype=)

            # Make Grayscale
            grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

            # Find edges
            edged = cv2.Canny(grey, t1, t2)

            # Convert edges to colour
            colour = cv2.cvtColor(edged, cv2.COLOR_GRAY2BGR)

            colour[colour != 0] = 255
            colour[colour == 0] = 128

            # Convert edges to current bpp
            nbpp = (colour / 255.0) * (2 ** bpp)

            # Blur?
            blurred = cv2.GaussianBlur(nbpp, (7, 7), 0)

            # Uhh
            blurred[blurred == (2 ** bpp) - 1] = ((2 ** bpp) - 1) / 2.0

            # I'm going to be honest, I just copied this one from
            # PhotoFiddle 1, I don't know what I was doing
            overlayed = self._overlay(blurred, im, float((2 ** bpp) - 1), im.dtype)

            out = cv2.addWeighted(overlayed, (strength / 100), im, 1 - (strength / 100), 0)

            im = out

        return im


    def _overlay(self, B, A, bpp, utype):
        a = A / bpp
        b = B / bpp
        merged = (1 - 2 * b) * a ** 2 + 2 * a * b
        return (merged * bpp).astype(utype)

