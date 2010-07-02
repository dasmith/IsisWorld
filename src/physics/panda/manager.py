from direct.showbase import DirectObject
from pandac.PandaModules import * # TODO: specialize
# initialize collision mask constants  
FLOORMASK = BitMask32.bit(0)      
WALLMASK = BitMask32.bit(2)
PICKMASK = BitMask32.bit(3)
AGENTMASK = BitMask32.bit(4)

def getOrientedBoundedBox(collObj):
    ''' get the Oriented Bounding Box '''
    # save object's parent and transformation
    parent=collObj.getParent()
    trans=collObj.getTransform()
    # ODE need everything in world's coordinate space,
    # so bring the object directly under render, but keep the transformation
    collObj.wrtReparentTo(render)
    # get the tight bounds before any rotation
    collObj.setHpr(0,0,0)
    bounds=collObj.getTightBounds()
    offset=collObj.getBounds().getCenter()-collObj.getPos()
    # bring object to it's parent and restore it's transformation
    collObj.reparentTo(parent)
    collObj.setTransform(trans)
    # (max - min) bounds
    box=bounds[1]-bounds[0]
#        print bounds[0], bounds[1]
    return [box[0],box[1],box[2]], [offset[0],offset[1],offset[2]]
    
    
class PhysicsWorldManager(DirectObject.DirectObject):
    
    def __init__(self):
        
        self.paused = True
        self._stopPhysics()
        # number of times per second to run the physical simulator
        self.stepSize = 1.0/50
        
        # keep track of all agents
        self.agents = []
        # Initialize the collision traverser.
        base.cTrav = CollisionTraverser()
        base.cTrav.showCollisions( render )
        # Initialize the handler.
        base.cEvent = CollisionHandlerEvent()
        base.cEvent.addInPattern('into-%in')
        base.cEvent.addOutPattern('outof-%in')
        
        # enable the physics manager (and the particle manager...) and 
        # add base.updateManagers to the task manager in ShowBase. 
        # This causes base.physicsMgr.doPhysics(dt) to be called each frame 
        base.enableParticles() 
        # we don't actually care about particles, so disable them again. 
        base.particleMgrEnabled = 0
        
        gravityFN = ForceNode('gravity')
        gravityNP = render.attachNewNode(gravityFN)
        gravityForce = LinearVectorForce(0, 0, -9.81)
        gravityFN.addForce(gravityForce)
        base.physicsMgr.addLinearForce(gravityForce)

        
    
    def addAgent(self,agent):
        self.agents.append(agent)

    def setupGround(self):
        # First we create a floor collision plane.
        floorNode = render.attachNewNode("Floor NodePath")
        # Create a collision plane solid.
        collPlane = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0)))
        # Call our function that creates a nodepath with a collision node.
        floorCollisionNP = self.makeCollisionNodePath(floorNode, collPlane)
        # Get the collision node the Nodepath is referring to.
        floorCollisionNode = floorCollisionNP.node()
        # The floor is only an into object, so just need to set its into mask.
        floorCollisionNode.setIntoCollideMask(BitMask32.allOff() | AGENTMASK | FLOORMASK)
        
        
    def stepSimulation(self,stepTime=1):
        if self.paused:
            self.togglePaused(stepTime)
        else:
            print "Error, cannot step while simulator is running"
        
    def togglePaused(self,stepTime=None):
        if self.paused: 
            self._GlobalClock.setRealTime(self._FrameTime) 
            self._GlobalClock.setMode(ClockObject.MNormal) 
            base.enableParticles()
            base.particleMgrEnabled = 0 
            self._GlobalClock=None 
            print "[IsisWorld] Restarting Simulator"
            self._startPhysics(stepTime)
        else:
            self._stopPhysics()
        # only untoggle bit if pause is called, not step
        if stepTime == None:
            self.paused = not self.paused

    def _stopPhysics(self,task=None):
        print "[IsisWorld] Stopping Physical Simulator"
        taskMgr.remove("physics-SimulationTask")
        base.disableParticles() 
        self._GlobalClock=ClockObject.getGlobalClock() 
        self._FrameTime=self._GlobalClock.getFrameTime() 
        self._GlobalClock.setMode(ClockObject.MSlave)

    def simulationTask(self, task):
        for agent in self.agents:
            agent.update(self.stepSize) 
        return task.cont 

    def _startPhysics(self, stopAt=None):
        """
        Here's another thing that's different than in the Panda Manual.
        I don't use the time accumulator to make the simulation run
        with a fixed time step, but instead I use the doMethodLater with
        task.again as the return value in self.simulationTask.

        This gave me better results than using the time accumulator method.
        """
        if stopAt != None:
          assert stopAt > 0.0
          assert stopAt > self.stepSize # cannot step less than physical simulator
          taskMgr.doMethodLater(stopAt, self._stopPhysics, "physics-SimulationStopper")
          # or can you 
          taskMgr.doMethodLater(min(self.stepSize,stopAt), self.simulationTask, "physics-SimulationTask")
        else:
          taskMgr.doMethodLater(self.stepSize, self.simulationTask, "physics-SimulationTask")



class PhysicsCharacterController(object):
    
    def __init__(self, worldManager):
        # make sure parent node is off
        import random
        self.rootNode.setCollideMask(BitMask32.allOff())
        x = random.randint(0, 10)
        y = random.randint(0, 10)
        z = random.randint(0, 10)
        self.actor.setPos(x, y, z)
        self.avatarRadius = 0.8        
        offsetNodeOne = [x, 0 + y, 0.5 + z, 0.5]
        offsetNodeTwo = [x, 0 + y, 1.6 + z, 0.5]
        # collision tubes have not been written as good FROM collidemasks
        # to make the person tall, but not wide we use three collisionspheres
        centerHeight = 0.8
        self.avatarViscosity = 0
        self.cNode = CollisionNode('collisionNode')
        self.cNode.addSolid(CollisionSphere(0.0, 0.0, centerHeight, self.avatarRadius))
        self.cNode.addSolid(CollisionSphere(0.0, 0.0, centerHeight + 2 * self.avatarRadius, self.avatarRadius))
        self.cNode.setFromCollideMask(BitMask32.allOn())
        self.cNode.setIntoCollideMask(BitMask32.allOff() | AGENTMASK)
        self.cNode.setTag('agent', 'agent')
        self.cNodePath = self.actor.attachNewNode(self.cNode)
        self.cNodePath.show()
        self.priorParent, self.actorNodePath, self.acForce = worldManager.addActorPhysics(self)



def getCapsuleSize(collobj, radius=1):
    bounds = collobj.getTightBounds()
    # (max - min) bounds
    return [bounds[0][0], bounds[0][1], bounds[0][2], bounds[1][0], bounds[1][1], bounds[1][2], radius]
