from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
from ..physics.panda.manager import *

# Object class definitions defining methods inherent to each object type




class IsisObject(NodePath):
    """ IsisObject is the base class for all visible objects in IsisWorld, other
    than sky, house, ground and agents """

    def  __init__(self, name, model, density, physicsManager, initialPos, offsetVec=Vec3(0,0,0)): 
        # setup the name of the object
        self.name = "IsisObject/"+name+"+"+str(id(self))
        NodePath.__init__(self, self.name)
        self.offsetVec = Vec3(0,0,0)#offsetVec
        self.model = model
        self.model.setPos(initialPos+offsetVec)
        self.model.reparentTo(self)
        self.physicsManager = physicsManager
        self.density = density 
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
        # private flag to lazily recompute properties when necessary
        self._needToRecalculateScalingProperties = True 
        #PhysicsObjectController.__init__(self, physicsManager,density=density,geomType='box',dynamic=False)
        
        # initialize dummy variables
        self.width = None
        self.length = None
        self.height = None
        self.weight = None

        self.on_layout = None
        self.in_layout = None

        # organize environments for internal layouts
        self.on_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())
        self.in_layout = self.on_layout
        # adds a pickable tag to allow an agent to view this object
        self.setTag('pickable', 'true')

        # setup up collision physics around the model passed as first arg
        self._setupPhysics(self.model)
        
    def _setupPhysics(self, model, collisionGeom='surface'):
        # ensure all existing collision masks are off
        self.setCollideMask(BitMask32.allOff())
        # allow the object iself to have a into collide mask
        # FIXME: is this slowing the show down a lot?
        self.setCollideMask(OBJMASK)
        # when models are scaled down dramatically (e.g < 1% of original size), Panda3D represents
        # the geometry non-uniformly, which means scaling occurs every render step and collision
        # handling is buggy.  flattenLight()  circumvents this.
        model.flattenLight()
        # setup gravity pointer
        cRay = CollisionRay()
        # set origin of ray slightly below obj
        lcorner, ucorner =model.getTightBounds()
        center = model.getBounds().getCenter()
        cRay.setOrigin(center[0],center[1],lcorner[2])
        # face downward
        cRay.setDirection(0,0,-1)
        
        cRayNode = self.attachNewNode(CollisionNode('avatarRay'))
        cRayNode.node().addSolid(cRay)
        # nothing can collide INTO the ray
        cRayNode.node().setIntoCollideMask(BitMask32.allOff())
        # but the ray can colide INTO the FLOOR and other objects
        cRayNode.node().setFromCollideMask(FLOORMASK | OBJMASK)
        # debug: show this node
        cRayNode.show()
        # TODO see if the collider geometry is defined in the model
        # ie. find it in the egg file:  cNodePath = model.find("**/collider")
        cNode = CollisionNode('object')
        if collisionGeom == 'surface': 
            # find the surface of the model                    
            lcorner, ucorner =model.getTightBounds()
            center = model.getBounds().getCenter()
            left_front = Vec3(lcorner[0], lcorner[1], ucorner[2])
            left_back = Vec3(lcorner[0], ucorner[1], ucorner[2])
            right_front = Vec3(ucorner[0], lcorner[1], ucorner[2])
            right_back = ucorner
            # and make a Collision Polygon (ordering important)
            cGeom = CollisionPolygon(right_back, left_back, left_front, right_front)
        elif collisionGeom == 'sphere':
            # set up a collision sphere       
            bounds, offset = getOrientedBoundedBox(model)
            radius = bounds[0]/2.0
            cGeom = CollisionSphere(0.0, 0.0, 0.0, radius)
        # set so that is just considered a sensor.
        cGeom.setTangible(0)
        cNode.addSolid(cGeom)

        # objects (ray) and agents can collide INTO it
        cNode.setIntoCollideMask(OBJMASK | AGENTMASK)
        # but this surface/sphere cannot collide INTO other objects
        cNode.setFromCollideMask(BitMask32.allOff())
        # attach to current node path
        cNodePath = self.attachNewNode(cNode)
        cNodePath.show()
        
        # register RayNode in GravityHandler and Traverser
        base.cFloor.addCollider(cRayNode, self)
        base.cTrav.addCollider(cRayNode, base.cFloor)

        # add this to the base collider, accessible through DirectStart
        base.cTrav.addCollider(cNodePath, base.cEvent)

    def rescaleModel(self,scale):
        """ Changes the model's dimensions to a given scale"""
        self.model.setScale(scale)
        self._needToRecalculateScalingProperties = True
  
    def getWeight(self):
        """ Returns the weight of an object, based on its bounding box dimensions
        and its density """
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.weight
    
    def getLength(self):
        """ Returns the length of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.length

    def getWidth(self):
        """ Returns the width of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.width
    
    def getHeight(self):
        """ Returns the height of an object, based on its bounding box"""
        if self._needToRecalculateScalingProperties: self._recalculateScalingProperties()
        return self.height

    def getDensity(self):
        """ Returns the density of the object"""
        return self.density

    def setDensity(self, density):
        """ Sets the density of the object """
        self.density = density
        self._needToRecalculateScalingProperties = True

    def take(self, parent):
        """ Allows Ralph to pick up a given object """
        if self.weight < 5000:
            self.reparentTo(parent)
            self.heldBy = parent
    def drop(self):
        """ Clears the heldBy variable """
        self.heldBy = None

    def putOn(self, obj):
        # TODO: requires that object has an exposed surface
        obj.reparentTo(self)
        obj.setPos(self.on_layout.add(obj))

    def putIn(self, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        obj.reparentTo(self)
        obj.setPos(self.in_layout.add(obj))

    def attachAsPart(self, object):
        """ Attaches another objet to a parent object's exposed joins """
        pass

    def getParts(self):
        """ Returns a list of the labeled sub-node paths that are parts of the model"""
        pass
    
    def destroyObject(self):
        # TODO destroy all sub object
        # make some snazzy viz using "explode" ODE method
        pass

    def _recalculateScalingProperties(self):
        """ Internal method for recomputing properties, lazily issued"""
        p1, p2 = self.getTightBounds()
        self.width = abs(p2.getX()-p1.getX())
        self.length = abs(p2.getY()-p1.getY())
        self.height = abs(p2.getZ()-p1.getZ())
        self.weight = self.density*self.width*self.length*self.height
        # reset physical model
        #print "destroying physics for", self.name
        #self.destroy()
        #PhysicsObjectController.__init__(self,self.physicsManager,self.density)
        self._needToRecalculateScalingProperties = False

    def call(self, agent, action, object = None):
        try:
            return getattr(self, "action_"+action)(agent, object)
        except AttributeError:
            return None
        except:
            return None

class Dividable(IsisObject):
    def __init__(self, name, model, density, pieceGenerator, physicsManager, initialPos, offsetVec=Vec3(0,0,0)):
        IsisObject.__init__(self, name, model, density, physicsManager, initialPos, offsetVec=Vec3(0, 0, 0))
        self.piece = pieceGenerator

    def action_divide(self, agent, object):
        if object != None and isinstance(object, SharpObject):
            if agent.right_hand_holding_object:
                agent.control__put_object_in_empty_right_hand(self.piece.generate_instance(self.physicsManager))
                return true
            elif agent.left_hand_holding_object:
                agent.control__put_object_in_empty_right_hand(self.piece.generate_instance(self.physicsManager))
                return true
        return false

class SharpObject(IsisObject):
    def __init__(self, name, model, density, physicsManager, initialPos, offsetVec=Vec3(0,0,0)):
        IsisObject.__init__(self, name, model, density, physicsManager, initialPos, offsetVec=Vec3(0, 0, 0))
