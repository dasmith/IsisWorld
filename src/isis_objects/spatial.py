from pandac.PandaModules import *
#from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *

from direct.controls.ControlManager import CollisionHandlerRayStart
from layout_manager import *

""" Material	Density (kg/m^3)
    Balsa wood	120
    Brick	2000
    Copper	8900
    Cork	250
    Diamond	3300
    Glass	2500
    Gold	19300
    Iron	7900
    Lead	11300
    Styrofoam 100
"""

class IsisSpatial(object):
    """ This class is called _after_ IsisVisual is called and it, and its children classes
    are responsible for maintaining the spatial, geometric and physical properties of the 
    objects in IsisWorld."""

    def __init__(self):
        # Flag to limit setup to once per object
        self.__setup = False

        # First, make sure IsisVisual was called
        if not hasattr(self,'models'):
            raise "Error: IsisVisual needs to be instantiated before IsisSpatial for %s" % self.name

        self.weight = None
        #self.containerItems = []
        if not hasattr(self,'density'):
            self.density = 1
        if not hasattr(self,'collisionGeom'):
            self.collisionGeom = 'box'

        self._neetToRecalculateSpatialProperties = True

    def _destroyPhysics(self):
        pass
    
    def setup(self):
        """ Initializes all the collision geometries for the top surface (gravity) and
        geometric reigon for wall and agent collisions, as well as aribtrary collide
        callbacks.   Must be called after self.activeModel is defined."""
        if self.__setup:
            return
        print "Spatial setup called for ", self.name
        # ensure all existing collision masks are off
        self.setCollideMask(BitMask32.allOff())
        # allow model to be picked (visual correspondance with Ralph's vision methods)
        self.activeModel.setCollideMask(OBJPICK)
        # compute model properties
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()
        #ucorner[2] += 0.2
        left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
        left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
        right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
        right_back = ucorner
        bounds, offset = getOrientedBoundedBox(self.activeModel)
        radius = min(ucorner[0]-lcorner[0],ucorner[1]-lcorner[1])/2.0

        # set up the floor ray collision node
        self.floorRay = CollisionRay() 
        self.floorRay.setOrigin(center[0],center[1],lcorner[2]-0.1) 
        self.floorRay.setDirection(0,0,-1)
        self.floorRayCN = CollisionNode('floorRayCollider-%s' % self.name) 
        self.floorRayCN.addSolid(self.floorRay)
        self.floorRayNP =self.attachNewNode(self.floorRayCN)
        #self.floorRayNP.show()
        self.physics.cFloor.addCollider(self.floorRayNP, self)
        base.cTrav.addCollider(self.floorRayNP, self.physics.cFloor)

        # construct geometry of top surface
        self.topSurfaceCN = CollisionNode('topSurfaceCollidee-%s' % self.name)
        self.topSurfaceCN.addSolid(CollisionPolygon(left_front, right_front, right_back, left_back))
        self.topSurfaceNP = self.attachNewNode(self.topSurfaceCN)
        # setup wall (horizontal) collider 
        self.fullBoxCN = CollisionNode('object')
        cGeom = CollisionBox(lcorner, ucorner)
        cGeom.setTangible(1)
        self.fullBoxNP = self.attachNewNode(self.fullBoxCN)
        self.fullBoxCN.addSolid(cGeom)
        #self.fullBoxNP.show()

        self.enableCollisions()

    def enableCollisions(self):
        self.topSurfaceCN.setFromCollideMask(BitMask32.allOff())
        self.topSurfaceCN.setIntoCollideMask(OBJFLOOR)
        self.floorRayCN.setFromCollideMask(OBJFLOOR|OBJPICK) 
        self.floorRayCN.setIntoCollideMask(BitMask32.allOff())
        self.fullBoxCN.setFromCollideMask(OBJMASK)
        self.fullBoxCN.setIntoCollideMask(OBJMASK)

    def disableCollisions(self):
        #self.floorRayCN.setFromCollideMask(BitMask32.allOff())
        #self.floorRayCN.setIntoCollideMask(BitMask32.allOff())
        self.topSurfaceCN.setFromCollideMask(BitMask32.allOff())
        self.topSurfaceCN.setIntoCollideMask(BitMask32.allOff())
        self.fullBoxCN.setIntoCollideMask(BitMask32.allOff())
        self.fullBoxCN.setFromCollideMask(BitMask32.allOff())

    def getWeight(self):
        """ Returns the weight of an object, based on its bounding box dimensions
        and its density """
        if self._needToRecalculateSpatialProperties: self._recalculateSpatialProperties()
        return self.weight

    def getDensity(self):
        """ Returns the density of the object"""
        return self.density

    def setDensity(self, density):
        """ Sets the density of the object """
        self.density = density
        self._needToRecalculateSpatialProperties = True

    def _recalculateSpatialProperties(self):
        """ Internal method for recomputing properties, lazily issued"""
        self.weight = self.density*self.width*self.length*self.height
        self._needToRecalculateSpatialProperties = False


class Surface(IsisSpatial):
    priority = 3
    def __init__(self):
        self.surfaceContacts = []
        IsisSpatial.__init__(self)
        self.__setup = False

    def setup(self):
        if self.__setup:
            return
        area = (self.getWidth(), self.getLength())
        self.on_layout = HorizontalGridSlotLayout(area, self.getHeight(), int(self.getWidth()),int(self.getLength()))
        # Creates a surface collision geometry on the top of the object
        self.topSurfaceNP.setTag('surface','asurface')

        IsisSpatial.setup(self)
        self.enableCollisions()
        self.__setup = True


    def enableCollisions(self):
        IsisSpatial.enableCollisions(self)

    def disableCollisions(self):
        print "Removing Collision - Surface"
        IsisSpatial.disableCollisions(self)

    def enterSurface(self,fromObj):
        print "Added to surface contacts", fromObj
    
    def exitSurface(self,fromObj):
        print "Removed item from surface contacts", fromObj

    def action__put_on(self, agent, obj):
        # TODO: requires that object has an exposed surface
        pos = self.on_layout.add(obj)
        if pos:
            if agent and agent.is_holding(obj.name):
                if agent.left_hand_holding_object == obj:
                    agent.control__drop_from_left_hand()
                elif agent.right_hand_holding_object == obj:
                    agent.control__drop_from_right_hand()
            obj.reparentTo(self)
            obj.setPos(pos)
            obj.setLayout(self.on_layout)
            return "success"
        return "Surface is full"




class Container(IsisSpatial):
    priority = 3
    def __init__(self):
        # Flag to limit setup to once per object
        self.__setup = False
        self.containerItems = []
        IsisSpatial.__init__(self)


    def setup(self):
        if self.__setup:
            return
        # call base class
        #TO-DO: Change this to something more fitting for a container
        self.in_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())

        IsisSpatial.setup(self)
        self.fullBoxNP.setTag('container','acontainer')
        self.enableCollisions()
        self.__setup = True
    
    def enableCollisions(self):
        IsisSpatial.enableCollisions(self)

    def disableCollisions(self):
        IsisSpatial.disableCollisions(self)

    def enterContainer(self,fromObj):
        print "Entering container", self.name
        if fromObj not in self.containerItems:

            self.containerItems.append(fromObj)

    def leaveContainer(self,fromObj):
        print "Removing %s from container", fromObj
        if fromObj in self.containerItems:
            self.containerItems.remove(fromObj)

    def isEmpty(self):
        return len(self.containerItems) == 0

    def action__put_in(self, agent, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        pos = self.in_layout.add(obj)
        if pos:
            if agent and agent.is_holding(obj.name):
                if agent.left_hand_holding_object == obj:
                    agent.control__drop_from_left_hand()
                elif agent.right_hand_holding_object == obj:
                    agent.control__drop_from_right_hand()
            obj.reparentTo(self)
            obj.disableCollisions()
            obj.setPos(pos)
            obj.setLayout(self.in_layout)
            return "success"
        return "container is full"

class Room(object):
    """ Room is like a container, but it does not inherit from the IsisSpatial methods,  so it needs to 
    implement its geometry (wall) collisions on its own.  Also, it doesn't have some of the specialized
    methods, like 'action__put_in' that Container objects do, because 'put item in room' should be 
    decomposed as a series of smaller tasks: grab object, enter room, drop object. """
    
    priority = 3
    def __init__(self):
        # Flag to limit setup to once per object
        self.__setup = False
        self.containerItems = []
        self.in_layout = RoomLayout((self.getWidth(), self.getLength()), 0)

    def setup(self):
        if self.__setup:
            return
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()

        left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
        left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
        right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
        right_back = ucorner
        bounds, offset = getOrientedBoundedBox(self.activeModel)
        radius = min(ucorner[0]-lcorner[0],ucorner[1]-lcorner[1])/2.0

        # setup wall (horizontal) collider 
        self.fullBoxCN = CollisionNode('room')
        cGeom = CollisionBox(lcorner, ucorner+Vec3(0,0,0.0))
        cGeom.setTangible(1)
        self.fullBoxNP = self.attachNewNode(self.fullBoxCN)
        base.cTrav.addCollider(self.fullBoxNP, base.cEvent)
        #TO-DO: Change this to something more fitting for a container

        self.fullBoxNP.setTag('container','acontainer')
        self.__setup = True

    def enableCollisions(self):
        self.fullBoxCN.setFromCollideMask(OBJMASK)
        self.fullBoxCN.setIntoCollideMask(OBJMASK|AGENTMASK)

    def disableCollisions(self):
        self.fullBoxCN.setFromCollideMask(BitMask32.allOff())
        self.fullBoxCN.setIntoCollideMask(BitMask32.allOff())

    def enterContainer(self,fromObj):
        print "Entering room", self.name
        if fromObj not in self.containerItems:
            self.containerItems.append(fromObj)

    def leaveContainer(self,fromObj):
        print "Removing %s from room %s" % (fromObj, self.name)
        if fromObj in self.containerItems:
            self.containerItems.remove(fromObj)

    def isEmpty(self):
        return len(self.containerItems) == 0

    def action__put_in(self, agent, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        pos = self.in_layout.add(obj)
        if pos:
            if agent and agent.is_holding(obj.name):
                if agent.left_hand_holding_object == obj:
                    agent.control__drop_from_left_hand()
                elif agent.right_hand_holding_object == obj:
                    agent.control__drop_from_right_hand()
            obj.reparentTo(self)
            obj.disableCollisions()
            obj.setPos(pos)
            obj.setLayout(self.in_layout)
            return "success"
        return "container is full"
