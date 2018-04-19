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

            out = cv2.UMat(im)


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


                #out = (((hn * ((hc * isHr) + np)) / (np * (hn - (hc * isHr)))) * (out - np / 2.0) + np / 2.0)






            if (hb != 0.0):
                print(hb)
                # Highlight Brightness
                calc = cv2.multiply(isHr, Scalar(hb), dtype=cv2.CV_64F)
                calc = cv2.divide(calc, Scalar(100.0))
                calc = cv2.multiply(calc, Scalar(np))
                out = cv2.add(out, calc, dtype=cv2.CV_64F)

                #out = (out + ((hb * isHr) / 100.0) * np)

            # # Midtones

            # isMr = self._is_midtone(out, (3.0 / mbl))
            # if (mc != 0.0):
            #     # Midtone Contrast
            #     hn = np + 4
            #     mc = (mc / 100.0) * np + 0.8
            #     out = (((hn * ((mc * isMr) + np)) / (np * (hn - (mc * isMr)))) * (out - np / 2.0) + np / 2.0)

            # if (mb != 0.0):
            #     # Midtone Brightness
            #     out = (out + ((mb * isMr) / 100.0) * np)

            # # Shadows

            # isSr = self._is_shadow(out, (3.0 / sbl))
            # if (sc != 0.0):
            #     # Shadow Contrast
            #     hn = np + 4
            #     sc = (sc / 100.0) * np + 0.8
            #     out = (((hn * ((sc * isSr) + np)) / (np * (hn - (sc * isSr)))) * (out - np / 2.0) + np / 2.0)

            # if (sb != 0.0):
            #     # Shadow Brightness
            #     out = (out + ((sb * isSr) / 100.0) * np)


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
    
        # icopy = cv2.add(image, Scalar(0), dtype=cv2.CV_64F)
        # bleed_mask = cv2.inRange(icopy, Scalar(mif - bleed), Scalar(mif))
        # bleed_mask = cv2.bitwise_not(icopy, mask=bleed_mask)


        # #cv2.normalize(bleed_mask, bleed_mask, alpha=0, beta=np, norm_type=cv2.NORM_MINMAX)
        # bleed_mask = cv2.subtract(Scalar(mif), bleed_mask, dtype=cv2.CV_64F)
        # bleed_mask = cv2.divide(bleed_mask, Scalar(bleed))
        # #bleed_mask = cv2.multiply(bleed_mask, Scalar(-1))
        # #bleed_mask = cv2.add(bleed_mask, Scalar(1))
        # cv2.normalize(bleed_mask, bleed_mask, alpha=0, beta=np, norm_type=cv2.NORM_MINMAX)
        # ret, highlight_mask = cv2.threshold(icopy, mif, np, cv2.THRESH_BINARY)

        # mask = cv2.bitwise_or(bleed_mask, highlight_mask)
        # cv2.normalize(mask, mask, alpha=0.0, beta=1.0, norm_type=cv2.NORM_MINMAX)

        # cv2.imshow("Display window",mask)
        # # icopy = cv2.add(image, Scalar(0), dtype=cv2.CV_64F)

        # # ret, icopy = cv2.threshold(icopy, mif - bleed, np, cv2.THRESH_TOZERO)
        # # icopy = cv2.subtract(Scalar(mif), icopy)
        # # icopy = cv2.divide(icopy, Scalar(bleed))
        # # icopy = cv2.multiply(icopy, Scalar(-1))
        # # icopy = cv2.add(icopy, Scalar(1))
        # # ret, icopy = cv2.threshold(icopy, mif, 1.0, cv2.THRESH_TOZERO_INV)



        # NEW

        # Make everything below (mif - bleed) = 0
        icopy = cv2.add(image, Scalar(0), dtype=cv2.CV_32F)
        ret, icopy = cv2.threshold(icopy, mif - bleed, np, cv2.THRESH_TOZERO)

        bld = cv2.subtract(Scalar(mif), icopy)
        bld = cv2.divide(bld, Scalar(bleed))
        bld = cv2.multiply(bld, Scalar(-1))
        bld = cv2.add(bld, Scalar(1))

        #res, bleed_mask = cv2.threshold(icopy, mif, np, cv2.THRESH_BINARY_INV)
        res, bleed_mask = cv2.threshold(icopy, 0.0, np, cv2.THRESH_BINARY)
        #bleed_mask = cv2.bitwise_and(bleed_mask, not_zero_mask)

        bleed_mask = cv2.cvtColor(bleed_mask, cv2.COLOR_BGR2GRAY)
        bleed_mask = cv2.inRange(bleed_mask, 0.1, np)
        cv2.normalize(bleed_mask, bleed_mask, 0, 255, cv2.NORM_MINMAX,cv2.CV_8U)



        icopy = cv2.bitwise_not(icopy, mask=bleed_mask)
        icopy = cv2.add(icopy, bld, mask=bleed_mask)

        cv2.imshow("Display window", icopy)

        return icopy


        #icopy[icopy < mif - bleed] = 0.0
        #icopy[(icopy < mif) * (icopy != 0.0)] = ((mif - (icopy[(icopy < mif) * (icopy != 0.0)])) / bleed) * -1 + 1
        #icopy[icopy >= mif] = 1.0
        #return icopy

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

