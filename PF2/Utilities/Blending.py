import cv2
from PF2.Scalar import Scalar
from PF2.Utilities import clip

def overlay(A, B, np):
    a = cv2.divide(A, Scalar(np))
    b = cv2.divide(B, Scalar(np))

    # f(a,b) = (1 - 2b)a^2 + 2ba

    left = cv2.multiply(Scalar(2), b)
    left = cv2.subtract(Scalar(1), left)
    right = cv2.pow(a, 2)
    left = cv2.multiply(left, right)
    right = cv2.multiply(Scalar(2), b)
    right = cv2.multiply(right, a)
    merged = cv2.add(left, right)

    merged = cv2.multiply(merged, Scalar(np))
    
    return clip(merged, np, 0, np)