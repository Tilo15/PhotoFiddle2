import numpy

import Tool


class Contrast(Tool.Tool):
    def on_init(self):
        self.id = "contrast"
        self.name = "Brightness and Contrast"
        self.icon_path = "ui/PF2_Icons/Contrast.png"
        self.properties = [
            Tool.Property("header", "Brightness and Contrast", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("overall_brightness", "Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("overall_contrast", "Contrast", "Slider", 0, max=50, min=-50),
            Tool.Property("tonal_header", "Tonal Brightness and Contrast", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("highlight_brightness", "Highlight Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("highlight_contrast", "Highlight Contrast", "Slider", 0, max=50, min=-50),
            Tool.Property("midtone_brightness", "Midtone Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("midtone_contrast", "Midtone Contrast", "Slider", 0, max=50, min=-50),
            Tool.Property("shadow_brightness", "Shadow Brightness", "Slider", 0, max=50, min=-50),
            Tool.Property("shadow_contrast", "Shadow Contrast", "Slider", 0, max=50, min=-50),
            Tool.Property("tonal_header", "Tonal Bleed Fraction", "Header", None, has_toggle=False,
                          has_button=False),
            Tool.Property("highlight_bleed", "Highlight Bleed", "Slider", 0.5, max=1, min=0.001),
            Tool.Property("midtone_bleed", "Midtone Bleed", "Slider", 0.5, max=1, min=0.001),
            Tool.Property("shadow_bleed", "Shadow Bleed", "Slider", 0.5, max=1, min=0.001),
        ]

    def on_update(self, im):
        # Apply Contrast Stuff
        if(not self.is_default()):
            ob = self.props["overall_brightness"].get_value()
            oc = -self.props["overall_contrast"].get_value()

            hb = self.props["highlight_brightness"].get_value()
            hc = self.props["highlight_contrast"].get_value()
            mb = self.props["midtone_brightness"].get_value()
            mc = self.props["midtone_contrast"].get_value()
            sb = self.props["shadow_brightness"].get_value()
            sc = self.props["shadow_contrast"].get_value()

            hbl = self.props["highlight_bleed"].get_value()
            mbl = self.props["midtone_bleed"].get_value()
            sbl = self.props["shadow_bleed"].get_value()

            # Add overall brightness
            hb += ob
            mb += ob
            sb += ob

            # Add overall contrast

            hc -= oc
            mc -= oc
            sc -= oc


            # Bits per pixel
            bpp = float(str(im.dtype).replace("uint", "").replace("float", ""))
            # Pixel value range
            np = float(2 ** bpp - 1)

            out = im.astype(numpy.float32)

            # Highlights

            isHr = self._is_highlight(out, (3.0 / hbl))
            if (hc != 0.0):
                # Highlight Contrast
                hn = np + 4
                hc = (hc / 100.0) * np + 0.8
                out = (((hn * ((hc * isHr) + np)) / (np * (hn - (hc * isHr)))) * (out - np / 2.0) + np / 2.0)

            if (hb != 0.0):
                # Highlight Brightness
                out = (out + ((hb * isHr) / 100.0) * np)

            # Midtones

            isMr = self._is_midtone(out, (3.0 / mbl))
            if (mc != 0.0):
                # Midtone Contrast
                hn = np + 4
                mc = (mc / 100.0) * np + 0.8
                out = (((hn * ((mc * isMr) + np)) / (np * (hn - (mc * isMr)))) * (out - np / 2.0) + np / 2.0)

            if (mb != 0.0):
                # Midtone Brightness
                out = (out + ((mb * isMr) / 100.0) * np)

            # Shadows

            isSr = self._is_shadow(out, (3.0 / sbl))
            if (sc != 0.0):
                # Shadow Contrast
                hn = np + 4
                sc = (sc / 100.0) * np + 0.8
                out = (((hn * ((sc * isSr) + np)) / (np * (hn - (sc * isSr)))) * (out - np / 2.0) + np / 2.0)

            if (sb != 0.0):
                # Shadow Brightness
                out = (out + ((sb * isSr) / 100.0) * np)

            # Clip any values out of bounds
            out[out < 0.0] = 0.0
            out[out > np] = np

            return out.astype(im.dtype)
        else:
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

