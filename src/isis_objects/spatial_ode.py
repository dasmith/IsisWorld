from pandac.PandaModules import Vec3, BitMask32 
from ..physics.ode.odeWorldManager import *
from ..physics.ode.pickables import *
from layout_manager import *


class SpatialContainer(object):
    priority = 19
    def __init__(self):
        self.containerItems = []
    
    def setup(self):
        self.in_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())
        self.collisionCallback = self.enterContainer
        if hasattr(self,'geom'):
            self.setCatColBits("container")

    def enterContainer(self,entry,fromObj,toObj):
        if fromObj != toObj:
            print "Entering container", self.name, fromObj, toObj
            if fromObj not in self.containerItems:
                self.containerItems.append(fromObj)

    def leaveContainer(self,entry,fromObj,toObj):
        print "Removing %s from container", fromObj
        if fromObj in self.containerItems:
            self.containerItems.remove(fromObj)

    def isEmpty(self):
        return len(self.containerItems) == 0

    def update(self,x=None):
        print "Update method called for", self.name, x

    def action__put_in(self, agent, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        print "IN LAYOUT FUNCT", self.in_layout
        pos = self.in_layout.add(obj)
        print "ADDING", obj, "to", self.name
        if pos:
            if agent and agent.is_holding(obj.name):
                if agent.left_hand_holding_object == obj:
                    agent.control__drop_from_left_hand()
                elif agent.right_hand_holding_object == obj:
                    agent.control__drop_from_right_hand()
            obj.disable()
            obj.reparentTo(self)
            pos = (pos[0]+self.getGeomPos()[0]+obj.offset_vector[0],
                   pos[1]+self.getGeomPos()[1]+obj.offset_vector[1],
                   self.getHeight()/2+obj.offset_vector[2])
            obj.setPosition(pos)
            obj.setRotation(obj.offset_vector[3:])
            obj.set_layout(self.in_layout)
            if not "toaster" in self.name:
                obj.enable() # let the object fall to the floor
            return "success"
        return "container is full"


class SpatialSurface(object):
    priority = 10

    def __init__(self):
        self.surfaceContacts = []
        
    def setup(self):
        area = (self.getWidth(), self.getLength())
        # -x moves to the right
        # y moves toward the camera
        
        self.on_layout =  SlotLayout([(1.5, 0.6, 0), (1.0, 0.6, 0.0), (0.5, 0.6, 0.0), (0, 0.6, 0.0)])
        
        #HorizontalGridSlotLayout(area, self.getHeight(), 2,2)
        #SlotLayout([(.3, .1, .2), (.3, -.1, .2)])

    def action__put_on(self, agent, obj):
        print " CALL TO action__put_on", agent, obj

        if agent and agent.is_holding(obj.name):
            #agent.is_holding(obj.name):
            if agent.left_hand_holding_object == obj:
                agent.control__drop_from_left_hand(throw_object=False)
            elif agent.right_hand_holding_object == obj:
                agent.control__drop_from_right_hand(throw_object=False)
            obj.disable()
            obj.rotateAlongX(1)
        #obj.setGeomQuat(self.getQuat())
        pos = self.on_layout.add(obj)
        print "POS result", pos
        if pos:
            obj.disable()
            obj.reparentTo(self)
            pos = (pos[0]+self.getGeomPos()[0]+obj.offset_vector[0],
                   pos[1]+self.getGeomPos()[1]+obj.offset_vector[1],
                   self.getHeight()+obj.offset_vector[2])
            obj.setPosition(pos)
            obj.setRotation(obj.offset_vector[3:])
            obj.set_layout(self.on_layout)
     
            obj.enable()
            #obj.synchPosQuatToNode()
            return "success"
        return "error: Surface is full"


class SpatialPickable(pickableObject):
    priority = 3

    def __init__(self):
        if not hasattr(self,'category'):
            self.category = "static"
        
        pickableObject.__init__(self,"box",0.5)
        self.geomSize = (1.0,1.0,1.0)
        self.friction = 1.0

        #self.mapObjects["kinematics"].append(self)
    
    def setup(self):
        
        self.physics.addObjectToWorld(self,'dynamics')
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        print "Creating:", self.name
        self.setupGeomAndPhysics(self.physics, pos, quat)
        self.showCCD = False


class SpatialPickableBox(pickableObject):

    def __init__(self):
        # weight = 0.5
        pickableObject.__init__(self, "box", 0.5)
        self.friction = 1.0      
        self.showCCD = False

    def setup(self):
        self.geomSize =self.physics.extractSizeForBoxGeom(self.activeModel)
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        self.setupGeomAndPhysics(self.physics, pos, quat)
        self.physics.addObject(self)


class SpatialPickableContainer(pickableObject):
    #priority = 19
    def __init__(self):
        pickableObject.__init__(self, "box", 0.5)
        self.friction = 1.0      
        self.showCCD = False
        self.containerItems = []

    def setup(self):
        self.geomSize =self.physics.extractSizeForBoxGeom(self.activeModel)
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        self.setupGeomAndPhysics(self.physics, pos, quat)
        self.physics.addObject(self)
        self.in_layout = HorizontalGridLayout((self.getWidth(), self.getLength()), self.getHeight())
        #self.collisionCallback = None
        if hasattr(self,'geom'):
            self.setCatColBits("container")

    def action__put_in(self, agent, obj):
        # TODO: ensure that object can fit in other object
        #  1) internal volume is big enough, 2) vol - vol of other things in there
        print "IN LAYOUT FUNCT", self.in_layout
        pos = self.in_layout.add(obj)
        print "ADDING", obj, "to", self.name
        if pos:
            if agent and agent.is_holding(obj.name):
                if agent.left_hand_holding_object == obj:
                    agent.control__drop_from_left_hand()
                elif agent.right_hand_holding_object == obj:
                    agent.control__drop_from_right_hand()
            obj.disable()
            obj.reparentTo(self)
            pos = (pos[0]+self.getGeomPos()[0]+obj.offset_vector[0],
                   pos[1]+self.getGeomPos()[1]+obj.offset_vector[1],
                   pos[2]+self.getGeomPos()[2]+obj.offset_vector[2])
            obj.setPosition(pos)
            obj.setRotation(obj.offset_vector[3:])
            obj.set_layout(self.in_layout)
            # don't enable@
            #obj.enable() # let the object fall to the floor
            return "success"
        return "container is full"


class SpatialPickableBall(pickableObject):
    def __init__(self):
        pickableObject.__init__(self, "ball", 0.5)
        self.modelPath = "./graphics/models/ball.egg"
        self.shape = "sphere"
        self.showCCD = False
        self.friction = 3.0

    def setup(self):
        lcorner, ucorner =self.activeModel.getTightBounds()
        radius = min(ucorner[0]-lcorner[0],ucorner[1]-lcorner[1])/2.0
        self.geomSize = radius
        pos = self.activeModel.getPos(render)
        quat = self.activeModel.getQuat(render)
        self.setupGeomAndPhysics(self.physics, pos, quat)
        self.physics.addObject(self)

class SpatialRoom(staticObject):
    priority = 3
    def __init__(self):
        staticObject.__init__(self,self.physics)
        # Flag to limit setup to once per object
        self.containerItems = []
        self.in_layout = RoomLayout((self.getWidth(), self.getLength()), 0)

    def setup(self):
        self.setTrimeshGeom(self.activeModel)
        self.setCatColBits("environment")
        self.physics.addObject(self)
    
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
        print "Putting %s in room %s" % (obj,self)
        #obj.disable() # turn off physics
        if pos:
            if agent and agent.is_holding(obj.name):
                if agent.left_hand_holding_object == obj:
                    agent.control__drop_from_left_hand()
                elif agent.right_hand_holding_object == obj:
                    agent.control__drop_from_right_hand()
            obj.reparentTo(self)
            obj.setPosition(pos)
            obj.set_layout(self.in_layout)
            return "success"
        return "container is full"


class SpatialStaticBox(staticObject):
    priority = 3

    def __init__(self):
        staticObject.__init__(self, self.physics)

    def setup(self):
        self.setBoxGeomFromNodePath(self.activeModel)
        #self.state = "vacant"
        self.physics.addObject(self)

class SpatialStaticTriMesh(staticObject):
    priority = 5
    def __init__(self):
        staticObject.__init__(self,self.physics)
    
    def setup(self):
        self.setTrimeshGeom(self.activeModel)
        self.physics.addObject(self)

