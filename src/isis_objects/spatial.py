from pandac.PandaModules import *
#from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *

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

OBJFLOOR = BitMask32.bit(21)

class IsisSpatial(object):
    """ This class is called _after_ IsisVisual is called and it, and its children classes
    are responsible for maintaining the spatial, geometric and physical properties of the 
    objects in IsisWorld."""

    def __init__(self,*args,**kwargs):
        # Flag to limit setup to once per object
        self.__setup = False

        # First, make sure IsisVisual was called
        if not hasattr(self,'models'):
            raise "Error: IsisVisual needs to be instantiated before IsisSpatial for %s" % self.name

        self.weight = None
        self.containerItems = []
        self.isOpen = False
        if 'density' in kwargs:
            self.density = kwargs['density']
        else:
            self.density = 1

        self._neetToRecalculateSpatialProperties = True

    def _destroyPhysics(self):
        pass
    
    def setup(self,collisionGeom='box'):
        if self.__setup:
            return
        # ensure all existing collision masks are off
        self.setCollideMask(BitMask32.allOff())
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()
        # setup ray for staying on the ground 
        cRay = CollisionRay(center[0],center[1],center[2]-((lcorner[2]-center[2])/2.5), 0.0, 0.0, -1.0)
        self.floorRayNP = CollisionNode('object')
        self.floorRayNP.addSolid(cRay)
        self.floorRayGeomNP = self.nodePath.attachNewNode(self.floorRayNP)
        print "Adding Ray to %s" % self.name
        self.topSurfaceNP = CollisionNode('object')
        left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
        left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
        right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
        right_back = ucorner
        cFloorGeom = CollisionPolygon(left_front, right_front, right_back, left_back)
        self.topSurfaceNP.addSolid(cFloorGeom)
        self.floorGeomNP = self.nodePath.attachNewNode(self.topSurfaceNP)
        print "Setup colliders for ", self.name

        # setup wall collider 
        self.fullBoxNP = CollisionNode('object')
        bounds, offset = getOrientedBoundedBox(self.activeModel)
        radius = bounds[0]/2.0
        #cGeom = CollisionSphere(0.0, 0.0, 0.0, radius)
        cGeom = CollisionBox(lcorner, ucorner)
        cGeom.setTangible(0)
        self.fullBoxNP.addSolid(cGeom)
        self.wallGeomNP = self.nodePath.attachNewNode(self.fullBoxNP)
        IsisSpatial.enableCollisions(self)
        self.wallGeomNP.show()
        self.physicsManager.cFloor.addCollider(self.floorRayGeomNP, self.nodePath)
        base.cTrav.addCollider(self.floorRayGeomNP, self.physicsManager.cFloor)
        self.physicsManager.cFloor.addCollider(self.floorGeomNP, self.nodePath)
        base.cTrav.addCollider(self.floorGeomNP, self.physicsManager.cFloor)
        self.physicsManager.cWall.addCollider(self.wallGeomNP, self.nodePath)
        base.cTrav.addCollider(self.wallGeomNP, self.physicsManager.cWall)


    def enableCollisions(self):
        self.floorRayNP.setFromCollideMask(FLOORMASK|OBJFLOOR)
        self.floorRayNP.setIntoCollideMask(BitMask32.bit(0))
        self.topSurfaceNP.setFromCollideMask(FLOORMASK)
        self.topSurfaceNP.setIntoCollideMask(OBJFLOOR|FLOORMASK)
        self.fullBoxNP.setIntoCollideMask(OBJMASK | AGENTMASK)
        self.fullBoxNP.setFromCollideMask(OBJMASK | AGENTMASK)

    def disableCollisions(self):
        print "Removing Collisions - Base"
        self.floorRayNP.setFromCollideMask(BitMask32.allOff())
        self.floorRayNP.setIntoCollideMask(BitMask32.allOff())
        self.topSurfaceNP.setFromCollideMask(BitMask32.allOff())
        self.topSurfaceNP.setIntoCollideMask(BitMask32.allOff())
        self.fullBoxNP.setIntoCollideMask(BitMask32.allOff())
        self.fullBoxNP.setFromCollideMask(BitMask32.allOff())

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
    def __init__(self, *args, **kwargs):
        self.surfaceContacts = []
        super(Surface,self).__init__(args,kwargs)
        self.__setup = True
        self.on_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())

    def setup(self):
        if self.__setup:
            return
        self.topSurfaceNP.setTag('surface','asurface')
        """ Creates a surface collision geometry on the top of the object"""
        super(Surface,self).setup()
        self.__setup = True


    def enableCollisions(self):
        return

    def disableCollisions(self):
        print "Removing Collision - Surface"
        super(Surface,self).disableCollisions()

    def enterSurface(self,fromObj,toObject):
        print "Added to surface contacts", toObject
    
    def exitSurface(self,fromObj,toObject):
        print "Removed item from surface contacts", toObject

    def putOn(self, obj):
        # TODO: requires that object has an exposed surface
        obj.reparentTo(self)
        obj.setPos(self.on_layout.add(obj))


class Container(IsisSpatial):
    def __init__(self, *args, **kwargs):
        # Flag to limit setup to once per object
        self.__setup = False
        self.surfaceContacts = []
        super(Container,self).__init__(args,kwargs)
        #TO-DO: Change this to something more fitting for a container
        self.in_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())

    def setup(self,collisionGeom='box'):
        if self.__setup:
            return
        # call base class
        IsisSpatial.setup(self)
        self.fullBoxNP.setTag('container','acontainer')
        self.enableCollisions()
        self.__setup = True

    
    def enableCollisions(self):
        pass

    def disableCollisions(self):
        super(Container,self).disableCollisions()

    def enterContainer(self,fromObj,toObject):
        print "Entering container", toObject
        assert toObject == self, "Error: cannot put into self"
        if fromObj not in self.containerItems:
            self.containerItems.append(fromObj)

    def leaveContainer(self,fromObj,toObject):
        assert toObject == self, "Error: cannot remove from another container"
        if fromObj in self.containerItems:
            self.containerItems.remove(toObject)

    def isEmpty(self):
        return len(self.containerItems) == 0

    def open(self):
        if self.isOpen:
            # container already open 
            return True

    def putIn(self, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        obj.reparentTo(self)
        obj.setPos(self.in_layout.add(obj))

