import numpy
from PF2.VectorMask import Path


class VectorMask:
    def __init__(self):
        self.paths = []
        self.width = 0
        self.height = 0
        self.__map = None

    def set_dimentions(self, width, height):
        self.width = width
        self.height = height

    def get_new_path(self, brush_size, brush_feather, scale, additive):
        path = Path.Path(brush_size, brush_feather, scale, additive)
        self.paths.append(path)
        return path

    def get_mask_map(self):
        if(self.has_updated()):

            map = numpy.zeros((self.height, self.width, 1), dtype=numpy.uint8)

            for path in self.paths:
                map = path.get_mask_map(map)

            map32 = map.astype(numpy.float32)
            map32 = map32 / 255.0

            self.__map = map32

        return self.__map

    def has_updated(self):
        res = True
        for path in self.paths:
            res &= path.has_rendered

        return not res



    def get_vector_mask_dict(self):
        paths = []
        for path in self.paths:
            paths.append(path.get_path_dict())

        return {
            "width": self.width,
            "height": self.height,
            "paths": paths
        }

    def set_from_vector_mask_dict(self, dict):
        self.width = dict["width"]
        self.height = dict["height"]
        paths = []
        for path in dict["paths"]:
            paths.append(Path.Path.new_from_dict(path))

        self.paths = paths