import numpy
import cv2
from PF2.Scalar import Scalar
from PF2.Utilities import HMS
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
            Tool.Property("hist_stretch", "Histogram Strecthing", "Header", None, has_toggle=False, has_button=False),
            Tool.Property("left_stretch", "Left Stretch", "Slider", 0, max=50, min=-50),
            Tool.Property("right_stretch", "Right Stretch", "Slider", 0, max=50, min=-50),
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

            ls = -self.props["left_stretch"].get_value()
            rs = -self.props["right_stretch"].get_value()

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

            out = cv2.UMat(im.astype("float32"))


            # Histogram Stretch
            if(rs != 0 or ls != 0):
                maxpxv = np + (rs/100.0)*np
                minpxv = 0 - (ls/100.0)*np

                #out = (out - minpxv) * (np/float(maxpxv))


                out = cv2.subtract(out, Scalar(minpxv))
                out = cv2.multiply(out, Scalar(np/float(maxpxv)))
                
                
            


            # Highlights

            isHr = HMS.is_highlight(out, (3.0 / hbl), np)
            if (hc != 0.0):
                # Highlight Contrast
                #out = (((hn * ((hc * isHr) + np)) / (np * (hn - (hc * isHr)))) * (out - np / 2.0) + np / 2.0)
                # The following is based on the above formula

                hn = np + 4
                hc = (hc / 100.0) * np + 0.8

                hc_x_isHr = cv2.multiply(isHr, Scalar(hc))
                numerator = cv2.add(hc_x_isHr, Scalar(np))
                numerator = cv2.multiply(numerator, Scalar(hn))
            
                denominator = cv2.subtract(Scalar(hn), hc_x_isHr)
                denominator = cv2.multiply(denominator, Scalar(np))

                left = cv2.divide(numerator, denominator)

                right = cv2.subtract(out, Scalar(np / 2.0))                

                out = cv2.multiply(left, right)
                out = cv2.add(out, Scalar(np / 2.0))
                
                res, out = cv2.threshold(out, np, np, cv2.THRESH_TRUNC)


            if (hb != 0.0):
                # Highlight Brightness
                #out = (out + ((hb * isHr) / 100.0) * np)
                # The following is based on the above formula
                calc = cv2.multiply(isHr, Scalar(np))
                calc = cv2.multiply(calc, Scalar(hb/100.0))
                out = cv2.add(out, calc)

            # Midtones


            isMt = HMS.is_midtone(out, (3.0 / mbl), np)
            if (mc != 0.0):
                # Midtone Contrast
                #out = (((hn * ((hc * isHr) + np)) / (np * (hn - (hc * isHr)))) * (out - np / 2.0) + np / 2.0)
                # The following is based on the above formula

                hn = np + 4
                hc = (mc / 100.0) * np + 0.8

                hc_x_isMt = cv2.multiply(isMt, Scalar(hc))
                numerator = cv2.add(hc_x_isMt, Scalar(np))
                numerator = cv2.multiply(numerator, Scalar(hn))
            
                denominator = cv2.subtract(Scalar(hn), hc_x_isMt)
                denominator = cv2.multiply(denominator, Scalar(np))

                left = cv2.divide(numerator, denominator)

                right = cv2.subtract(out, Scalar(np / 2.0))                

                out = cv2.multiply(left, right)
                out = cv2.add(out, Scalar(np / 2.0))


            if (mb != 0.0):
                # Midtone Brightness
                #out = (out + ((hb * isHr) / 100.0) * np)
                # The following is based on the above formula
                calc = cv2.multiply(isMt, Scalar(np))
                calc = cv2.multiply(calc, Scalar(mb/100.0))
                out = cv2.add(out, calc)

            # Shadows


            isSh = HMS.is_shadow(out, (3.0 / sbl), np)
            if (sc != 0.0):
                # Shadow Contrast
                #out = (((hn * ((hc * isHr) + np)) / (np * (hn - (hc * isHr)))) * (out - np / 2.0) + np / 2.0)
                # The following is based on the above formula

                hn = np + 4
                hc = (sc / 100.0) * np + 0.8

                hc_x_isSh = cv2.multiply(isSh, Scalar(hc))
                numerator = cv2.add(hc_x_isSh, Scalar(np))
                numerator = cv2.multiply(numerator, Scalar(hn))
            
                denominator = cv2.subtract(Scalar(hn), hc_x_isSh)
                denominator = cv2.multiply(denominator, Scalar(np))

                left = cv2.divide(numerator, denominator)

                right = cv2.subtract(out, Scalar(np / 2.0))                

                out = cv2.multiply(left, right)
                out = cv2.add(out, Scalar(np / 2.0))


            if (sb != 0.0):
                # Shadow Brightness
                #out = (out + ((hb * isHr) / 100.0) * np)
                # The following is based on the above formula
                calc = cv2.multiply(isSh, Scalar(np))
                calc = cv2.multiply(calc, Scalar(sb/100.0))
                out = cv2.add(out, calc)


            out = out.get()

            # Clip any values out of bounds
            out[out < 0.0] = 0.0
            out[out > np] = np
            return out.astype(im.dtype)
        else:
            return im


