"""  Objects defined by the IsisWorld simulator """
from math import sin, cos, pi
from pandac.PandaModules import NodePath, Quat
import pdb
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
        #if obj.model == "oven/oven":
            #pdb.set_trace()
        if self.side < len(self.sides) and LayoutManager.add(self, obj):
            # There are still some empty walls
        
            ow = obj.getWidth()+self.padw*2
            ol = obj.getLength()+self.padh*2
        
            coords = self.sides[self.side](obj, ow, ol)
            if coords:
                # Recalculate coordinates returned from the top left point to the object's center
                return (coords[0]-(self.w-ow)/2.0+self.padw, coords[1]-(self.h-ol)/2.0+self.padh, self.z)
        return
    
    def rotateValForOrientationVector(self, obj, desiredVec):
        
        # NOTE: This method is only actually called in branch fix_layout2 of the git repository
        # I originally wasn't planning on making 2 branches, but when I integrated this method into
        # the add methods to make the code cleaner, it stopped working as intended, so I made 
        # that a separate branch. 
        # I was also intending to fix something which I thought might be the source of a bug.
        # Let's say we end up adding the obj to the south wall. The way the add methods are organized,
        # we will first try the north and east walls. The code in here would rotate the obj once
        # for the north wall, and again for the east wall. When writing the rotate code I assumed
        # H would be 0, but it's not in this case, which was an oversight on my part.
        # The odd thing was that this code appears to work if you compare the orientation of the
        # oven to the wall we put it against (using the report from the print statements). However,
        # the code in fix_layout2, despite attempting to fix this bug, doesn't work. Interesting.
        
        # Returns the value by which obj should be rotated along X such that 
        # obj's orientation vector will be pointing in the direction of desiredVec
        # Does NOT actually rotate the object, that is the job of the calling function
        # The reason for this is because the calling function can change its mind as to which
        # wall to put the object against.
        
        # TODO It may be possible to determine a mathematical formula to set the rotation
        # value; that might be more elegant than this enumeration of all the possiblities.
        # I wrote down all the possibilities on paper, I don't quite see a formula, but I
        # can't claim to be great at geometry.
        
        if desiredVec == (0, -1): # south
            if obj.orientationVector[0] == 1: # Orientation vector points east
                return 90 # Now it will point south, away from the wall (when rotated by this value)
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                return 270 # Now it will point south when rotated
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                return 180 # Now it will point south when rotated
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                return 0 # Don't need to do anything
        elif desiredVec == (-1, 0): # west
            if obj.orientationVector[0] == 1: # Orientation vector points east
                return 180 # Now it will point west, away from the wall, when rotated
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                return 0 # Don't need to change it
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                return 270 # Now it will point west when rotated
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                return 90 # Now it will point west when rotated
        elif desiredVec == (0, 1): # north
            if obj.orientationVector[0] == 1: # Orientation vector points east
                return 270 # Now it points north, away from the wall, when rotated
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                return 90 # Now it will point north when rotated
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                return 0 # Don't need to change it
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                return 180 # Now it points north when rotated
        elif desiredVec == (1, 0): # east
            if obj.orientationVector[0] == 1: # Orientation vector points east
                return 0 # Don't need to change it
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                return 180 # Now it points east when rotated
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                return 90 # Now it points east when rotated
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                return 270 # Now it points east when rotated
        
        # TODO add functionality when the orientation vector is different (is this possible?)
        return 0 # For now, just don't make any possibly harmful changes
    
    def __addn(self, obj, ow, ol):
        """Tries to add the object along the north side"""
        if obj.orientationVector is not None:
            print "Added oven to north side"
            # Position the object as per its orientation vector
            # We don't need to worry about the z-axis, just examine the x and y axes
            if obj.orientationVector[0] == 1: # Orientation vector points east
                obj.rotateAlongX(90) # Now it points south, away from the wall
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                obj.rotateAlongX(270) # Now it points south
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                obj.rotateAlongX(180) # Now it points south
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                obj.rotateAlongX(0) # Don't need to do anything
        if self.px+ow > self.w:
            # No more room on this side, prepare coordinates for next wall
            self.side += 1
            self.py = self.maxd
            self.maxd = 0
            return self.__adde(obj, ow, ol)
        # Calculate the 2D coordinates for the top left of the object
        x = self.px
        self.px += ow
        # Compute maximum distance from this wall for the starting point of the next
        # Once this wall is full
        if ol > self.maxd:
            self.maxd = ol
        return (x, 0)
    def __adde(self, obj, ow, ol):
        """Tries to add the object along the east side"""
        # if length > width, rotate object so longest dimension is against wall.
        if obj.orientationVector is not None:
            print "Added oven to east side"
            # Position the object as per its orientation vector, we want it to point west
            # We don't need to worry about the z-axis, just examine the x and y axes
            if obj.orientationVector[0] == 1: # Orientation vector points east
                obj.rotateAlongX(180) # Now it points west, away from the wall
                #obj.rotateAlongX(0)
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                obj.rotateAlongX(0) # Don't need to change it
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                obj.rotateAlongX(270) # Now it points west
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                obj.rotateAlongX(90)
        if ow > ol and obj.orientationVector is None:
            #pdb.set_trace()
            obj.rotateAlongX(90)
            t = ow; ow = ol; ol = t
        if self.py+ol > self.h:
            # No more room on this side, prepare coordinates for next wall
            self.side += 1
            self.px = self.w-self.maxd
            self.maxd = 0
            return self.__adds(obj, ow, ol)
        # Calculate the 2D coordinates for the top left of the object
        y = self.py
        self.py += ol
        # Compute maximum distance from this wall for the starting point of the next
        # Once this wall is full
        if ow > self.maxd:
            self.maxd = ow
        return (self.w-2*ow, y)  # FIXME: without *2, objects start in the wall.
    def __adds(self, obj, ow, ol):
        """Tries to add the object along the south side"""
        if obj.orientationVector is not None:
            print "Added oven to south side"
            # Position the object as per its orientation vector
            # We don't need to worry about the z-axis, just examine the x and y axes
            # We want the orientation vector to point north at the end of this branch
            if obj.orientationVector[0] == 1: # Orientation vector points east
                obj.rotateAlongX(270) # Now it points north, away from the wall
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                obj.rotateAlongX(90) # Now it points north
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                obj.rotateAlongX(0) # Don't need to change it
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                obj.rotateAlongX(180) # Now it points north
        if ol > ow and obj.orientationVector is None:
            # undo previous change
            obj.rotateAlongX(-90)
            t = ow; ow = ol; ol = t
        if self.px-ow < 0:
            # No more room on this side, prepare coordinates for next wall
            self.side += 1
            self.py = self.h-self.maxd
            return self.__addw(obj, ow, ol)
        # Calculate the 2D coordinates for the top left of the object
        x = self.px
        self.px -= ow
        # Compute maximum distance from this wall for the starting point of the next
        # Once this wall is full
        if ol > self.maxd:
            self.maxd = ol
        return (x-ow, self.h-ol)
    def __addw(self, obj, ow, ol):
        """Tries to add the object along the west side"""
        if obj.orientationVector is not None:
            print "Added oven to west side"
            # Position the object as per its orientation vector
            # We don't need to worry about the z-axis, just examine the x and y axes
            # We want the orientation vector to point east at the end of this branch
            if obj.orientationVector[0] == 1: # Orientation vector points east
                obj.rotateAlongX(0) # Don't need to change it
            elif obj.orientationVector[0] == -1: # Orientation vector points west
                obj.rotateAlongX(180) # Now it points east
            elif obj.orientationVector[1] == 1: # Orientation vector points north
                obj.rotateAlongX(90) # Now it points east
            elif obj.orientationVector[1] == -1: # Orientation vector points south
                obj.rotateAlongX(270) # Now it points east
        # if length > width, rotate object so longest dimension is against wall.
        if ow > ol and obj.orientationVector is None:
            obj.rotateAlongX(90)
            t = ow; ow = ol; ol = t
        if self.py-ol < 0:
            # No more room on this side, room is full
            self.side += 1
            LayoutManager.remove(self, obj)
            return
        # Calculate the 2D coordinates for the top left of the object
        y = self.py
        self.py -= ol
        return (0, y-ol)


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
        ow = obj.getWidth()+self.padw
        ol = obj.getLength()+self.padh
        if self.px+ow > self.w:
            self.py += self.maxh
            self.px = 0
            self.maxh = 0
            if self.py+ol > self.h:
                return None
        x = self.px
        self.px += ow
        if ol > self.maxh:
            self.maxh = ol
        return (x-(self.w-ow)/2.0, self.py-(self.h-ol)/2.0, self.z)


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
