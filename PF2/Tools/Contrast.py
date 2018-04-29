import numpy
import cv2
from PF2.Scalar import Scalar
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

            isHr = self._is_highlight(out, (3.0 / hbl), np)
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


            #isMt = self._is_midtone(out, (3.0 / mbl), np)
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


            isSh = self._is_shadow(out, (3.0 / sbl), np)
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


    def _is_highlight(self, image, bleed_value = 6.0, np=255):
        bleed = float(np / bleed_value)
        mif = np / 3.0 * 2.0

        #icopy[icopy < mif - bleed] = 0.0
        #icopy[(icopy < mif) * (icopy != 0.0)] = ((mif - (icopy[(icopy < mif) * (icopy != 0.0)])) / bleed) * -1 + 1
        #icopy[icopy >= mif] = 1.0
        #return icopy
        # The following is based upon the above old procedure

        # Make everything below (mif - bleed) = 0
        icopy = cv2.add(image, Scalar(0), dtype=cv2.CV_32F)
        ret, icopy = cv2.threshold(icopy, mif - bleed, np, cv2.THRESH_TOZERO)

        # Calculate bleed
        bld = cv2.subtract(Scalar(mif), icopy)
        bld = cv2.divide(bld, Scalar(bleed))
        bld = cv2.multiply(bld, Scalar(-1))
        bld = cv2.add(bld, Scalar(1))
        res, bld = cv2.threshold(bld, 0.0, 1.0, cv2.THRESH_TOZERO)

        return bld



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

    def _is_shadow(self, image, bleed_value=6.0, np=255):
        inv = cv2.multiply(image, Scalar(-1))
        inv = cv2.add(inv, Scalar(np))
        return self._is_highlight(inv, bleed_value,)


        bleed = float(np / bleed_value)
        mir = np / 3.0

        icopy = cv2.add(image, Scalar(0), dtype=cv2.CV_32F)

        # Make everything below mir = 1
        # ret, shadow_mask = cv2.threshold(icopy, mir, np, cv2.THRESH_BINARY_INV)
        # icopy = cv2.bitwise_and(icopy, shadow_mask)
    
        # Make everything above (mir + bleed) = 0
        #ret, icopy = cv2.threshold(icopy, mir + bleed, np, cv2.THRESH_TOZERO_INV)

        # Calculate bleed
        bld = cv2.subtract(icopy, Scalar(mir))
        bld = cv2.divide(bld, Scalar(bleed))
        bld = cv2.multiply(bld, Scalar(-1))
        bld = cv2.add(bld, Scalar(1))
        res, bld = cv2.threshold(bld, 1.0, np, cv2.THRESH_TRUNC)

        print(bld.get().max(), bld.get().min())
        cv2.imshow("Display window", bld)
        cv2.imshow("Display thresh", icopy)

        return bld

        # icopy[icopy <= mir] = 1.0
        # icopy[icopy > mir + bleed] = 0.0
        #icopy[icopy > mir] = (((icopy[(icopy > mir) * (icopy != 0.0)]) - mir) / bleed) * -1 + 1
        # return icopy

