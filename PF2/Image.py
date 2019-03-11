import cv2
import numpy
from PF2.Scalar import Scalar
from PF2.Utilities import clip

class Image:
    def __init__(self, image, gpuEnabled = True):
        # Use GPU?
        self.gpu_enabled = gpuEnabled
        # Set the image
        self.set(image)
        # Bits per pixel
        self.bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
        # Pixel value range
        self.np = float(2 ** self.bpp - 1)
        # Dtype
        self.dtype = image.dtype

        self.height, self.width = image.shape[:2]

    def get(self):
        out = clip(self.image, self.np, 0, self.np)
        if(type(out) == cv2.UMat):
            out = out.get()

        return out.astype(self.dtype)

    def set(self, image):
        if(self.gpu_enabled):
            self.image = cv2.UMat(image)
            self.image = cv2.add(Scalar(0), self.image, dtype=cv2.CV_32F)
        else:
            self.image = image.copy()
            self.image = self.image.astype(numpy.float32)