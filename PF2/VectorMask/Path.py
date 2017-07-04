import cv2
import numpy
from gi.repository import Gdk


class Path:
    def __init__(self, brush_size, brush_feather, scale, additive):
        self.points = []
        self.brush_size = brush_size
        self.scale = scale
        self.brush_feather = brush_feather
        self.additive = additive
        self.has_rendered = False

    def add_point(self, x, y, previewShape = None, fill = None):
        self.points.append([x,y])
        self.has_rendered = False
        if(previewShape != None and fill != None and len(self.points) > 1):
            preview = numpy.zeros(previewShape, dtype=numpy.uint8)
            points = self.points[-2:]
            sx = points[0][0]
            sy = points[0][1]
            fx = points[1][0]
            fy = points[1][1]
            cv2.line(preview, (sx, sy), (fx, fy), (fill), int(self.brush_size), cv2.LINE_4)

            return preview


    def get_mask_map(self, mask):
        self.has_rendered = True
        if(self.additive):
            return self.draw_additive_path(mask)
        else:
            return self.draw_subtractive_path(mask)

    def draw_subtractive_path(self, mask):
        self.draw_points(mask, self.points, 0)
        return mask

    def draw_additive_path(self, mask):
        map = numpy.zeros(mask.shape, dtype=numpy.uint8)

        self.draw_points(map, self.points, 255)

        if(self.brush_feather > 1):
            blur_size = 2 * round((round(self.brush_feather) + 1) / 2) - 1
            map = cv2.blur(map, (int(blur_size), int(blur_size)))
            map = map[:, :, numpy.newaxis]

        # Painful workaround for int overflow
        mask2 = mask.astype(numpy.uint16)
        mask2 = mask2 + map
        mask2[mask2 > 255] = 255
        mask = mask2.astype(numpy.uint8)

        return mask

    def draw_points(self, mask, points, value):
        for i in range(len(points) - 2):
            sx = int(self.points[i][0] * self.scale)
            sy = int(self.points[i][1] * self.scale)
            fx = int(self.points[i + 1][0] * self.scale)
            fy = int(self.points[i + 1][1] * self.scale)

            # print("[PATH.PY]", sx, sy, fx, fy)
            cv2.line(mask, (sx, sy), (fx, fy), (value), int(self.brush_size * self.scale), cv2.LINE_AA)

        return mask


    def get_path_dict(self):
        return {
            "brush_size": self.brush_size,
            "scale": self.scale,
            "brush_feather": self.brush_feather,
            "additive": self.additive,
            "points": self.points
        }

    @staticmethod
    def new_from_dict(dict):
        path = Path(dict["brush_size"], dict["brush_feather"], dict["scale"], dict["additive"])
        path.points = dict["points"]
        return path