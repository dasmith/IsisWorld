import pdb
import math

from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

"""
This is a convenient way of handling the most tedious and powerful part of ODE
"""
bitMaskDict = {
    "generalKCC": (BitMask32(0b110), BitMask32(0b0)),
    "pickable": (BitMask32(0b1), BitMask32(0b11)),
    
    "wifiTrigger": (BitMask32(0b0), BitMask32(0b10)),
    "charTrigger": (BitMask32(0b100), BitMask32(0b10)),
    
    "environment": (BitMask32(0b10), BitMask32(0b111)),
    "aimRay": (BitMask32(0b0), BitMask32(0b011)),
    "kccEnvCheckerRay": (BitMask32(0b0), BitMask32(0b11)),
}

"""
The basic physical object in this framework. It represents static geometry
and is meant to be used for environment.

More complex objects inherit from this one.
"""
class physicalObject(object):
    def __init__(self, physics):
        self.physics = physics
        
        """
        Node Path, graphical representation for this object
        """
        if not hasattr(self,'activeModel'):
            self.activeModel = None
        """
        OdeGeom for collision detection
        """
        self.geom = None
        
        """
        In case of physicalObject and staticObject this will stay None,
        but it aids the world manager's readability to keep it here.
        """
        self.body = None
        
        """
        Shape visualization geom. Currently only Box can be visualized.
        """
        self.visualization = None
        
        """
        Object type for World Manager
        
        The possible values* are:
            - static
            - kinematic
            - dynamic (no distinction between ccd and no-ccd)
            - ray
            - trigger (note that previously there was an isTrigger variable)
            - ccd (ccd helper object)
            
        (* that's those my code understands by default,
        feel free to add more)
        """
        self.objectType = "static"
        
        self.pos = None
        self.quat = None
        
        """
        Name of the bit masks used for this object.
        """
        self.bitsName = ""
        
        """
        Whether to visualize this object ore not.
        """
        self.visualize = False
        
    def getGeom(self):
        return self.geom
    
    
    def disable(self):
        if self.geom: self.geom.disable()
        if self.body: self.body.disable()
        
    def enable(self):
        if self.geom: self.geom.enable()
        if self.body: self.body.enable()
    
    """
    Collision and Selection Callbacks, functionality previously
    implemented in the now removed OdeGeomData class.
    """
    def collisionCallback(self, *args):
        return
    
    def selectionCallback(self, *args):
        return
    
    """
    Set a custom geom (as in, not created by this class).
    """
    def setGeom(self, geom):
        self.geom = geom
        
    def getNodePath(self):
        return self.activeModel
        
    """
    Set the Node Path for this Object's rendering
    
    Model attribute can be a string, containing a path to the model's egg,
    or a nodepath.
    
    Parent indicates the new parent for this node.
    """
    def setNodePath(self, model, parent=None, scale=1.0, pos=None):
        """
        Load the model using it's name or wrap around a passed nodepath
        """
        if isinstance(model, basestring):
            self.activeModel = loader.loadModel(model)
        else:
            self.activeModel = model
        
        self.activeModel.setScale(scale)
        
        if pos:
            self.setGeomPos(pos)
        
        if parent is None:
            pass
        elif parent == "detach":
            self.activeModel.detachNode()
        else:
            self.activeModel.reparentTo(parent)
        
    def detachNode(self):
        self.activeModel.detachNode()
    
    def synchPosQuatToNode(self):
        if self.activeModel:
            self.geom.setPosition(self.activeModel.getPos(render))
            self.geom.setQuaternion(self.activeModel.getQuat(render))
    
    def setGeomPos(self, pos=None):
        if pos is None:
            pos = self.activeModel.getPos(render)
            self.geom.setPosition(pos)
        else:
            if self.activeModel:
                self.activeModel.setPos(render, pos)
            self.geom.setPosition(pos)
        self.pos = pos
        
        if self.visualization:
            self.visualization.setPos(pos)
            
    def getGeomPos(self):
        return self.geom.getPosition()
    
    def getGeomQuat(self):
        return self.geom.getQuaternion()
    
    def setGeomQuat(self, quat=None):
        if quat is None:
            quat = self.activeModel.getQuat(render)
            self.geom.setQuaternion(quat)
        else:
            if self.activeModel:
                self.activeModel.setQuat(render, quat)
            self.geom.setQuaternion(quat)
        self.quat = quat
        
        if self.visualization:
            self.visualization.setQuat(quat)
    
    """
    Simplified setting collision and category bits for geoms.
    Uses the bitMaskDict dictionary -- see at the begining of this file.
    """
    def setCatColBits(self, name):
        self.bitsName = name
        self.geom.setCollideBits(bitMaskDict[name][0])
        self.geom.setCategoryBits(bitMaskDict[name][1])
    
    def update(self, stepSize):
        return
        
    def destroy(self):
        print "REMOVING DESTROYING OBJECT", self.objectType
        self.physics.removeObject(self)
        if self.activeModel:
            self.activeModel.remove()
        if self.visualization:
            self.visualization.remove()
        self.geom.destroy()
        del self.visualization
        del self.geom
        del self.activeModel
        del self.physics
        print "FINISHED DESTROYING PHYSICAL OBJECT", self.objectType


class staticObject(physicalObject):
    def __init__(self, physics):
        physicalObject.__init__(self, physics)
        
        """
        This is the data for handling collisions.
        Previously, this was placed in the OdeGeomData class.
        
        In the future, it might be moved into some other place,
        so that it can be used by many objects, like bitMasks.
        """
        self.surfaceFriction = 0.0
        self.surfaceBounce = 0.0
        self.surfaceBounceVel = 0.0
        self.surfaceSoftCFM = 0.1
        self.surfaceSoftERP = 0.2
        self.surfaceSlip = 0.0
        self.surfaceDampen = 2.0
    
    """
    Set up and OdeBoxGeom of the given size.
    """
    def setBoxGeom(self, size):
        self.boxSize = size
        self.geom = OdeBoxGeom(self.physics.getSpace(), size)
        
        """
        If a nodePath is set, get the position and rotation from it
        """
        if self.activeModel:
            self.geom.setPosition(self.activeModel.getPos(render))
            self.geom.setQuaternion(self.activeModel.getQuat(render))
        
        """
        If visualization is enabled, create the visualization node
        """
        if self.visualize:
            np = "./media/models/ccdbox.egg"
            self.visualization = loader.loadModel(np)
            self.visualization.reparentTo(render)
            self.visualization.setScale(*self.geom.getLengths())
            self.visualization.setPos(self.geom.getPosition())
            self.visualization.setQuat(self.geom.getQuaternion())
    
    """
    Set a box geom from a given model.
    See World Manager class for details.
    """
    def setBoxGeomFromNodePath(self, node, remove=False):
        size = self.physics.extractSizeForBoxGeom(node)
        self.setBoxGeom(size)
        if remove:
            node.removeNode()
    
    """
    Set up an OdeTriMeshGeom from the given node.
    """
    def setTrimeshGeom(self, model, remove=False):
        if isinstance(model, basestring):
            model = loader.loadModel(model)
        trimeshData = OdeTriMeshData(model, True)
        self.geom = OdeTriMeshGeom(self.physics.getSpace(), trimeshData)
        if self.activeModel:
            self.geom.setPosition(self.activeModel.getPos(render))
            self.geom.setQuaternion(self.activeModel.getQuat(render))
        if remove:
            model.removeNode()
    
    """
    Set up an OdeSphereGeom of the given radius.
    """
    def setSphereGeom(self, radius):
        self.geom = OdeSphereGeom(self.physics.getSpace(), radius)
        
        """
        If a nodePath is set, get the position from it
        """
        if self.activeModel:
            self.geom.setPosition(self.activeModel.getPos(render))
        

"""
The kinematic object class. This type of object it meant to be animated
using Panda's Interval system.

The getLinearVel method can be usefull for making a moving platform, but
I haven't tried it this way yet.
"""
class kinematicObject(staticObject):
    def __init__(self, map):
        staticObject.__init__(self, map)
        self.objectType = "kinematic"
        
        self.linearVel = Vec3(0,0,0)
        self.prevPos = Vec3(0,0,0)
    
    """
    Get linear velocity
    """
    def getLinearVel(self):
        return self.linearVel
    
    def update(self, stepSize):
        quat = self.activeModel.getQuat(render)
        pos = self.activeModel.getPos(render)
        
        # To get m per s instead of m per simulation step
        self.linearVel = (pos - self.prevPos) * (1.0 / stepSize)
        
        self.geom.setPosition(pos)
        self.geom.setQuaternion(quat)
    
        if self.visualization:
            self.visualization.setQuat(quat)
            self.visualization.setPos(pos)
        
        self.prevPos = pos

"""
Simpler dynamic object, which has no continuous collision detection.

This type of object can be used for large and slow moving objects, but
shouldn't be used for small or fast moving ones.

This dynamic object has no protection against the tunneling effect.
"""
class dynamicObjectNoCCD(staticObject):
    def __init__(self, map):
        staticObject.__init__(self, map)
        self.objectType = "dynamic"
    
    def getLinearVel(self):
        return self.body.getLinearVel()
    
    """
    Setting a standard body with Box mass.
    It uses setBoxTotal instead of setBox, so give weight and not
    density.
    """
    def setBoxBody(self, weight, size):
        if not self.geom:
            print "you must set geom before setting body"
            return False
        if not self.activeModel:
            print "you must set nodepath before setting body"
            return False
        
        """
        IMPORTANT
        
        To prevent getting nan values when a box Body is rotating, set
        it to a cube. This still allows the Geom to collide correctly,
        but prevents the body from gaining speed by itself when rotating.
        """
        maxSize = self.geomSize[0]
        for s in self.geomSize:
            if s > maxSize:
                maxSize = s
        bodySize = Vec3(maxSize, maxSize, maxSize)
        
        self.mass = OdeMass()
        self.mass.setBoxTotal(weight, bodySize)
        
        self.body = OdeBody(self.physics.world)
        self.body.setMass(self.mass)
        self.body.setPosition(self.activeModel.getPos(render))
        self.body.setQuaternion(self.activeModel.getQuat(render))
        
        self.geom.setBody(self.body)
    
    """
    Setting a standard body with Sphere mass.
    It uses setSphereTotal instead of setSphere, so give weight and not
    density.
    """
    def setSphereBody(self, weight, radius):
        if not self.geom:
            print "you must set geom before setting body"
            return False
        if not self.activeModel:
            print "you must set nodepath before setting body"
            return False
            
        self.mass = OdeMass()
        self.mass.setSphereTotal(weight, radius)
        
        self.body = OdeBody(self.physics.world)
        self.body.setMass(self.mass)
        self.body.setPosition(self.activeModel.getPos(render))
        self.body.setQuaternion(self.activeModel.getQuat(render))
        
        self.geom.setBody(self.body)
        
    def getBody(self):
        return self.body
        
    def setPos(self, pos=None):
        staticObject.setPos(self, pos)
        if pos is None:
            self.body.setPosition(self.activeModel.getPos(render))
        else:
            self.body.setPosition(pos)
    
    """
    Update the node's position accordingly to the geom's position.
    """
    def update(self, stepSize):
        pos = Vec3(self.geom.getPosition())
        quat = Quat(self.geom.getQuaternion())
        
        self.activeModel.setPosQuat(render, pos, quat)
        self.previousPos = pos
        
    def destroy(self):
        staticObject.destroy(self)
        self.body.destroy()
        del self.body
        del self.mass

"""
The more complex version of a dynamic object, featuring
Continuous Collision Detection.

This version is not a subject to tunneling, so it should be used for fast
moving and/or small objects.

IMPORTANT LIMITATIONS

This implementation is meant to prevent tunneling, and not to
ensure proper behavior of the body. Read further coments to learn why bodies
can behave less realistically with this object type.

Don't use this implementation to make a sports game or such. It should be fine
for shooters and the like, but for sports games consider Bullet.

Another limitation is that it supports only box and sphere, and no compound shapes.
This should be enough for most games and most cases when CCD is needed, though.

Also, be aware that this class is much slower than the version without CCD!
"""
class dynamicObjectCCD(dynamicObjectNoCCD):
    def __init__(self, map):
        dynamicObjectNoCCD.__init__(self, map)
        
        """
        This object is handled by the World Manager in the exact same way as a normal Dynamic Object.
        """
        self.objectType = "dynamic"
        
        """
        The CCD process can be visualized.
        """
        self.showCCD = False
        
        """
        Two crucial variables.
        
        previousPos of the geom allows the system to know where
        to put the CCD helper geoms.
        
        ccdCollidingGeomPos is set to the colliding helper geom
        which is nearest the previous position of the real geom.
        """
        self.previousPos = None
        self.ccdCollidingGeomPos = None
        
        """
        ccDist is the distance between the helper geoms. It's set to it's
        actual value later, automatically.
        """
        self.ccdDist = 0.5
        
        """
        With this variable you can control the precision of the CCD process.
        
        2.0 is the most sensible value, but the higher you set it, the less
        the objects will 'sink' into environment before bumping off of it.
        
        The higher this value is, the more expensive the CCD process it.
        """
        self.ccdDistMultiplier = 2.0
        
        
        """
        The list that holds the helper objects.
        """
        self.helperObjects = []
    
    """
    Reimplementation of the dynamicObjectNoCCD.setBoxGeom method
    """
    def setBoxGeom(self, size):
        dynamicObjectNoCCD.setBoxGeom(self, size)
        
        """
        Automatically find the CCD Distance by searching for the
        shortest edge of the box.
        """
        self.ccdDist = self.geom.getLengths()[0]
        for len in self.geom.getLengths():
            if len < self.ccdDist:
                self.ccdDist = len
        return True
    
    """
    Reimplementation of the dynamicObjectNoCCD.setSphereGeom method
    """
    def setSphereGeom(self, radius):
        dynamicObjectNoCCD.setSphereGeom(self, radius)
        
        """
        Set the CCD Distance to the sphere's radius.
        I multiply it by 1.7 for better results -- just out of observation.
        """
        self.ccdDist = radius * 1.7
        
    def setBoxBody(self, weight, size):
        dynamicObjectNoCCD.setBoxBody(self, weight, size)
        self.previousPos = self.activeModel.getPos(render)
        
    def setSphereBody(self, weight, radius):
        dynamicObjectNoCCD.setSphereBody(self, weight, radius)
        self.previousPos = self.activeModel.getPos(render)
    
    """
    What the exception says
    """
    def setTrimeshGeom(self, model):
        raise Exception("Trimesh is not supported for ccd!!")
        return False
    
    """
    The callback method for Helper Geom objects.
    
    This allows me to find the nearest collision happening between
    two frames.
    """
    def castCollision(self, entry, object1, object2):
        """
        Don't care about collisions between this object and helper objects,
        or between two helper objects
        """
        if object2 is self or object2.objectType == "ccd":
            return
        
        """
        For convenience
        """
        geom = object1.geom
        
        """
        If there was no previous collision, default to this one and return.
        """
        if self.ccdCollidingGeomPos is None:
            self.ccdCollidingGeomPos = geom.getPosition()
            return
        
        """
        Get the distance between this helper collision and the previous
        position of this object.
        """
        vNew = self.previousPos - geom.getPosition()
        dNew = vNew.length()
        
        """
        Get the distance between the previous nearest helper collision
        and the previous position of this object.
        """
        vOld = self.previousPos - self.ccdCollidingGeomPos
        dOld = vOld.length()
        
        """
        If the new collision is nearer to the previous position than the
        previous nearest collision, switch them.
        
        This is used to make sure we don't get the collision from the other
        side of a wall, for example.
        """
        if dNew > dOld:
            self.ccdCollidingGeomPos = geom.getPosition()
    
    """
    Completely different update callback then the one from dynamicObjectNoCCD
    """
    def update(self, stepSize):
        quat = Quat(self.geom.getQuaternion())
        
        """
        Getn the distance the object traveled in this frame.
        """
        vel = self.body.getLinearVel()
        speed = vel.length()
        dist = speed * stepSize
        
        """
        Destroy all Helper Geoms and empty the geomCast list.
        """
        for obj in self.helperObjects:
            self.physics.removeObject(obj)
            if self.showCCD:
                obj.nodePath = None
            obj.collisionCallback = None
            obj.destroy()
        self.helperObjects = []
        
        if self.ccdCollidingGeomPos:
            """
            There was a collision detected by one of the helper geoms, stop
            the CCD process.
            """
            
            
            """
            For convenience.
            """
            pos = self.ccdCollidingGeomPos
            
            """
            Set the position of the geom AND THE BODY to the one detected
            by helper geoms.
            """
            self.geom.setPosition(pos)
            self.body.setPosition(pos)
            
            """
            To prevent the CCD from kicking in after the collision, what
            usually causes the body to flicker or permanently stick to the
            geom it collides with, WE NEED TO CUT DOWN IT'S VELOCITY.
            
            This is generally deemed abusing the physics engine, but
            I haven't found a better way yet.
            
            This is why this class shoudn't be used for sports games.
            Cutting velocity causes the object to bump off of the environment
            in a less realistic way, i.e. with less energy.
            
            Note, that how much velocity is removed depends on the size of
            the object.
            """
            amount = dist / self.ccdDist * self.ccdDistMultiplier
            if self.body.getLinearVel().length() > (vel / amount).length():
                self.body.setLinearVel(vel / amount)
            
        else:
            """
            The helper geoms detected no collision, start/continue the CCD process.
            """
            
            pos = Vec3(self.geom.getPosition())
            
            """
            Only do CCD if the object travaled more distance in this frame,
            than the value of the ccdDist variable.
            """
            if dist > (self.ccdDist / self.ccdDistMultiplier):
                """
                How many helper geoms are needed?
                """
                amount = dist / self.ccdDist * self.ccdDistMultiplier
                
                """
                The distance (vector) between the helper geoms
                """
                vec = pos - self.previousPos
                vecPart = vec / amount
                
                """
                Start casting helper geoms from the previous position of the object
                """
                castPos = self.previousPos
                
                amount = int(amount)
                r = range(amount)
                
                """
                CREATE HELPER GEOMS
                """
                for i in r:
                    """
                    The position vector of the new helper geom.
                    """
                    castPos += vecPart
                    
                    """
                    Create the helper object.
                    """
                    obj = staticObject(self.physics)
                    
                    """
                    A special object type for ccd helper geoms, which gives them
                    privileges in World Manager collision handling.
                    """
                    obj.objectType = "ccd"
                    
                    """
                    Set the collision callback to point to this dynamicObjects's
                    castCollision method. That way we can get the collisions from
                    the helper object.
                    """
                    obj.collisionCallback = self.castCollision
                    
                    """
                    Create the correct Geom depending on the type of this object's geom.
                    
                    At the same time, create visualization, if needed.
                    """
                    if str(self.geom.getClassType()) == "OdeBoxGeom":
                        if self.showCCD:
                            np = "./media/models/ccdbox.egg"
                            obj.setNodePath(np, render)
                            obj.nodePath.setScale(*self.geom.getLengths())
                        obj.setBoxGeom(self.geom.getLengths())
                    
                    elif str(self.geom.getClassType()) == "OdeSphereGeom":
                        if self.showCCD:
                            np = "./media/models/ccdsphere.egg"
                            obj.setNodePath(np, render)
                            obj.nodePath.setScale(self.geom.getRadius()*2.0)
                        obj.setSphereGeom(self.geom.getRadius())
                    
                    """
                    Set the cat/col bit masks to the same value as this object's
                    """
                    obj.setCatColBits(self.bitsName)
                    
                    """
                    Set the helper's position, quaternion, append it to the
                    geomCast list and add it, along with it's data,
                    to the World Manager.
                    """
                    obj.setGeomPos(castPos)
                    obj.setGeomQuat(self.geom.getQuaternion())
                    
                    self.helperObjects.append(obj)
                    self.physics.addObject(obj)
        
        """
        Update the geom's position, clear the colliding (helper) geom position
        variable and set previous position to current position for the next frame.
        """
        self.activeModel.setPosQuat(render, pos, quat)
        self.ccdCollidingGeomPos = None
        self.previousPos = pos
        
        if self.visualization:
            self.visualization.setQuat(quat)
            self.visualization.setPos(pos)
        
    def destroy(self):
        """
        Make sure we remove the helper objects.
        """
        for obj in self.helperObjects:
            self.physics.removeObject(obj)
            if self.showCCD:
                obj.nodePath = None
            obj.destroy()
        self.helperObjects = []
        
        dynamicObjectNoCCD.destroy(self)
        
        del self.helperObjects

"""
That's just for convenience, setting the default dynamicObject.
"""
global dynamicObject
dynamicObject = dynamicObjectCCD
#dynamicObject = dynamicObjectNoCCD

class rayObject(physicalObject):
    def __init__(self, physics):
        physicalObject.__init__(self, physics)
        self.objectType = "ray"
        
    def setRayGeom(self, length, rayAttribs = None):
        self.geom = OdeRayGeom(self.physics.getSpace(), length)
        if rayAttribs is not None:
            self.geom.set(*rayAttribs)
            
        self.synchPosQuatToNode()

"""
Explosion class for ODE

You use it by just creating it with the required attributes, it will 
self-destruct as soon as it runs out of power.
"""
class explosion(kinematicObject):
    def __init__(self, map, pos, force = 100.0, radius = 0.5):
        """
        You might notice that I'm not setting a collision callback here,
        like I would with OdeGeomData previously. That's because the
        self.collisionCallback method is used (same with all other objects).
        """
        
        kinematicObject.__init__(self, map)
        
        """
        Note that previously (with OdeGeomData) this was done with isTrigger
        variable. Now it's just a separate object type.
        """
        self.objectType = "trigger"
        
        self.timeElapsed = 0.0
        self.speed = 2000.0
        self.force = force
        self.currentForce = 0.0
        self.radius = radius
        
        self.collisions = []
        
        self.setSphereGeom(radius)
        self.setGeomPos(pos)
        
        self.physics.addObject(self)
        
    """
    Get all geoms within the range
    
    You might notice this method is FAR simpler and shorter than previously.
    You'll find out why in the World Manager class.
    """
    def collisionCallback(self, entry, object1, object2):
        self.collisions.append([object2, entry.getContactGeom(0).getNormal(), entry.getContactPoint(0)])
        
    def update(self, timeStep):
        self.timeElapsed += timeStep
        
        if self.timeElapsed > .1:
            self.physics.removeObject(self)
            self.destroy()
            return
        
        force = self.force - self.geom.getRadius()/10.0
        
        for obj, normal, point in self.collisions:
            if obj.body:
                forceVector = -normal * force
                obj.body.enable()
                obj.body.addForce(forceVector)
                
        self.radius += self.speed * self.timeElapsed**2
        self.geom.setRadius(self.radius)
        
        self.collisions = []

"""
Most important class which... well, manages the world.
"""
class ODEWorldManager(object):
    def __init__(self, isisworld):
        self.main = isisworld
        self.world = OdeWorld()
        self.world.setGravity(0, 0, -9.81)
        
        """
        An important optimization. Manipulate the values to get the correct behaviour,
        but I advice not to turn it off.
        
        What it does, is it puts to sleep (disables) objects that are not used (the combined
        forces set on them are lower than thresholds set) for a specific time/number of steps.
        """
        self.world.setAutoDisableFlag(1)
        self.world.setAutoDisableAngularThreshold(0.3)
        self.world.setAutoDisableLinearThreshold(0.3)
        self.world.setAutoDisableSteps(60)
        self.world.setAutoDisableTime(0.0)
        
        """
        Standard ODE stuff
        """
        self.contactGroup = OdeJointGroup()
        self.space = OdeSimpleSpace()
        
        self.stepSize = 1.0/60.0
        
        """
        The list of objects in the simulation.
        
        If you used the previous version, you might remember there were two lists before,
        one for dynamics, one for kinematics. This is no longer needed because of the
        *Object classes above.
        """
        self.objects = []
        
        """
        This is used to get objects by it's geom surface type. It's needed because
        of ditching the odeGeomData. Basically this move made all object code MUCH
        more readable and simple, but it came with the price of this nasty piece.
        
        I might eventually find a better way to handle this, or not, but in any case
        possible changes to this area will not affect your code.
        
        More on that in the addObject, removeObject and update methods.
        """
        self.lastGeomIndex = 0
        self.objectGeomIndexes = {}
        
        """
        Convenient way to pause the world.
        """
        base.accept("pause", self.pause)
        base.accept("unpause", self.unpause)
    
    def pause(self):
        self.stopSimulation()
        
    def unpause(self):
        self.startSimulation(self.stepSize)
    
    """
    This function gets the size of a Node's bounding box. It's used to create OdeBoxGeoms
    from Nodes in physicalObject.setBoxGeomFromNodePath method.
    
    FOR BEST RESULTS (in Blender) make sure your models are only rotated in object-mode, while
    remaining aligned with their local XYZ in edit-mode. Also, make sure the objects have only
    as much rotation as they *really* need. Otherwise you might get artifacts with this method.
    """
    def extractSizeForBoxGeom(self, node):
        quat = node.getQuat(render)
        node.setHpr(render, Vec3(0, 0, 0))
        
        p1, p2 = node.getTightBounds()
        
        sx = abs(p1.getX() - p2.getX())
        sy = abs(p1.getY() - p2.getY())
        sz = abs(p1.getZ() - p2.getZ())
        
        node.setQuat(render, quat)
        
        return Vec3(sx, sy, sz)
    
    def getSpace(self):
        return self.space
        
    def destroy(self):
        self.stopSimulation()
        for object in self.objects:
            self.removeObject(object)
        
        self.contactGroup.empty()
        self.space.destroy()
        self.contactGroup.destroy()
        self.world.destroy()
        
        del self.space
        del self.contactGroup
        del self.world
        
        del self.objects
        
        return True
    
    """
    Collide only one object against the rest of the space. I use it to check
    whether an object can be dropped somewhere.
    
    I'm worried that this method might eventually proove too inefficient for
    really large worlds, so be aware it might get deprecated in the future.
    Still, there's a lot of potential for optimization here, me thinks, so time will tell.
    """
    def collideSelected(self, selected, exclude=[]):
        entries = []
        
        selCat = selected.getCategoryBits()
        selCol = selected.getCollideBits()
        
        for idx in range(self.space.getNumGeoms()):
            geom = self.space.getGeom(idx)
            
            # Check bitmasks
            geomCat = geom.getCategoryBits()
            geomCol = geom.getCollideBits()
            if (selCat & geomCol) | (geomCat & selCol) == BitMask32(0):
                continue
            
            if not geom.isEnabled():
                continue
            if geom in exclude:
                continue
            if self.getObjectByGeomSurfaceIndex(geom).objectType in ["trigger", "ccd", "ray"]:
                continue
            
            entry = OdeUtil.collide(selected, geom, 1)
            if entry.getNumContacts():
                entries.append(entry)
        return entries
    
    """
    Do a raycast against the space using an existing ray.
    """
    def doRaycast(self, ray, exclude=[]):
        ray.enable()
        
        closestEntry = None
        closestGeom = None
        
        rayCat = ray.getCategoryBits()
        rayCol = ray.getCollideBits()
        
        
        
        for idx in range(self.space.getNumGeoms()):
            geom = self.space.getGeom(idx)
            if not geom.isEnabled():
                continue
            if geom in exclude:
                continue
            geomCat = geom.getCategoryBits()
            geomCol = geom.getCollideBits()
            calc = (rayCat & geomCol) | (geomCat & rayCol)
            if calc == BitMask32(0):
                continue
            entry = OdeUtil.collide(ray, geom, 2)
            if entry.getNumContacts():
                depth = entry.getContactGeom(0).getDepth()
                if closestEntry is None:
                    closestEntry = entry
                    closestGeom = geom
                elif depth < closestEntry.getContactGeom(0).getDepth():
                    closestEntry = entry
                    closestGeom = geom
        
        ray.disable()
        
        if closestGeom:
            closestobject = self.getObjectByGeomSurfaceIndex(closestGeom)
        else:
            closestobject = None
        
        return (closestEntry, closestobject)
    
    """
    Create a ray and do a raycast against the space with it.
    """    
    def doRaycastNew(self, bitMaskName, length, rayAttribs, exclude=[]):
        print "RAYCASTING new"
        
        ray = OdeRayGeom(self.space, length)
        ray.set(*rayAttribs)
        ray.setCollideBits(bitMaskDict[bitMaskName][0])
        ray.setCategoryBits(bitMaskDict[bitMaskName][1])
        
        closestEntry, closestObject = self.doRaycast(ray, exclude)
        
        ray.destroy()
        del ray
        
        return (closestEntry, closestObject)
    
    """
    
    This is the main replacement for the odeGeomData stuff here.
    It uses the objectGeomIndexex dictionary, which contains the
    surfaceType value assigned to the geom (key) and the object
    that uses this geom (value).
    
    It's used to get from the geom to the object. The other way is simple,
    but this is tricky, since OdeGeoms in Panda don't support any kind of
    taging. If they did, it would be super easy, and wouldn't require such
    nasty hacks.
    """
    def getObjectByGeomSurfaceIndex(self, geom):
        idx = self.space.getSurfaceType(geom)
        return self.objectGeomIndexes[idx]
    
    """
    A more flexible replacement for AutoCollide. In this version getting a major overhaul and optimization (yay).
    
    If you've used 0.9 (and earlier) you will notice, that this time I work on OBJECTS rather than GEOMS. This
    is an important simplification and it allows for some optimization too. That's why I ditched the OdeGeomData
    class, because without it everything is a lot more straightforward, and it prooved to be pointless, since
    with the CopperODE design it could not be used by more than one object at the same time anyway.
    
    Additionally, notice that the collision callbacks are now called with the object1 and object2 values, where
    object1 is the one the callback method belongs to, while object2 is the other object taking part in the collision.
    You might want to ask why I even send object1 then, since it's the same as "self" in the callback method anyway.
    Well, exactly for that reason. It doesn't hurt performance (just one argument more or less), but made debugging
    a lot easier initially, so I decided to keep it, just in case.
    
    Anyway, I hope you'll notice how much cleaner the method is now.
    """
    def handleCollisions(self, arg, geom1, geom2):
        entry = OdeUtil.collide(geom1, geom2)
        
        if entry.isEmpty():
            return
        
        """
        Get the physical objects that use those geoms using their surface type.
        I gotta make a request for pythonTags on odeGeoms... seriously.
        
        On a side note, initially I used a for loop for that. Heck, that was slow beyond any description.
        """
        object1 = self.getObjectByGeomSurfaceIndex(geom1)
        object2 = self.getObjectByGeomSurfaceIndex(geom2)
        
        """
        No collisions between "naked" geoms are permited. Physical objects have a monopoly on collisions here.
        """
        if object1 is None or object2 is None:
            return
        
        """
        Get the types of the two objects for convenience and better readability.
        """
        type1 = object1.objectType
        type2 = object2.objectType
        
        """
        Ignore collisions when both objects are tiggers or static objects.
        """
        ignoredTypes = ["trigger", "static"]
        if type1 in ignoredTypes and type2 in ignoredTypes:
            return
        
        """
        Ignore collisions between rays, ccd helpers and/or triggers.
        Note that we've already sorted out collisions between triggers and statics,
        but now we DO want statics here, because rays and ccd helpers must collide
        with those.
        
        This and the previous instructions are very important optimizations.
        Obviously, feel free to tweak this as needed, just make sure not to
        handle collisions between two static objects -- doing those will
        eat your FPS badly.
        """
        ignoredTypes = ["ray", "ccd", "trigger"]
        if type1 in ignoredTypes and type2 in ignoredTypes:
            return
        
        """
        Get the bodies of the two objects for convenience and better readability.
        """
        body1 = object1.body
        body2 = object2.body
        
        """
        And now we add statics to ignored types to get the total of:
        ["ray", "ccd", "trigger", "static"].
        
        This is because the next step is actually creating collisions between
        objects (so that ODE can deal with physical interaction).
        Yet for the objects of the aforementioned types we just want the
        collision callbacks called.
        """
        ignoredTypes += ["static"]
        
        """
        Create collision joints between certain objects.
        """
        if body1 or body2 and type1 not in ignoredTypes and type2 not in ignoredTypes:
            """
            Don't do collisions between two disabled dynamic objects.
            """
            if body1 and body2 and not body1.isEnabled() and not body2.isEnabled():
                return
            if body1 and not body1.isEnabled() and type2 == "static":
                return
            if body2 and not body2.isEnabled() and type1 == "static":
                return
            
            """
            Make sure a collision between a kinematic object and a dynamic one
            wakes up the later.
            """
            if body1 and type2 == "kinematic":
                body1.enable()
            if body2 and type1 == "kinematic":
                body2.enable()
            
            """
            The standard ODE contact joint setting voodoo starts here.
            """
            surfaceParams = OdeSurfaceParameters()
            
            """
            Be carefull with those flags. softERP and softCFM for example don't like
            it when approx is enabled. If you want to make water, for example, you gonna
            need to "if" here and disable approx for that.
            """
            # Enable a more accurate friction model (approx)
            # Flags: mu2, fdir1, bounce, softERP, softCFM, motion1, motion2, slip1, slip2, approx1, approx2, approx
            surfaceParams.setMode(0b110000000111)
            
            surfaceParams.setMu(object1.surfaceFriction)
            surfaceParams.setMu2(object2.surfaceFriction)
            surfaceParams.setSlip1(object1.surfaceSlip)
            surfaceParams.setSlip2(object2.surfaceSlip)
            
            numContacts = entry.getNumContacts()
            
            """
            Pick the body that will become the provider of FDir.
            """
            if body1:
                body = body1
            elif body2:
                body = body2
            else:
                body = None
            
            for i in range(numContacts):
                cgeom = entry.getContactGeom(i)
                
                contactPoint = entry.getContactPoint(i)
                
                contact = OdeContact()
                contact.setGeom(cgeom)
                
                """
                Set the friction direction one to the linear velocity
                of the body selected earlier (if any). The friction
                direction two is calculated automatically by ODE.
                
                Before you ask, ODE doesn't support rolling friction, so
                any balls you might have in your game will spin infinitely.
                To prevent that, you might try adding damping forces.
                """
                if body:
                    contact.setFdir1(body.getLinearVel())
                
                contact.setSurface(surfaceParams)
                
                contactJoint = OdeContactJoint(self.world, self.contactGroup, contact)
                contactJoint.attach(body1, body2)
        
        """
        Call the collision callbacks on both objects. Note the positions of object1 and object2
        in both callbacks. They depend on which object we call the collision callback on.
        
        I did this to make sure I don't have to check that inside the callbacks themselves.
        """
        object1.collisionCallback(entry, object1, object2)
        object2.collisionCallback(entry, object2, object1)
        
    
    """
    Add object (*Object class' instance) to the simulation
    
    At the same time I assign an index to that Geom/Object pair
    and put it into that objectGeomIndexes dictionary.
    
    Have I mentioned the need for odeGeom python tagging?
    """
    def addObject(self, obj):
        geom = obj.getGeom()
        
        self.lastGeomIndex += 1
        self.space.setSurfaceType(geom, self.lastGeomIndex)
        
        self.objectGeomIndexes[self.lastGeomIndex] = obj
        
        self.objects.append(obj)

    
    """
    Remove object from simulation
    """
    
    
    def removeObject(self, object):
        if object not in self.objects:
            return False
        
        geomIndex = self.space.getSurfaceType(object.geom)
        del self.objectGeomIndexes[geomIndex]
        
        idx = self.objects.index(object)
        self.objects.pop(idx)
        
        return True
    
    """
    Step the simulation
    """
    def simulationTask(self, task):
        
        # run XML commands
        self.main.commandHandler.panda3d_thread_process_command_queue()
                
        self.space.collide("", self.handleCollisions)
        self.world.quickStep(self.stepSize)
        self.contactGroup.empty()
        
        """
        Update the objects in the simulation
        """
        for object in self.objects:
            object.update(self.stepSize)
                
        return task.again
    
    def startSimulation(self, stepSize):
        self.stepSize = stepSize
        taskMgr.add(self.main.cloud_moving_task, "visual-movingClouds")
        taskMgr.doMethodLater(stepSize, self.simulationTask, "physics-ODESimulation")
        
    def stopSimulation(self):
        taskMgr.remove("visual-movingClouds")
        taskMgr.remove("physics-ODESimulation")

