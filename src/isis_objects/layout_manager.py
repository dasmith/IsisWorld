"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath, Quat

# Various layout managers used to generate coordinates for placing objects

class LayoutManager():
    def __init__(self):
        self.items = []
    def add(self, obj):
        self.items.append(obj)
        return (0, 0, 0)
    def remove(self, obj):
        self.items.remove(obj)
    def getItems(self):
        return self.items

class HorizontalGridLayout(LayoutManager):
    """Arranges objects in rows within the given area"""
    def __init__(self, area, height, padw = .05, padh = .05):
        LayoutManager.__init__(self)
        self.w, self.h = area
        self.z = height
        self.px, self.py = (0, 0)
        self.maxh = 0
        self.padw = padw
        self.padh = padh
    def add(self, obj):
        LayoutManager.add(self, obj)
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
        return (x-(self.w-ow)/2.0, self.py-(self.h-oh)/2.0, self.z)


class SlotLayout(LayoutManager):
    """Arranges objects into pre-defined (x, y, z) slots"""
    def __init__(self, slots):
        LayoutManager.__init__(self)
        self.slots = slots
        self.map = {}
    def add(self, obj):
        LayoutManager.add(self, obj)
        for s in self.slots:
            if not s in self.map:
                self.map[s] = obj
                return s
        return None
    def remove(self, obj):
        LayoutManager.remove(self, obj)
        key = None
        for k, o in self.map.iteritems():
            if o == obj:
                key = k
                break
        if key:
            del self.map[key]

class HorizontalGridSlotLayout(SlotLayout):
    """Creates a grid of slots in the given area centered at 0,0"""
    def __init__(self, area, height, nx, ny, padw = .5, padh = .5):
        LayoutManager.__init__(self)
        if nx == 1 and ny == 1:
            slots = [(0, 0, height+1)]
        else:
            width = area[0]-2*padw
            length = area[1]-2*padh
            dx = width/nx
            dy = length/ny
            slots = [(x*dx-width/2, y*dy-length/2, height) for x in xrange(0, nx) for y in xrange(0, ny)]
        SlotLayout.__init__(self, slots)