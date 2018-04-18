import PF2.VectorMask

import cv2

import numpy


class Mask:
    def __init__(self, image, width, height):
        self.image = image
        self.mask = PF2.VectorMask.VectorMask()
        self.mask.set_dimentions(width, height)

    def get_mask_preview(self, image):
        mask =  self.mask.get_mask_map()

        if(type(mask) == numpy.ndarray):
            w, h = image.shape[:2]
            print(w, h)

            # Bits per pixel
            bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
            # Pixel value range
            np = float(2 ** bpp - 1)

            mask = cv2.resize(mask, (h, w), interpolation=cv2.INTER_AREA)
            inverted_map = (mask * -1) + 1
            image[0:, 0:, 2] = (np * mask) + (image[0:, 0:, 2] * inverted_map)

        return image