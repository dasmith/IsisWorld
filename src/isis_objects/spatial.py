from pandac.PandaModules import *
#from pandac.PandaModules import Vec3, BitMask32 
from ..physics.panda.manager import *

OBJFLOOR = BitMask32.bit(21)
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
        self.setCollideMask(OBJMASK)
        # allow the object iself to have a into collide mask
        # FIXME: is this slowing the show down a lot?
        # setup gravity pointer
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()
        cRay = CollisionRay(center[0],center[1],center[2]-((lcorner[2]-center[2])/2.5), 0.0, 0.0, -1.0)
        cRayNode = CollisionNode('object')
        cRayNode.addSolid(cRay)
        cRayNode.setFromCollideMask(FLOORMASK|OBJFLOOR)
        cRayNode.setIntoCollideMask(BitMask32.bit(0))
        self.cRayNodePath = self.nodePath.attachNewNode(cRayNode)
        # add colliders
        #self.cRayNodePath.show()
        self.physicsManager.cFloor.addCollider(self.cRayNodePath, self.nodePath)
        base.cTrav.addCollider(self.cRayNodePath, self.physicsManager.cFloor)
        print "Adding Ray to %s" % self.name
        # TODO see if the collider geometry is defined in the model
        # ie. find it in the egg file:  cNodePath = model.find("**/collider")
        lcorner, ucorner =self.activeModel.getTightBounds()
        cFloorNode = CollisionNode('object')
        left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
        left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
        right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
        right_back = ucorner
        cFloorGeom = CollisionPolygon(left_front, right_front, right_back, left_back)
        cFloorNode.addSolid(cFloorGeom)
        cFloorNode.setFromCollideMask(FLOORMASK)
        cFloorNode.setIntoCollideMask(OBJFLOOR|FLOORMASK)
        # setup up collider for floor
        cFloorGeomNodePath = self.nodePath.attachNewNode(cFloorNode)
        self.physicsManager.cFloor.addCollider(cFloorGeomNodePath, self.nodePath)
        base.cTrav.addCollider(cFloorGeomNodePath, self.physicsManager.cFloor)
        print "Setup colliders for ", self.name
        return

        # setup wall collider 
        cWallNode = CollisionNode('object')
        bounds, offset = getOrientedBoundedBox(self.activeModel)
        radius = bounds[0]/2.0
        cGeom = CollisionSphere(0.0, 0.0, 0.0, radius)
        #cGeom = CollisionBox(lcorner, ucorner)
        cGeom.setTangible(0)
        cWallNode.addSolid(cGeom)
        # objects (ray) and agents can collide INTO it
        cWallNode.setIntoCollideMask(OBJMASK | AGENTMASK)
        cWallNode.setFromCollideMask(OBJMASK | AGENTMASK)
        # attach to current node path
        cWallNodePath = self.nodePath.attachNewNode(cWallNode)
        self.physicsManager.cWall.addCollider(cWallNodePath, self.nodePath)
        base.cTrav.addCollider(cWallNodePath, self.physicsManager.cWall)


class Surface(IsisSpatial):
    def __init__(self):
        self.surfaceContacts = []

    def _setupPhysics(self):
        """ Creates a surface collision geometry on the top of the object"""
        # find the surface of the model                    
        cNode = CollisionNode('object')
        left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
        left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
        right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
        right_back = ucorner
        # and make a Collision Polygon (ordering important)
        cGeom = CollisionPolygon(left_front, right_front, right_back, left_back)
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
        print "Setup surface", self.name
        super(Surface,self)._setupPhysics()
        # wall traversing collision objects

    def enterSurface(self,fromObj,toObject):
        print "Added to surface contacts", toObject
    
    def exitSurface(self,fromObj,toObject):
        print "Removed item from surface contacts", toObject


class Container(IsisSpatial):

    def _setupPhysics(self,collisionGeom='box'):
        cNode = CollisionNode('container')
        lcorner, ucorner =self.activeModel.getTightBounds()
        center = self.activeModel.getBounds().getCenter()
        if collisionGeom == 'sphere':
            # set up a collision sphere       
            bounds, offset = getOrientedBoundedBox(self.activeModel)
            radius = bounds[0]/2.0
            cGeom = CollisionSphere(0.0, 0.0, 0.0, radius)
        elif collisionGeom == 'box':
            cGeom = CollisionBox(lcorner, ucorner)
        # set so that is just considered a sensor.
        cGeom.setTangible(0)
        cNode.addSolid(cGeom)

        #cFloorGeom = CollisionBox(lcorner,ucorner)
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

