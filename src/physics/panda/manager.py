from direct.showbase import DirectObject
from pandac.PandaModules import * # TODO: specialize
# initialize collision mask constants  
FLOORMASK = BitMask32.bit(1)      
WALLMASK = BitMask32.bit(2)
PICKMASK = BitMask32.bit(3)
AGENTMASK = BitMask32.bit(4)
OBJMASK= BitMask32.bit(5)
OBJFLOOR = BitMask32.bit(6)
OBJPICK = BitMask32.bit(7)

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
    
def getObjFromNP(np,tag="isisobj"):
    """ Helper function to get the Python object from a NodePath involved with 
    a collision entry, using a tag """
    if np.hasPythonTag(tag):
        return np.getPythonTag(tag)
    else:
        p = np.getParent()
        if p.hasPythonTag(tag):
            return p.getPythonTag(tag)
        else:
            return np

class PhysicsWorldManager(DirectObject.DirectObject):
    
    def __init__(self):
        """ Initialize the 3 Collision Handlers and the base Traverser, which looks
        through the entire node path. 
        
        Future optimization: traversers that only look at certain branches of the render tree.
        """
        self._GlobalClock=ClockObject.getGlobalClock() 
        globalClock.setMode(ClockObject.MLimited) 
        globalClock.setFrameRate(20)
        #self._FrameTime=self._GlobalClock.getFrameTime() 
        #self._GlobalClock.setRealTime(self._FrameTime) 
        
               
        self.stepping = False
        # keep track of all agents
        self.agents = []
     
        if False:
            base.enableParticles()
            self.cHandler = PhysicsCollisionHandler()
            gravityFN = ForceNode('gravity')
            gravityNP = render.attachNewNode(gravityFN)
            gravityForce = LinearVectorForce(0, 0, -9.81)
            gravityFN.addForce(gravityForce)
            base.physicsMgr.addLinearForce(gravityForce)  

        # Initialize the collision traverser.
        base.cTrav = CollisionTraverser()
        base.cTrav.setRespectPrevTransform(True)
        

        # initialize 3 handlers: wall, gravity, and other events
        
        # the CollisionHandlerPusher is good for keeping items from going through walls
        self.cWall = CollisionHandlerFluidPusher()
        self.cWall.setHorizontal(True)
        # this tracks the velocity of moving objects, whereas CollisionHandlerFloor doesnt
        self.cFloor = CollisionHandlerGravity()
        # gravity should be -9.81m/s, but that doesn't quite work
        self.cFloor.setGravity(9.81*50)
        self.cFloor.setOffset(.2)
        self.cFloor.setMaxVelocity(1)
        self.cFloor.addInPattern('into')

        # Initialize the handler.
        base.cEvent = CollisionHandlerEvent()
        base.cEvent.addInPattern("%fn-into-%(container)it")
        base.cEvent.addInPattern("%fn-into-%(surface)it")
        base.cEvent.addInPattern('%fn-into-%in')
        base.cEvent.addOutPattern("%fn-outof-%(container)it")
        base.cEvent.addOutPattern("%fn-outof-%(surface)it")
        base.cEvent.addOutPattern('%fn-outof-%in')
       
        # initialize listeners
        base.accept('object-into-acontainer', self._enterContainer)
        base.accept('object-outof-acontainer', self._exitContainer)
        base.accept('object-into-asurface', self._exitSurface)
        base.accept('object-outof-asurface', self._exitSurface)
        #base.accept('object-into-object', self._objCollisionHandlerIn)
        #base.accept('object-outof-object', self._objCollisionHandlerOut)
        base.accept('agent-into-object', self._agentCollisionHandlerIn)
        base.accept('agent-into-agent', self._agentsCollisionIn)

        # start it up 
        self.paused = False 
        self._startPhysics()


    def _enterContainer(self, entry):
        """ When an object enters into a container. """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterContainer(cInto)
        print "Entering container %s, %s" % (cFrom, cInto)

    def _exitContainer(self, entry):
        """ When an object exits a container."""
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterContainer(cInto)
        print "Exiting container %s, %s" % (cFrom, cInto)

    def _enterSurface(self, entry):
        """ When an object collides with another object's surface plane. """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterSurface(cInto)
        print "Entering surface %s, %s" % (cFrom, cInto)

    def _exitSurface(self, entry):
        """ When an object ceases to collide with another object's surface plane. """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        cInto.enterSurface(cInto)
        print "Exiting surface %s, %s" % (cFrom, cInto)

    def _objCollisionHandlerIn(self, entry):
        """ The general case when two objects collide"""
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        if hasattr(cInto,'enterContainer'):
            cInto.enterContainer(cInto)
        print "Object In Collision: %s, %s" % (cFrom, cInto)
    
    def _objCollisionHandlerOut(self, entry):
        """ The general caase when two objects cease to collide """
        cFrom = getObjFromNP(entry.getFromNodePath(),"isisobj")
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        if hasattr(cInto,'exitContainer'):
            cInto.exitContainer(cInto)
        print "Object Out Collision: %s, %s" % (cFrom, cInto)

    def _agentCollisionHandlerIn(self, entry):
        """ When an agent collides with a container object. """
        agent = entry.getFromNodePath().getParent()
        cInto = getObjFromNP(entry.getIntoNodePath(),"isisobj")
        if hasattr(cInto,'enterContainer'):
            cInto.enterContainer(agent)
        print "Agent In Collision: %s, %s" % (agent, cInto)

    def _agentsCollisionIn(self, entry):
        """ When two agents collide with each other. """
        agentFrom = entry.getFromNodePath().getParent()
        agentInto = entry.getIntoNodePath().getParent()
        print "Agents collided : %s, %s" % (agentFrom, agentInto) 

    def addAgent(self,agent):
        self.agents.append(agent)
        
    def stepSimulation(self,stepTime=1):
        if self.paused:
            self.togglePaused(stepTime)
        else:
            print "Error, cannot step while simulator is running"
 
    def pause(self):
         if not self.paused: 
             self._stopPhysics()
             #self._GlobalClock.setMode(ClockObject.MSlave)
             self.paused = True

    def resume(self):
        if self.paused: 
            #self._GlobalClock.setMode(ClockObject.MNormal) 
            #base.enableParticles()
            #base.particleMgrEnabled = 0 
            print "[IsisWorld] Resuming Simulator"
            self._startPhysics(None)
            self.paused = False

    def togglePaused(self,stepTime=None):
        if self.paused: 
            #self._GlobalClock.setMode(ClockObject.MNormal) 
            #base.enableParticles()
            #base.particleMgrEnabled = 0 
            print "[IsisWorld] Resuming Simulator"
            self._startPhysics(stepTime)
        else:
            self._stopPhysics()
            #self._GlobalClock.setMode(ClockObject.MSlave)
        # only untoggle bit if pause is called, not step
        if stepTime == None:
            self.paused = not self.paused

    def simulationTask(self, task):
        dt = self._GlobalClock.getDt()
        for agent in self.agents:
            agent.update(dt) 
        return task.cont 
    
    def _stopPhysics(self,task=None):
        print "[IsisWorld] Stopping Physical Simulator"
        taskMgr.remove("physics-SimulationTask")
        self.stepping = False
        #base.disableParticles() 


    def _startPhysics(self, stopAt=None):
        if stopAt != None:
          assert stopAt > 0.0
          taskMgr.doMethodLater(stopAt, self._stopPhysics, "physics-SimulationStopper", priority=10)
          # or can you
          self.stepping = True 
          taskMgr.add(self.simulationTask, "physics-SimulationTask", priority=10)
        else:
          taskMgr.add(self.simulationTask, "physics-SimulationTask", priority=10)


