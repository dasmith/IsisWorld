# -*- coding: UTF-8 -*-

# Copyright (c) 2009, Piotr Podgórski
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
#       in the documentation and/or other materials provided with the distribution.
#    3. Neither the name of the Author nor the names of other contributors may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState

FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)
PICKMASK = BitMask32.bit(2)
AGENTMASK = BitMask32.bit(3)
THINGMASK = BitMask32.bit(4)

from ODEWireGeom import wireGeom 

class odeGeomData:
    """
    This is my class for keeping the surface data and more.
    If you want to use my odeWorldManager you must also use this class
    and not the standard Panda/ODE surfaceTable
    """
    def __init__(self):
        """
        Any object can be handled as an Area Trigger,
        but for real Area Trigger functionality
        you need the odeTrigger class.

        This isTrigger setting just tells the collision handler
        whether to make an actual collision between this object
        and others or just execute it's callback.
        """
        self.isTrigger = False

        """
        The method to be called when a collision with the object
        that uses this Data occurs.
        """
        self.collisionCallback = None

        """
        This is used when the player attempts to use an object
        Of course objects are usable (clickable) only when
        this is not None.
        """
        self.selectionCallback = None

        """
        This is for general usage
        """
        self.pythonObject = None

        self.name = ""

        """
        And here we have the standard ODE stuff for collisions
        """
        self.surfaceFriction = 0.1#OdeUtil.getInfinity()#0.1
        self.surfaceBounce = 0.2
        self.surfaceBounceVel = 0.0
        self.surfaceSoftERP = 0.0
        self.surfaceSoftCFM = 1e-3
        self.surfaceSlip = 0.1
        self.surfaceDampen = 0.2

class PhysicsCharacterController:
    """
    The Kinematic Character Controller is the feature that is the most
    painfully missing from ODE in my personal opinion.

    Some justification for using KCC over DCC.

    I really don't know why, but most of the ODE sources (wiki, mailing list)
    suggest that the best approach to character control with ODE is the
    dynamic controller. Since this might look like the simpler sollution
    (as in "oh, I just need to keep the capsule upwards and ODE will
    do the rest, briliant") it's very, very missleading. Trust me, there
    is a reason why none (as far as I'm aware) of the physics engines
    that provide character controller use dynamic objects for this
    functionality.

    The Dynamic CC, while easy to get started with is extremelly unpredictable
    and difficult to control. As a result they don't act like a character
    capable of conscious movement. This should come as no surprise,
    the dynamic body is meant to be meant to be inert. Characters are not.
    Thus in order to get DCC to move more "character-like" you need to
    put lots and lots of constraints on it up to the point where it becomes
    pointless to even have a body there.

    The sollution to those problems is the Kinematic Character Controller.
    This might sound like a step backwards, because it's strictly collision
    detection based and not physics based, so at first it seems like it's place
    is in the '90s. But in reality using physics where it doesn't belong
    is just pointless.
    """
    def __init__(self, worldManager):
        self.worldManager = worldManager
        self.odeWorld = self.worldManager.world
        self.space = self.worldManager.space

        """
        Here we set the capsule Geom used for collision detection during movement.
        (for damage I suggest using separate hitboxes).

        The values here fit my needs so far but, as you can see, they're hardcoded.
        I haven't made any kind of setHeight, setRadius etc. here, because I just
        don't need that at this point, and it prooved to be a little tricky (I guess
        sizes in ODE do not follow the Panda's world when things are scaled), so at
        this point finding the right values is trial and error. Sorry.
        """
        
        self.radius = .5
        self.walkLength =  2.1
        self.walkLevitation = 2.1 
        self.crouchLength = .1
        self.crouchLevitation = 1.2
        self.length = self.walkLength
        self.levitation = self.walkLevitation
        self.capsuleGeom = OdeCappedCylinderGeom(self.space, self.length- self.radius*2.0, self.length)
        # TODO, create a second physics that uses the body.
        
        #self.capsuleGeom.setIntoCollideMask(BitMask32.allOff()|AGENTMASK)
        #self.cylinderNodepath = wireGeom().generate ('cylinder', radius=self.radius, length=self.length- self.radius*2.0) 
        #self.cylinderNodepath.reparentTo(self.actor)
        #self.capsuleGeom.setOffsetPosition(0,0,1.7)
        
        self.offsetVec = Vec3(0,0,-1.9)
        import random
        x = random.randint(0,10)
        y = random.randint(0,10)
        z = random.randint(5,10)
        self.setPos(Vec3(x,y,z))

        """
        This is here mainly for fly-mode. but maybe I'll find other uses for this.
        Anyway, this var controls how the direction of movement is calculated.
        In fly mode I set it to camera and the character flies wherever I look.
        In walking mode I set it to the capsule so that it moves in a more 2D
        matter.
        """
        self.movementParent = self.capsuleGeom

        """
        The foot ray that's meant to control the levitation and so on.
        This is a rather typpical sollution for the "how to get character
        to walk up stairs"-problem.
        """
        self.footRay = OdeRayGeom(self.space, 3.0)
        self.footRay.set(0, 0, 0, 0, 0, -1)

        self.setCollideBits(BitMask32(0x00000122))
        self.setCategoryBits(BitMask32(0x0000111))

        """
        The GeomData for the character capsule.
        """
        self.capsuleData = odeGeomData()
        self.capsuleData.name = "charCapsule"
        self.capsuleData.isTrigger = False
        self.capsuleData.collisionCallback = self.capsuleCollision
        self.capsuleData.pythonObject = self
        self.capsuleData.surfaceFriction = 2.0
        self.worldManager.setGeomData(self.capsuleGeom, self.capsuleData, self, True)
     
        #self.capsuleGeom.setCollideBits(BitMask32.allOn())
        """
        The geomData for the footRay. Note that I don't set any of the
        typpically ODE stuff here (friction and the like) because it's not needed.

        Also note that the capsule and the ray both have their own collision
        callback methods.
        """
        footData = odeGeomData()
        footData.isTrigger = True
        footData.collisionCallback = self.footCollision
        self.worldManager.setGeomData(self.footRay, footData, None)

        """
        The current speed of the character's movement. 2d because
        jumping is handled elswhere.
        """
        self.speed = [0, 0]

        """
        The control variables for jumping and falling
        """
        self.jumpStartPos = 0.0
        self.jumpTime = 0.0
        self.jumpSpeed = 0.0
        self.fallStartPos = 0.0
        self.fallSpeed = 0.0
        self.fallTime = 0.0

        """
        This is used to block crouching in small spaces, so that character
        doesn't stand up inside of a ventilation shaft. Of course
        the shaft has to be "filled" with area trigger.

        The test map has an example of how to use this.
        """
        self.crouchLock = False

        """
        State variable to know what the character is currently doing.
        The possible values are:
            - ground
            - jumping
            - falling
            - fly
        Crouching is not considered a state here, but it might be one
        in your FSM for example.

        I don't use FSM here because it's too sophisticated for this task.
        """
        self.state = ""

        """
        This is used to store the highest hit on the footray. It's needed
        to calculate the height we're currently on.
        """
        self.highestEntry = None

    def setPos(self, pos):
        self.capsuleGeom.setPosition(pos)
        self.currentPos = pos
        self.actor.setPos(pos+self.offsetVec)

    def setCollideBits(self, bits):
        self.capsuleGeom.setCollideBits(bits)
        self.footRay.setCollideBits(bits)

    def setCategoryBits(self, bits):
        self.capsuleGeom.setCategoryBits(bits)
        self.footRay.setCategoryBits(bits)


    def setH(self, h):
        quat = self.getQuat()
        hpr = quat.getHpr()
        hpr[0] = h
        quat.setHpr(hpr)
        self.actor.setHpr(hpr)
        self.setQuat(quat)

    def setQuat(self, quat):
        self.actor.setQuat(Quat(quat))
        self.capsuleGeom.setQuaternion(Quat(quat))

    def getQuat(self):
        return self.capsuleGeom.getQuaternion()

    def crouch(self):
        self.levitation = self.crouchLevitation
        self.capsuleGeom.setParams(self.radius, self.crouchLength)
        return True

    def crouchStop(self):
        if self.crouchLock:
            return False
        self.levitation = self.walkLevitation
        self.capsuleGeom.setParams(self.radius, self.walkLength)
        return True

    def capsuleCollision(self, entry, geom1Data, geom2Data):
        """
        The character's Capsule Collision callback.
        """
        if not entry.getNumContacts() or geom1Data.isTrigger or geom2Data.isTrigger:
            return

        """
        In the previous version of this code I've used forces to push bodies around,
        but I've found it to be not needed. And it gave worse results.
        Now, for bodies, I relly on ODE's internal systems, that are meant
        to stop bodies from penetrating static (or in this case kinematic,
        but for ODE it's the same) objects.

        However, we still need to handle collisions between the character
        and the static environment or other kinematic objects (such as door).
        """
        if not entry.getGeom2().hasBody() and not entry.getGeom1().hasBody():
            """
            We need to run through all of the contact points,
            because otherwise the character would go through walls
            when walking into a corner in a room made of
            one collision sollid.
            """
            for i in range(entry.getNumContacts()):
                point = entry.getContactPoint(i)
                geom = entry.getContactGeom(i)
                depth = geom.getDepth()
                normal = geom.getNormal()
                print geom
                """
                Move the character away from the object it collides with to prevent
                penetrating it. ODE itself won't do that because the capsule
                is not a body.

                I move it slightly less than the returned penetration depth because
                I found the character to shake less this way.

                Note that the direction of movement is dependant on which object
                in the collision process our character happens to be.
                """
                if geom1Data is self.capsuleData:
                    for i in range(3):
                        self.currentPos[i] += depth * 0.8 * normal[i]
                else:
                    for i in range(3):
                        self.currentPos[i] -= depth * 0.8 * normal[i]

            """
            This prevents the character from penetrating ceilings that are
            lower than the character's maximum jump height.
            """
            if normal[2] == -1 and self.state == "jumping":
                self.fallStartPos = self.capsuleGeom.getPosition()[2]
                self.fallSpeed = 0.0
                self.fallTime = 0.0
                self.state = "falling"

    def footCollision(self, entry, geom1Data, geom2Data):
        """
        Here we handle the collisions that the foot ray participates in.
        The self.highestEntry get's it's value here.
        Note that there's a constant process of sorting going on here.
        """
        if not entry.getNumContacts():
            return
        if entry.getGeom1() == self.capsuleGeom or entry.getGeom2() == self.capsuleGeom:
            return
        if self.highestEntry is None or (entry.getContactPoint(0)[2] > self.highestEntry.getContactPoint(0)[2]):
            self.highestEntry = entry

    def update(self, stepSize):
        """
        Find out how hight above the ground (directly beneath us) we are.
        """
        height = None
        if self.highestEntry is not None:
            height = self.capsuleGeom.getPosition()[2] - self.highestEntry.getContactPoint(0)[2]

        """
        This will become the new position for our character.
        """
        newPos = self.currentPos

        """
        If the state is fly that means we're in the fly mode so everything releated to
        walking is irrelevant
        """
        if self.state == "fly" :
            pass

        elif self.state == "jumping":
            print "jumping"
            newPos[2] = self.processJump(newPos, stepSize, self.highestEntry)
            self.speed = [0,0]

        elif height is None:
            """
            Height is None when we're too high for the foot ray to have anything to collide with.
            That means we have to fall.
            """
            #print "height 1"
            newPos = self.fall(newPos, stepSize, self.highestEntry)

        elif height > self.levitation + 0.01 and height < self.levitation + 0.65 and self.state == "ground":
            #print "height 2"
            """
            This means we're walking down stairs.
            Step walking is kinda harsh and I know that. It's fine with me, but I might still try
            to do something about it in the future.
            """
            newPos = self.stickToGround(newPos, stepSize, self.highestEntry)

        elif height > self.levitation + 0.01:
            #print "height 3 ", self.levitation+0.01, height
            """
            We're falling but we're low enough for the ray to collide with the ground.
            """
            newPos = self.fall(newPos, stepSize, self.highestEntry)

        elif height <= self.levitation + 0.01:
            #print "height 4 ", self.levitation+0.01, height
            #print "height 4"

            """"
            This means we're walking up stairs.
            """
            newPos = self.stickToGround(newPos, stepSize, self.highestEntry)

        """
        Calculate the walking.
        """
        speedVec = Vec3(self.speed[0]*stepSize, self.speed[1]*stepSize, 0)
        try:
            quat = self.movementParent.getQuaternion()
        except AttributeError:
            quat = self.movementParent.getQuat(render)
        """
        The xform function is very usefull. It gives you your vector with
        the appropriate rotation applied.
        """
        speedVec = quat.xform(speedVec)
        newPos += speedVec

        """
        Finish and set the positions of everything
        """
        self.currentPos = newPos
        self.capsuleGeom.setPosition(newPos)
        self.actor.setPos(newPos+self.offsetVec)
        rayPos = Vec3(newPos)
        rayPos[2] -= self.length/2
        self.footRay.setPosition(rayPos)
        npPos = Vec3(newPos)
        npPos[2] -= self.levitation + 0.15

        """
        And clean the highest entry.
        """
        self.highestEntry = None

    def processJump(self, newPos, stepSize, highestEntry):
        """
        Time elapsed since the beginning of the jump
        """
        self.jumpTime += stepSize

        """
        Fall speed might be used to calculate how hard we hit the ground
        for character health.
        """
        self.fallSpeed = self.jumpSpeed*self.jumpTime + (-9.81)*(self.jumpTime)**2

        np = self.jumpStartPos + self.fallSpeed

        if highestEntry and np <= highestEntry.getContactPoint(0)[2] + self.levitation:
            self.state = "ground"
            return highestEntry.getContactPoint(0)[2] + self.levitation

        return np

    def stickToGround(self, newPos, stepSize, highestEntry):
        """
        If fallSpeed is set that means it's the first call of stickToGround since
        we've finished a jump or a fall. This means we need to call the fall
        callback and reset the fallSpeed.
        """
        if self.fallSpeed:
            self.fallCallback(self.fallSpeed)
        self.fallSpeed = 0.0

        """
        Make sure the state is set correctly
        """
        self.state = "ground"

        """
        Levitate the capsule
        """
        newPos[2] = highestEntry.getContactPoint(0)[2] + self.levitation
        return newPos

    def fall(self, newPos, stepSize, highestEntry):
        if self.state != "falling":
            """
            This means we've just started to fall.
            Let's reset everything.
            """
            self.fallStartPos = self.capsuleGeom.getPosition()[2]
            self.fallSpeed = 0.0
            self.fallTime = 0.0
            self.state = "falling"
        else:
            """
            This means we're in the middle of a fall
            """
            self.fallTime += stepSize
            self.fallSpeed = (-9.81)*(self.fallTime)**2
        newPos[2] = self.fallStartPos + self.fallSpeed
        return newPos

    def fallCallback(self, speed):
        print "A character has hit the ground with speed:", speed

    def setSpeed(self, x, y):
        self.speed[0] = x
        self.speed[1] = y

    def jump(self):
        """
        Start a jump
        """
        if self.state != "ground":
            return
        self.jumpSpeed = 8.0
        self.jumpStartPos = self.capsuleGeom.getPosition()[2]
        self.jumpTime = 0.0
        self.state = "jumping"


class odeTrigger:
    """
    The trigger mechanics for ODE.

    The way it works is very simple. It has a list of the geoms
    that were there inside the trigger in the last update pass.
    This is the self.oldGeoms.

    On the other hand it has a list of the geoms that collide
    in this pass for the first time.
    That's the self.newGeoms.

    In every pass it compares the two lists. If something is
    in the self.newGeoms but not in self.oldGeoms that means
    this geom has just entered the trigger in this pass.
    If something is in the self.oldGeoms but not in self.newGeoms
    that means it has left the trigger.
    """
    def __init__(self, wm):
        self.worldManager = wm
        self.triggerMessage = ""
        self.triggerGeom = None
        self.oldGeoms = []
        self.newGeoms = []
        self.transGeoms = []

    def handleCollision(self, entry, geom1Data, geom2Data):
        if entry.getGeom1() == self.triggerGeom:
            geom = entry.getGeom2()
        elif entry.getGeom2() == self.triggerGeom:
            geom = entry.getGeom1()
        else:
            return

        if geom not in self.newGeoms:
            self.newGeoms.append(geom)

    def update(self, stepSize):
        for geom in self.newGeoms:
            if geom not in self.oldGeoms:
                messenger.send(self.triggerMessage+"_enter", [geom])
        for geom in self.oldGeoms:
            if geom not in self.newGeoms:
                messenger.send(self.triggerMessage+"_exit", [geom])

        self.oldGeoms = list(self.newGeoms)
        self.newGeoms = []


class PhysicsWorldManager:
    """
    World manager is meant to make it easier to handle ODE in a game.
    It also contains some functionality that is crucial to the functioning
    of triggers and KCC.
    """
    def __init__(self, FRAME_RATE=20):
        self.world = OdeWorld()
        self.world.setGravity(0, 0, -9.81)

        self.timeAccu = 0.0
        self.FRAME_RATE = FRAME_RATE
        """
        The list of odeGeomData objects.
        More on this later.
        """
        self.geomsData = []

        """
        Standard ODE setup
        """
        self.contactGroup = OdeJointGroup()
        self.space = OdeSimpleSpace()
        self.raySpace = OdeSimpleSpace()
        self.stepSize = 0.01

        """
        This dictionary and list contain two, very different, types of objects.
        I will explain later what one is a dict and the other is a list.
        """
        self.dynamics = {}
        self.kinematics = []

        # for pausing the simulator
        self.paused = True 
        self._globalClock = ClockObject.getGlobalClock()
        self._frameTime=self._globalClock.getFrameTime()
        self._globalClock.setRealTime(self._frameTime)
        self._globalClock.setMode(ClockObject.MLimited)
        self._globalClock.setFrameRate(self.FRAME_RATE)
        self.togglePaused()

    def stepSimulation(self, stepTime):
        if self.paused:
            self.togglePaused(stepTime)
        else:
            print "Error, cannot step while simulator is running"

    def togglePaused(self, stepTime=None):
        """ by default, the simulator is unpaused/running."""
        if (self.paused):
            print "[IsisWorld] Restarting Simulator"
            self._frameTime=self._globalClock.getFrameTime()
            self._globalClock.setRealTime(self._frameTime)
            self._globalClock.setMode(ClockObject.MNormal)
            self._globalClock.setFrameRate(self.FRAME_RATE)
            #base.enableParticles()
            self._globalClock=None
            self.startPhysics(stepTime)
        else:
            self.stopPhysics()
        # only untoggle bit if pause is called, not step
        if stepTime == None:
            self.paused = not self.paused

    def collideSelected(self, selected, exclude=[]):
        """
        A convenience method for colliding only one object with the rest
        instead of running the whole collision test on the whole space.

        You can also exclude certain objects from the test.
        """
        entries = []
        for idx in range(self.space.getNumGeoms()):
            geom = self.space.getGeom(idx)
            if not geom.isEnabled():
                continue
            if geom in exclude:
                continue
            entry = OdeUtil.collide(selected, geom, 2)
            if entry.getNumContacts():
                entries.append(entry)
        return entries

    def doRaycast(self, ray, exclude=[]):
        """
        Similar to the above, but only for rays and I also sort the hits myself here.
        I just want to be sure that the hit I get in return is always the closest one.
        """
        closestEntry = None
        closestGeom = None
        for idx in range(self.space.getNumGeoms()):
            geom = self.space.getGeom(idx)
            if not geom.isEnabled():
                continue
            if geom in exclude:
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
        return (closestEntry, closestGeom)

    def getGeomData(self, geom):
        """
        Get the odeGeomData object associated with this geom.
        I use the getSurfaceType for convenience so that
        I don't need to write my own stuff.
        """
        idx = self.space.getSurfaceType(geom)
        try:
            return self.geomsData[idx]
        except IndexError:
            return None

    def handleCollisions(self, arg, geom1, geom2):
        """
        A more flexible replacement for autoCollide.
        """
        entry = OdeUtil.collide(geom1, geom2)

        if entry.isEmpty():
            return

        geom1Data = self.getGeomData(geom1)
        geom2Data = self.getGeomData(geom2)
        

        if geom1Data.isTrigger and geom2Data.isTrigger:
            """
            Detecting a collision between two area triggers would be a little pointless
            """
            return

        if not geom1Data.isTrigger and not geom2Data.isTrigger:
            """
            Handle a typpical collision between two geoms of which none is a trigger.
            Create contact joint and the rest of the standard ODE stuff.
            """
            surfaceParams = OdeSurfaceParameters()

            surfaceParams.setMu(geom2Data.surfaceFriction)
            surfaceParams.setMu2(geom1Data.surfaceFriction)
            surfaceParams.setBounce(geom1Data.surfaceBounce)
            surfaceParams.setBounceVel(geom1Data.surfaceBounceVel)
            surfaceParams.setSlip1(geom1Data.surfaceSlip)
            surfaceParams.setSlip2(geom2Data.surfaceSlip)

            numContacts = entry.getNumContacts()
            if numContacts > 4:
                numContacts = 4
            for i in range(numContacts):
                if (geom1Data.name == "ground" or geom1Data.name == "door") and geom2Data.name == "ground": continue
                cgeom = entry.getContactGeom(i)

                contactPoint = entry.getContactPoint(i)

                contact = OdeContact()
                contact.setGeom(cgeom)
                contact.setFdir1(cgeom.getNormal())
                contact.setSurface(surfaceParams)
                #debug()
                if geom1Data.name == "charCapsule" or geom2Data.name == "charCapsule":
                    print "Contact between ", geom1.getBody(), geom2.getBody(), geom1Data.name, geom2Data.name
                contactJoint = OdeContactJoint(self.world, self.contactGroup, contact)
                contactJoint.attach(geom1.getBody(), geom2.getBody())

        """
        Collision callbacks for both objects
        Note that I also send the geomXData so the collisionCallback method must take 3 arguments.
        The reason I send that is because I think it's pointless to get it again from inside
        the callback, and it's simply very often needed.
        """
        if geom1Data.collisionCallback is not None:
            geom1Data.collisionCallback(entry, geom1Data, geom2Data)

        if geom2Data.collisionCallback is not None:
            geom2Data.collisionCallback(entry, geom1Data, geom2Data)

    def setGeomData(self, geom, data, object=None, kinematic=False):
        """
        A very important method. It's used for adding objects to the simulation
        so that they can benefit from the odeWorldManager features.
        """
        if data not in self.geomsData:
            """
            The data might be reused, so it's only added
            when it's not already in the list
            """
            self.geomsData.append(data)

        index = self.geomsData.index(data)
        """
        I use the OdeSpace's setSurfaceType to hold information about
        which geomData this specific geom uses.
        """
        self.space.setSurfaceType(geom, index)

        """
        Here you set how the object is meant to be handled in
        the simulation update task.

        For dynamic objects there is a dictionary of OdeGeom: NodePath
        form, because their updating is simply updating the pos
        and quat of the node path to track the geom.

        For kinematics there is a list, because there's only one
        value to store - the python object with an self.update(...)
        method. Kinematic objects can be updated in a variaty of ways
        depending on the need, so all the world manager cares about
        is whether they have the update method.
        """
        if object is None:
            return
        elif not kinematic:
            self.dynamics[geom] = object
        elif kinematic:
            self.kinematics.append(object)

    def addObject(self, obj):
        """ Takes an IsisObject and adds it as a dynamic or kinematic 
        object in the physics simulator """
        model = obj.model
        name = obj.name
        density = obj.density
        #obj.model.showBounds()
        def getOBB(collObj):
            ''' get the Oriented Bounding Box '''
            bounds=collObj.getTightBounds()
            box=bounds[1]-bounds[0]
            return [box[0],box[1],box[2]]
        bounds = getOBB(obj.model)
        h_bounds = bounds #[x/2.0 for x in bounds]
        boxNodepath = wireGeom().generate ('box', extents=h_bounds) 
        boxNodepath.reparentTo(obj)
        """
        Get the map's panda node. This will allow us to find the objects
        that the map consists of.
        """
        # find object's rotation
        objectGeom = OdeBoxGeom(self.space, *bounds) 
        objectBody = OdeBody(self.world)
        if density:
            M = OdeMass()
            M.setBox(density, *bounds)
            objectBody.setMass(M)
        # synchronize ODE geom's transformation according to the real object's

        objectGeom.setPosition(model.getPos(render))
        objectGeom.setQuaternion(model.getQuat(render))
        objectGeom.setCategoryBits(BitMask32.allOn())
        objectGeom.setCollideBits(BitMask32.allOn())
        #objectGeom.setCollideBits(THINGMASK)
        #objectGeom.setCategoryBits(THINGMASK)
        objectGeom.setBody(objectBody)
        #objectGeom.setOffsetPosition(Vec3(*offset))
        objData = odeGeomData()
        objData.name = name
        objData.surfaceFriction = 20.0
        #objData.collisionCallback = obj.collide
        self.setGeomData(objectGeom, objData, obj, False)#True)
        return objectGeom
        
        objectData = odeGeomData()
        objectData.name = name
        objectData.surfaceFriction = 2.0
        self.setGeomData(objectGeom, objectData, obj, True)
        objGeomData = OdeTriMeshData(model, True)
        objGeom = OdeTriMeshGeom(self.space, objGeomData)
        objGeom.setPosition(model.getPos(render))
        objgeom.setcategorybits(bitmask32.allon())
        objgeom.setcollidebits(bitmask32.allon())
        objGeom.setQuaternion(model.getQuat(render))
        objData = odeGeomData()
        objData.name = name
        objData.surfaceFriction = 2.0
        #objData.collisionCallback = obj.collide
        self.setGeomData(objGeom, objData, obj, True)
        return objGeom

    def destroyObject(self, objectToRemove):
        """
        Automatically destroy object and remove it from the worldManager
        """
        if objectToRemove in self.dynamics:
            objectToRemove.destroy()
            del self.dynamics[objectToRemove]
            return True
        elif objectToRemove in self.kinematics:
            idx = self.kinematics.index(objectToRemove)
            self.kinematics.pop(idx)
            return True
        return False

    def simulationTask(self, task):
        """
        As you can see, I do not use autoCollide here at all.
        Instead I only use the space's collide method pointing
        it to the handleCollisions callback.
        """
        self.space.collide("", self.handleCollisions)

        """
        And here we update the objects that take part in the simulation.
        """
        self.world.quickStep(self.stepSize)
        self.contactGroup.empty()

        for object in self.kinematics:
            """
            All kinematic objects (such as the KCC or, for example, door)
            must have an update method taking one argument. What happens
            inside that method is only up to you as the coder, the update
            method is the only requirement.
            """
            object.update(self.stepSize)

        for geom, nodePath in self.dynamics.iteritems():
            """
            The dynamic objects are updated in a more standard way,
            by setting the nodePath's position and rotation to the one
            of the geom, and thus of the body.
            """
            if not nodePath:
                continue
            pos = Vec3(geom.getPosition())
            quat = Quat(geom.getQuaternion())
            nodePath.setPosQuat(render, pos, quat)
        return task.again

    def setupGround(self, isisworld):
        cm = CardMaker("ground")
        groundTexture = loader.loadTexture("./textures/env_ground.jpg")
        cm.setFrame(-100, 100, -100, 100)
        groundNP = render.attachNewNode(cm.generate())
        groundNP.setTexture(groundTexture)
        groundNP.setPosHpr(0, 0, 0.0, 0, 0, 0)
        groundNP.lookAt(0, 0, -1)
        #groundNP.setTransparency(TransparencyAttrib.MAlpha)
        groundGeom = OdePlaneGeom(self.space, Vec4(0, 0, 1, 0))
        #groundGeom.setPos
        groundGeom.setCollideBits(FLOORMASK)
        groundGeom.setCategoryBits(FLOORMASK)
        groundData = odeGeomData()
        groundData.name = "ground"
        groundData.surfaceFriction = 20#OdeUtil.getInfinity()#20.0
        self.setGeomData(groundGeom, groundData, None)
        return
        """
        Get the map's panda node. This will allow us to find the objects
        that the map consists of.
        """
        isisworld.map = loader.loadModel("./models3/kitchen")
        isisworld.map.reparentTo(render)
        #isisworld.map.hide()
        isisworld.mapNode = isisworld.map.find("-PandaNode")
        isisworld.room = isisworld.mapNode.find("Wall")

        roomGeomData = OdeTriMeshData(isisworld.room, True)
        roomGeom = OdeTriMeshGeom(self.space, roomGeomData)
        roomGeom.setPosition(isisworld.room.getPos(render))
        roomGeom.setQuaternion(isisworld.room.getQuat(render))
        self.setGeomData(roomGeom, groundData, None)

        isisworld.steps = isisworld.mapNode.find("Steps")
        stepsGeomData = OdeTriMeshData(isisworld.steps, True)
        stepsGeom = OdeTriMeshGeom(self.space, stepsGeomData)
        stepsGeom.setPosition(isisworld.steps.getPos(render))
        self.setGeomData(stepsGeom, groundData, None)

        """
        Steps is yet another part of the map.
        Meant, obviously, to demonstrate the ability to climb stairs.
        """
        isisworld.steps = isisworld.mapNode.find("Steps")
        isisworld.map.flattenLight()
        isisworld.steps.flattenLight()
        isisworld.room.flattenLight()

    def stopPhysics(self,task=None):
        print "[IsisWorld] Stopping Physical Simulator"
        taskMgr.remove("ODE_simulationTask")
        #base.disableParticles()
        self._globalClock=ClockObject.getGlobalClock()
        self._globalClock.setMode(ClockObject.MSlave)

    def startPhysics(self, stopAt=None):
        """
        Here's another thing that's different than in the Panda Manual.
        I don't use the time accumulator to make the simulation run
        with a fixed time step, but instead I use the doMethodLater with
        task.again as the return value in self.simulationTask.

        This gave me better results than using the time accumulator method.
        """
        self.stepSize = 1.0/100.0
        if stopAt != None:
            assert stopAt > 0.0
            assert stopAt > self.stepSize # cannot step less than physical simulator
            taskMgr.doMethodLater(stopAt, self.stopPhysics, "ODE_simulationTaskEnder")
            # or can you 
            taskMgr.doMethodLater(min(self.stepSize,stopAt), self.simulationTask, "ODE_simulationTask")
        else:
            taskMgr.doMethodLater(self.stepSize, self.simulationTask, "ODE_simulationTask")

class explosion:
    """
    Explosion mechanics for ODE.

    To use it, just do:

    explosion(worldManager, Vec3(...))

    It will destroy itself once it's done.

    TODO - Explain more and make an example on the map
    """
    def __init__(self, worldManager, pos):
        self.worldManager = worldManager
        self.odeWorld = self.worldManager.world
        self.space = self.worldManager.space

        self.timeElapsed = 0.0
        self.speed = 2000.0
        self.force = 150.0
        self.currentForce = 0.0
        self.radius = 0.0

        self.collisions = []

        sphereData = odeGeomData()
        sphereData.name = "explosion"
        sphereData.isTrigger = True
        sphereData.collisionCallback = self.handleCollision

        self.sphere = OdeSphereGeom(self.worldManager.space, 0.0)
        self.sphere.setPosition(pos)

        self.worldManager.setGeomData(self.sphere, sphereData, self, False)#True)


    def handleCollision(self, entry, geom1Data, geom2Data):
        if entry.getGeom1() == self.sphere:
            geom = entry.getGeom2()
            geomData = geom2Data
        elif entry.getGeom2() == self.sphere:
            geom = entry.getGeom1()
            geomData = geom1Data
        else:
            return
        self.collisions.append([geom, entry.getContactGeom(0).getNormal(), entry.getContactPoint(0), geomData])

    def update(self, timeStep):
        self.timeElapsed += timeStep
        print "T", self.timeElapsed
        if self.timeElapsed > .1:
            self.worldManager.destroyObject(self)
            self.sphere.destroy()
            return

        force = self.force - self.sphere.getRadius()/10.0
        print "F", force

        for geom, normal, point, geomData in self.collisions:
            if geom.hasBody():
                #forceVector = (geom.getPosition() - self.sphere.getPosition()) * force
                forceVector = -normal * force
                geom.getBody().addForceAtPos(forceVector, point)
                print "force vector", forceVector
                if geomData.damageCallback:
                    geomData.damageCallback(100.0)

        self.radius += self.speed * self.timeElapsed**2
        print "R", self.radius
        self.sphere.setRadius(self.radius)

        print "\n"

        self.collisions = []
