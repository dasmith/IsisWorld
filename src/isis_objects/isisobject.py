from pandac.PandaModules import *
#from pandac.PandaModules import NodePath, Vec3
from layout_manager import *
from ..physics.panda.manager import *

# Object class definitions defining methods inherent to each object type


def setupPhysics(self, model, collisionGeom='sphere'):
    # ensure all existing collision masks are off
    model.setCollideMask(BitMask32.allOff())
    
    # possible optimization step?
    # model.flattenLight()
    # see if the collider geometry is defined in the model
    try:
        collideGeom = model.find("**/collider")
    except:
        return # TODO
        # if it isn't, approximate the geometry as a sphere or a box
        bounds, offset = getOrientedBoundingBox(model)
        if collisionGeom == 'box':
            pass
            # TODO: use bounds to define an CollisionBox (?)
        else: # sphere
            radius = bounds[0]/2.0

        # other objects and agents can collide INTO it
        colliderGeom.node().setToCollideMask(AGENTMASK|OBJECTMASK)
        # it can collide into other objects and the floor.
        colliderGeom.node().setFromCollideMask(AGENTMASK|OBJECTMASK)

   
    # add this to the base collider, accessible through DirectStart
    base.cTrav.addCollider(colliderGeom, collisionHandler)

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

        # setup gravity pointer
        raygeometry = CollisionRay(0, 0, 2, 0, 0, -1)
        avatarRay = self.attachNewNode(CollisionNode('avatarRay'))
        avatarRay.node().addSolid(raygeometry)
# let's mask our floor FROM collider
        avatarRay.node().setFromCollideMask(FLOORMASK|OBJMASK)
        avatarRay.node().setIntoCollideMask(BitMask32.allOff())
        base.cFloor.addCollider(avatarRay,self)
        base.cTrav.addCollider(avatarRay,base.cFloor)

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
