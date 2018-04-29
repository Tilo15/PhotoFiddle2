import cv2
from PF2.Scalar import Scalar


def get_curve(im, position, invert, bleed, np):
    # Position is an int from 0 to 2
    floor = np / 3.0 * position
    bld = np / float(bleed)

    # Calculate bleed
    crv = cv2.subtract(Scalar(floor), im)
    crv = cv2.divide(crv, Scalar(bld))
    if(invert):
        crv = cv2.multiply(crv, Scalar(-1))
    crv = cv2.add(crv, Scalar(1))

    res, crv = cv2.threshold(crv, 0.0, 1.0, cv2.THRESH_TOZERO)
    res, crv = cv2.threshold(crv, 1.0, 1.0, cv2.THRESH_TRUNC)

    return crv


def combine_curve(a, b):
    return cv2.min(a, b)


def is_highlight(image, bleed_value = 6.0, np=255):
    return get_curve(image, 2, True, bleed_value, np)

def is_midtone(image, bleed_value = 6.0, np=255):
    curve1 = get_curve(image, 2, False, bleed_value, np)
    curve2 = get_curve(image, 1, True, bleed_value, np)
    return combine_curve(curve1, curve2)

def is_shadow(image, bleed_value = 6.0, np=255):
    return get_curve(image, 1, False, bleed_value, np)
