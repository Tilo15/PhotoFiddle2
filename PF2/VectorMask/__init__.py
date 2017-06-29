import numpy
from PF2.VectorMask import Path


class VectorMask:
    def __init__(self):
        self.paths = []
        self.width = 0
        self.height = 0

    def set_dimentions(self, width, height):
        self.width = width
        self.height = height

    def get_new_path(self, brush_size, brush_feather, scale, additive):
        path = Path.Path(brush_size, brush_feather, scale, additive)
        self.paths.append(path)
        return path

    def get_mask_map(self):
        map = numpy.zeros((self.height, self.width, 1), dtype=numpy.uint8)

        print(map.shape)

        for path in self.paths:
            map = path.get_mask_map(map)

        print(map.shape)

        map32 = map.astype(numpy.float32)
        map32 = map32 / 255.0

        print(map32.shape)

        return map32

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