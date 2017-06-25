import cv2
import numpy


class Histogram:
    @staticmethod
    def draw_hist(image, path):
        bpp = float(str(image.dtype).replace("uint", "").replace("float", ""))
        img = ((image/2**bpp)*255).astype('uint8')
        bpp = float(str(img.dtype).replace("uint", "").replace("float", ""))
        hv = 2 ** bpp
        hist = numpy.zeros(shape=(128, 330, 3))

        color = ('b', 'g', 'r')
        for i, col in enumerate(color):
            histr = cv2.calcHist([img], [i], None, [hv], [0, hv])
            for i2, hval in enumerate(histr):
                hi = max(histr)
                hist[int(-(hval / hi) * 127) + 127][int((i2 / hv) * 330)][i] = 255;

        cv2.imwrite(path, hist)
