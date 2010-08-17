"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath, Quat

# Various layout managers used to generate coordinates for placing objects

class LayoutManager():
    def __init__(self):
        self.items = []
    def add(self, obj):
        if not obj:
            return
        self.items.append(obj)
        return (0, 0, 0)
    def remove(self, obj):
        self.items.remove(obj)
    def getItems(self):
        return self.items


class RoomLayout(LayoutManager):
    """Arranges objects in rows around the perimeter"""
    def __init__(self, area, height, padw = .05, padh = .05):
        LayoutManager.__init__(self)
        self.w, self.h = area
        self.z = height
        self.px, self.py = (0, 0)
        self.maxd = 0
        self.padw = padw
        self.padh = padh
        self.side = 0;
        self.sides = [self.__addn, self.__adde, self.__adds, self.__addw]
    def add(self, obj):
        """Tries to add the object to the current side"""
        if self.side < len(self.sides) and LayoutManager.add(self, obj):
            # There are still some empty walls
            ow = obj.getWidth()+self.padw*2
            oh = obj.getLength()+self.padh*2
            coords = self.sides[self.side](obj, ow, oh)
            if coords:
                # Recalculate coordinates returned from the top left point to the object's center
                return (coords[0]-(self.w-ow)/2.0+self.padw, coords[1]-(self.h-oh)/2.0+self.padh, self.z)
        return
    def __addn(self, obj, ow, oh):
        """Tries to add the object along the north side"""
        if self.px+ow > self.w:
            # No more room on this side, prepare coordinates for next wall
            self.side += 1
            self.py = self.maxd
            self.maxd = 0
            return self.__adde(obj, ow, oh)
        # Calculate the 2D coordinates for the top left of the object
        x = self.px
        self.px += ow
        # Compute maximum distance from this wall for the starting point of the next
        # Once this wall is full
        if oh > self.maxd:
            self.maxd = oh
        return (x, 0)
    def __adde(self, obj, ow, oh):
        """Tries to add the object along the east side"""
        if self.py+oh > self.h:
            # No more room on this side, prepare coordinates for next wall
            self.side += 1
            self.px = self.w-self.maxd
            self.maxd = 0
            return self.__adds(obj, ow, oh)
        # Calculate the 2D coordinates for the top left of the object
        y = self.py
        self.py += oh
        # Compute maximum distance from this wall for the starting point of the next
        # Once this wall is full
        if ow > self.maxd:
            self.maxd = ow
        return (self.w-ow, y)
    def __adds(self, obj, ow, oh):
        """Tries to add the object along the south side"""
        if self.px-ow < 0:
            # No more room on this side, prepare coordinates for next wall
            self.side += 1
            self.py = self.h-self.maxd
            return self.__addw(obj, ow, oh)
        # Calculate the 2D coordinates for the top left of the object
        x = self.px
        self.px -= ow
        # Compute maximum distance from this wall for the starting point of the next
        # Once this wall is full
        if oh > self.maxd:
            self.maxd = oh
        return (x-ow, self.h-oh)
    def __addw(self, obj, ow, oh):
        """Tries to add the object along the west side"""
        if self.py-oh < 0:
            # No more room on this side, room is full
            self.side += 1
            LayoutManager.remove(self, obj)
            return
        # Calculate the 2D coordinates for the top left of the object
        y = self.py
        self.py -= oh
        return (0, y-oh)


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
        if not LayoutManager.add(self, obj):
            return
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
        if not LayoutManager.add(self, obj):
            return
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
    """Creates a grid of slots in the given area centered at 0,0, nx slots wide by nx slots in length"""
    def __init__(self, area, height, nx, ny, padw = .5, padh = .5):
        LayoutManager.__init__(self)
        if nx <= 1 and ny <= 1:
            # Create a single slot centered on the item in question
            slots = [(0, 0, height+1)]
        else:
            #the width and height of the area to work in, minus the padding specified so objects don't end up on the edge of the area
            width = area[0]-2*padw
            length = area[1]-2*padh
            #calculate the spacing of each slot
            dx = width/nx
            dy = length/ny
            slots = [(x*dx-width/2, y*dy-length/2, height) for x in xrange(0, nx) for y in xrange(0, ny)]
        SlotLayout.__init__(self, slots)
