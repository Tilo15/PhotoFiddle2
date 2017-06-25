import cv2

import Tool
from scipy import ndimage

class Exposure(Tool.Tool):
    def on_init(self):
        self.id = "exposure"
        self.name = "Exposure"
        self.icon_path = "ui/PF2_Icons/Exposure.png"
        self.properties = [
            # Detailer
            Tool.Property("enabled", "Exposure", "Header", False, has_toggle=False, has_button=False),
            Tool.Property("exposure", "Overall Exposure", "Slider", 0, max=50, min=-50),
            Tool.Property("h_exposure", "Highlight Exposure", "Slider", 0, max=50, min=-50),
            Tool.Property("m_exposure", "Midtone Exposure", "Slider", 0, max=50, min=-50),
            Tool.Property("s_exposure", "Shadow Exposure", "Slider", 0, max=50, min=-50),
        ]

    def on_update(self, image):
        im = image
        if(not self.is_default()):
            ex = self.props["exposure"].get_value() * 0.0001
            hex = self.props["h_exposure"].get_value() * 0.0001
            mex = self.props["m_exposure"].get_value() * 0.0001
            sex = self.props["s_exposure"].get_value() * 0.0001


            if(hex != 0):
                ish = self._is_highlight(im)
                mul = 2**hex
                im[ish > 0] = im[ish > 0]*mul

            if(mex != 0):
                ish = self._is_midtone(im)
                mul = 2**mex
                im[ish > 0] = im[ish > 0] * mul

            if(sex != 0):
                ish = self._is_shadow(im)
                mul = 2**sex
                im[ish > 0] = im[ish > 0] * mul

            if(ex != 0):
                mul = 2 ** ex
                im = im * mul


        return im


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