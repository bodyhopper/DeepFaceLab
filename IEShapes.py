import numpy as np
import cv2

from enum import IntEnum

class IEShapeType(IntEnum):
    NONE = 0
    POLYGON = 1
    
class IEIncludeType(IntEnum):
    EXCLUDE = 0
    INCLUDE = 1
        
class IEShape():
    def __init__(self, shape_type, include_type):
        self.shape_type = shape_type
        self.include_type = include_type
    
class IEShapePolygon(IEShape):
    def __init__(self, include_type):
        super().__init__(IEShapeType.POLYGON, include_type)
        
        self.points = np.empty( (0,2), dtype=np.float32 )
        self.n_max = self.n = 0

    def add_point(self, x,y):
        self.points = np.append(self.points[0:self.n], [ ( float(x), float(y) ) ], axis=0)
        self.n_max = self.n = self.n + 1

    def undo(self):
        self.n = max(0, self.n-1)
        return self.n

    def redo(self):
        self.n = min(len(self.points), self.n+1)
        return self.n

    def redo_clip(self):
        self.points = self.points[0:self.n]
        self.n_max = self.n

    def get_last_point(self):
        return self.points[self.n-1]

    def get_points(self):
        return self.points[0:self.n]

    def set_points(self, points):
        self.points = np.array(points)
        self.n_max = self.n = len(points)

class IEShapes:
    def __init__(self):
        self.shapes = []

    def add_polygon(self, include_type):        
        poly = IEShapePolygon(include_type)        
        self.shapes.append ( poly )
        return poly

    def remove_polygon(self, poly):
        pass
        
    def get_polygons(self):
        return [shape for shape in self.shapes if shape.shape_type == IEShapeType.POLYGON]

    def __iter__(self):
        for shape in self.shapes:
            yield shape

    #def overlay_mask(self, mask):
    #    h,w,c = mask.shape
    #    white = (1,)*c
    #    black = (0,)*c
    #    for n in range(self.n):
    #        poly = self.shapes[n]
    #        if poly.n > 0:
    #            cv2.fillPoly(mask, [poly.points_to_n()], white if poly.type == 1 else black )

    #def dump(self):
    #    result = []
    #    for shape in self.shapes:
    #        pass
    #        #result += [ (l.type, l.points_to_n().tolist() ) ]
    #    return result

    #@staticmethod
    #def load(ie_polys=None):
    #    obj = IEShapes()
    #    if ie_polys is not None and isinstance(ie_polys, list):
    #        for (type, points) in ie_polys:
    #            obj.add(type)
    #            obj.n_list().set_points(points)
    #    return obj