"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath, Quat

# Various layout managers used to generate coordinates for placing objects

class LayoutManager():
    def add(self, obj):
        return (0, 0, 0)
    def remove(self, obj):
        pass

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
        ow = obj.getWidth()+self.padw*2
        oh = obj.getLength()+self.padh*2
        if self.px+ow > self.w:
            self.py += self.maxh
            self.px = 0
            self.maxh = 0
            if self.py+oh > self.h:
                return None
        x = self.px
        self.px += ow
        if oh > self.maxh:
            self.maxh = oh
        return (x-(self.w-ow)/2.0, self.py-(self.h-oh)/2.0, self.z+obj.getHeight())


class SlotLayout(LayoutManager):
    """Arranges objects into pre-defined (x, y, z) slots"""
    def __init__(self, slots):
        self.slots = slots
        self.map = {}
    def add(self, obj):
        for s in self.slots:
            if not s in self.map:
                self.map[s] = obj
                return s
        return None
    def remove(self, obj):
        key = None
        for k, o in self.map.iteritems():
            if o == obj:
                key = k
                break
        if key:
            del self.map[key]