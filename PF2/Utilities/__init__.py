import cv2
from PF2.Scalar import Scalar

def invert(im, np):
    inv = cv2.multiply(im, Scalar(-1))
    return cv2.add(inv, Scalar(np))

def clip(im, max_value, min_value, np):
    res, clipped = cv2.threshold(im, min_value, np, cv2.THRESH_TOZERO)
    res, clipped = cv2.threshold(clipped, max_value, np, cv2.THRESH_TRUNC)
    return clipped