from pandac.PandaModules import *
#from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *

class IsisSpatial(object):
    """ This class is called _after_ IsisVisual is called and it, and its children classes
    are responsible for maintaining the spatial, geometric and physical properties of the 
    objects in IsisWorld."""

    def __init__(self,density=1):
        # First, make sure IsisVisual was called
        if not hasattr(self,'models'):
            raise "Error: IsisVisual needs to be instantiated before IsisSpatial for %s" % self.name

        self.containerItems = []
        self.isOpen = False
        self.density = 1
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

    def _destroyPhysics(self):
        pass
    
    def _setupPhysics(self,collisionGeom='box'):
        # ensure all existing collision masks are off
        self.setCollideMask(BitMask32.allOff())
        # allow the object iself to have a into collide mask
        # FIXME: is this slowing the show down a lot?
        # setup gravity pointer
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()
        cRay = CollisionRay(center[0],center[1],center[2], 0.0, 0.0, -1.0)
        cRayNode = CollisionNode('object')
        cRayNode.addSolid(cRay)
        cRayNode.setFromCollideMask(FLOORMASK|OBJMASK)
        cRayNode.setIntoCollideMask(BitMask32.bit(0))
        self.cRayNodePath = self.nodePath.attachNewNode(cRayNode)
        # add colliders
        self.cRayNodePath.show()
        self.physicsManager.cFloor.addCollider(self.cRayNodePath, self.nodePath)
        base.cTrav.addCollider(self.cRayNodePath, self.physicsManager.cFloor)
        print "Adding Ray to %s" % self.name
        # TODO see if the collider geometry is defined in the model
        # ie. find it in the egg file:  cNodePath = model.find("**/collider")
        lcorner, ucorner =self.activeModel.getTightBounds()
        cWallGeom = CollisionBox(lcorner,ucorner)
        cWallNode = CollisionNode('object-wall')
        left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
        left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
        right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
        right_back = ucorner
        # and make a Collision Polygon (ordering important)
        cWallGeom = CollisionPolygon(left_front, right_front, right_back, left_back)
        cWallNode.addSolid(cWallGeom)
        cWallNode.setFromCollideMask(FLOORMASK)
        cWallNode.setIntoCollideMask(OBJMASK|BitMask32.allOff())
        cWallGeomNodePath = self.nodePath.attachNewNode(cWallNode)
        #cWallGeomNodePath.show()
        #`self.physicsManager.cWall.addCollider(cWallGeomNodePath, self.nodePath)
        #base.cTrav.addCollider(cWallGeomNodePath, self.physicsManager.cWall)
        # and for the floor!
        self.physicsManager.cFloor.addCollider(cWallGeomNodePath, self.nodePath)
        base.cTrav.addCollider(cWallGeomNodePath, self.physicsManager.cFloor)


class Surface(IsisSpatial):

    def enterSurface(self,fromObj,toObject):
        pass

class Container(IsisSpatial):

    def _setupPhysics(self,collisionGeom='box'):
        cNode = CollisionNode('object')
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()
        if collisionGeom == 'surface': 
            # find the surface of the model                    
            left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
            left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
            right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
            right_back = ucorner
            # and make a Collision Polygon (ordering important)
            cGeom = CollisionPolygon(left_front, right_front, right_back, left_back)
        elif collisionGeom == 'sphere':
            # set up a collision sphere       
            bounds, offset = getOrientedBoundedBox(self.activeModel)
            radius = bounds[0]/2.0
            cGeom = CollisionSphere(0.0, 0.0, 0.0, radius)
        elif collisionGeom == 'box':
            cGeom = CollisionBox(lcorner, ucorner)
        # set so that is just considered a sensor.
        cGeom.setTangible(0)
        cNode.addSolid(cGeom)

        # but this surface/sphere cannot collide INTO other objects
        cNode.setIntoCollideMask(OBJMASK | AGENTMASK)
        # objects (ray) and agents can collide INTO it
        cNode.setFromCollideMask(OBJMASK | AGENTMASK)
        # attach to current node path
        cNodePath = self.nodePath.attachNewNode(cNode)
        #cNodePath.show()
        # add this to the base collider, accessible through DirectStart
        base.cTrav.addCollider(cNodePath, base.cEvent)
        print "Setup container", self.name
        super(Container,self)._setupPhysics()
        # wall traversing collision objects

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

