from pandac.PandaModules import OdeCappedCylinderGeom, OdeRayGeom, Vec3, BitMask32, Quat
import utils
from ODEWireGeom import *

class PhysicsCharacterController:
    def __init__(self, worldManager):

        self.worldManager = worldManager
        self.world = self.worldManager.world
        self.space = self.worldManager.space

        boundingBox, offset = utils.getOrientedBoundingBox(self.actor)
        self.radius =  boundingBox[0]/3.0
        low, high = self.actor.getTightBounds()
        self.walkLength = high[2]-low[2]
    

        self.walkLevitation = self.walkLength - self.radius 
        self.crouchLength = .1
        self.crouchLevitation = 1.2
        self.length = self.walkLength
        self.levitation = self.walkLevitation
        self.capsuleGeom = OdeCappedCylinderGeom(self.space, self.radius, self.length- self.radius*2.0)
        self.worldManager.addAgent(self.capsuleGeom, self)
        #self.worldManager.addCollisionCallback(self.capsuleGeom, self.capsuleCollision)

        #self.capsuleGeom.setCollideBits(BitMask32.bit(1))
        self.cylinderNodepath = wireGeom().generate ('cylinder', radius=self.radius, length=self.length- self.radius*2.0) 
        self.cylinderNodepath.reparentTo(self.actor)
        #self.capsuleGeom.setOffsetPosition(0,0,1.7)
        self.offsetVec = Vec3(*offset)
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

        self.setCollideBits(BitMask32.allOn())
        self.setCategoryBits(BitMask32.allOn())#BitMask32(0x0000111))
        self.worldManager.addCollisionCallback(self.footRay, self.footCollision)
     
        #self.capsuleGeom.setCollideBits(BitMask32.allOn())
        """
        The geomData for the footRay. Note that I don't set any of the
        typpically ODE stuff here (friction and the like) because it's not needed.

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
        self.actor.setPos(pos-self.offsetVec)

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

    def handleCollision(self, entry, geom1Data, geom2Data):
        print "Handlin'", geom1Data.name, geom2Data.name
        self.capsuleCollision(entry, geom1Data, geom2Data)

    def capsuleCollision(self, entry, geom1Data, geom2Data):
        if not entry.getNumContacts():
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
        print entry.getGeom1(), entry.getGeom2()
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
                """
                Move the character away from the object it collides with to prevent
                penetrating it. ODE itself won't do that because the capsule
                is not a body.

                I move it slightly less than the returned penetration depth because
                I found the character to shake less this way.

                Note that the direction of movement is dependant on which object
                in the collision process our character happens to be.
                """
                if geom1Data is self:
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

        #  This will become the new position for our character.
        newPos = self.currentPos

        if self.state == "jumping":
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
            print "height 2"
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
        self.actor.setPos(newPos-self.offsetVec)
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
        # Time elapsed since the beginning of the jump
        self.jumpTime += stepSize

        """
        Fall speed might be used to calculate how hard we hit the ground
        for character health.
        """
        self.fallSpeed = self.jumpSpeed*self.jumpTime + (-9.81)*(self.jumpTime)**2
        
        np = self.jumpStartPos + self.fallSpeed

        if highestEntry and np <= highestEntry.getContactPoint(0)[2] + self.levitation:
            self.state = "ground"
            print "Jump1"
            return highestEntry.getContactPoint(0)[2] + self.levitation
        else:
            print "Jump2"
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
        print "jumping", self.state
        #if self.state != "ground":
        #    return
        self.jumpSpeed = 8.0
        self.jumpStartPos = self.capsuleGeom.getPosition()[2]
        self.jumpTime = 0.0
        self.state = "jumping"

