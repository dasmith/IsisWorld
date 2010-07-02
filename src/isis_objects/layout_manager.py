"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath, Quat

# Various layout managers used to generate coordinates for placing objects

class LayoutManager():
    def add(self, obj):
        return (0, 0, 0)

class HorizontalGridLayout(LayoutManager):
    """Arranges objects in rows within the given area"""
    def __init__(self, area, height, padw = .05, padh = .05):
        self.w, self.h = area
        self.z = height
        self.px, self.py = (0, 0)
        self.maxh = 0
        self.padw = padw
        self.padh = padh
    def add(self, obj):
        ow = obj.width+self.padw
        oh = obj.length+self.padh
        if self.px+ow > self.w:
            self.py += self.maxh
            self.px = 0
            self.maxh = 0
            if self.py+oh > self.h:
                return (0, 0, self.z)
        x = self.px
        self.px += ow
        if oh > self.maxh:
            self.maxh = oh
        return (x-(self.w-obj.width)/2.0, self.py-(self.h-obj.height)/2.0, self.z)


