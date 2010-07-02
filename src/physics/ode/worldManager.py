from direct.showbase.DirectObject import DirectObject
from direct.showbase.InputStateGlobal import inputState
from pandac.PandaModules import TransparencyAttrib,GeomVertexReader,GeomVertexFormat,GeomVertexData,Geom,GeomVertexWriter,GeomTriangles,GeomNode
from pandac.PandaModules import Vec3,Vec4,Point3
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdeSpace, OdeBallJoint, OdeHinge2Joint, OdeQuadTreeSpace, OdeHashSpace
from pandac.PandaModules import OdeBody, OdeMass, OdeSphereGeom, OdeBoxGeom, OdePlaneGeom, OdeCylinderGeom, OdeCappedCylinderGeom, OdeTriMeshGeom, OdeTriMeshData
from pandac.PandaModules import BitMask32, Quat, Mat4, CollisionTraverser, CollisionHandlerQueue
from pandac.PandaModules import * # TODO: specify me

import utils
from object import PhysicsObjectController

FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)
PICKMASK = BitMask32.bit(2)
AGENTMASK = BitMask32.bit(3)
THINGMASK = BitMask32.bit(4)

class Wall():
    def __init__(self, box, dims, room, world, space):
        x,y,z,sx,sy,sz = dims 
        self.model = box.copyTo(room)
        self.model.setPos(x,y,z)
        self.model.setScale(sx,sy,sz)
        boundingBox, offset = utils.getOrientedBoundingBox(self.model)
        self.geom = OdeBoxGeom(space, *boundingBox)
        self.geom.setCollideBits(BitMask32.bit(1))
        self.geom.setCategoryBits(BitMask32.bit(1))
        space.setSurfaceType(self.geom, 1)
        self.body = OdeBody(world)
        mass = OdeMass()
        mass.setBoxTotal(100, *boundingBox)
        self.body.setPosition(self.model.getPos(render))
        self.body.setQuaternion(self.model.getQuat(render))
        self.body.setMass(mass)
        #self.geom.setBody(self.body)
        #self.geom.setOffsetPosition(*offset)
        self.name = "Wall"

    def update(self,step=1):
        pass

    def isDynamic(self):
        return False

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
    
        if base.cTrav == 0:
            self.traverser = CollisionTraverser("collision_traverser")
            self.queue = CollisionHandlerQueue()
            self.traverser.addCollider
            base.cTrav = self.traverser
        else:
            self.traverser = base.cTrav
            self.traverser.clearColliders()
        
        # Setup the physics world
        self.world = OdeWorld()
        # Create a space and add a contactgroup to it to add the contact joints
        self.space = OdeHashSpace()
        self.space.setLevels(0,0)
        self.space.setAutoCollideWorld(self.world)
        self.contactGroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactGroup)
        self.space.setCollisionEvent("collision")
        
        self.world.setGravity(0.0, 0.0, -35)
        #self.world.setGravity(0.0, 0.0, -9.81)

        # Surface IDs: 0 - ground 1 - objects 2 - actors
        self.world.initSurfaceTable(3)
        self.world.setSurfaceEntry(0, 1, 1.0, 0.3, 7, 0.9, 0.00001, 0.0, 0.01)
        self.world.setSurfaceEntry(1, 1, 1.0, 0.3, 7, 0.9, 0.00001, 0.0, 0.01)
        self.world.setSurfaceEntry(1, 2, 1.0, 0.3, 7, 0.9, 0.00001, 0.0, 0.01)
        self.world.setSurfaceEntry(0, 2, 10.0, 0.3, 7, 0.9, 0.00001, 0.0, 0.01)
        self.world.setSurfaceEntry(2, 2, 0.2, 0.3, 7, 0.9, 0.00001, 0.0, 0.01)
        self.world.setSurfaceEntry(0, 0, 1.0, 0.3, 7, 0.9, 0.00001, 0.0, 0.01)
        # Setup the physics world...
        erp = 0.8
        cfm = 1e-4
        slip = 0.0
        dampen = 0.01

        self.world.setCfm(cfm)
        self.world.setErp(erp)
        self.world.setContactSurfaceLayer(.001)
        self.world.setAutoDisableFlag(True)
        self.world.setAutoDisableAngularThreshold(0.5)
        self.world.setAutoDisableLinearThreshold(0.5)
    
        self.agents = dict()
        self.kinematic = dict() # id(func) -> nodepath 

        self.geomToID = dict() # id(func) -> func
        self.preCollide = dict() # id(func) -> func
        self.postCollide = dict()

        # Create the damping database - damps objects so that they slow down over time, which is very good for stability...
        self.damping = dict() # id(body) -> (body,amount)

        # Run at 1/X, where X is frames per second.
        self.stepSize = 1.0 / 40.0

        self.FRAME_RATE = FRAME_RATE
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
            # throttle frame rate
            self._globalClock.setFrameRate(self.FRAME_RATE)
            #self._globalClock=None
            self.startPhysics(stepTime)
        else:
            self.stopPhysics()
        # only untoggle bit if pause is called, not step
        if stepTime == None:
            self.paused = not self.paused


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

            
    def handleCollisions(self, entry):
        geom1 = entry.getGeom1()
        geom2 = entry.getGeom2()
        #print str(geom1), str(geom2)
        id1 = int(str(geom1).split(" ")[-1].rstrip(")"), 16)
        id2 = int(str(geom2).split(" ")[-1].rstrip(")"), 16)
        if id1 in self.geomToID.keys() and id2 in self.geomToID.keys():
            geom1data = self.geomToID[id1]
            geom2data = self.geomToID[id2]
            if hasattr(geom1data, 'handleCollision'):
                geom1data.handleCollision(entry, geom1data, geom2data)
            if hasattr(geom2data, 'handleCollision'):
                geom2data.handleCollision(entry, geom1data, geom2data)
        if id1 in self.postCollide:
            func = self.postCollide[id1]
            func(entry,geom1,geom2)
        if id2 in self.postCollide:
            func = self.postCollide[id2]
            func(entry,geom1,geom2)
    
    
    def addCollisionCallback(self, obj, func):
        """ Stores a collision callback for objects that can be any arbitrary function, such as for a Ray object
        that does not have a collision body nor a deligated response to collisions (nor should it prompt one on 
        the receiving object) so it shouldn't be registered in PhysicsWorldManager._trackGeom """
        if hasattr(obj, 'geom'):
            print "ODE GEOM", str(obj)
            if str(obj.geom).split(" ")[-1] == '': 
                print "could not add callback", obj 
                return
            id = int(str(obj.geom).split(" ")[-1].rstrip(")"), 16)
        else:
            print "ODE GEOM", str(obj)
            if str(obj).split(" ")[-1] == '': 
                print "could not add callback", obj 
                return
            id = int(str(obj).split(" ")[-1].rstrip(")"), 16)
        self.postCollide[id] =  func

    def addObject(self, obj):
        """ Registers an object to be tracked and maintained by the Ode World """
        self.kinematic[obj.geom] = obj
        self._trackGeom(obj.geom, obj)
    
    def addAgent(self, geom, agent):
        self.agents[geom] = agent
        self._trackGeom(geom, agent)

    def _trackGeom(self, odeGeom, node):
        print "ODE GEOM", str(odeGeom)
        if str(odeGeom).split(" ")[-1] == '': 
            print "could not add", node
            return
        id = int(str(odeGeom).split(" ")[-1].rstrip(")"), 16)
        self.geomToID[id] = node 

    def makeRoom(self, node,box,odeworld,collideBits,categoryBits,minpos,maxpos,thickness,sides=4):
        # make a rectangular room using boxes
        def MakeRoomBoxes(minpos, maxpos, thickness):
            # six pieces
            xmid = (maxpos[0] + minpos[0]) / 2
            ymid = (maxpos[1] + minpos[1]) / 2
            zmid = (maxpos[2] + minpos[2]) / 2
            xl = (maxpos[0] - minpos[0])
            yl = (maxpos[1] - minpos[1])
            zl = (maxpos[2] - minpos[2])
            return [
                [maxpos[0]+thickness/2,ymid,zmid,thickness,yl,zl],
                [minpos[0]-thickness/2,ymid,zmid,thickness,yl,zl],
                [xmid, ymid, maxpos[2]+thickness/2, xl, yl, thickness],
                [xmid, ymid, minpos[2]-thickness/2, xl, yl, thickness],
                [xmid, maxpos[1]+thickness/2, zmid, xl, thickness, zl],
                [xmid, minpos[1]-thickness/2, zmid, xl, thickness, zl],
            ]

        boxes = MakeRoomBoxes(minpos,maxpos,thickness)
        room = node.attachNewNode("roomwalls")
        objlist=[]
        for i in range(sides):
            dims = boxes[i]
            wall = Wall(box, dims, room, self.world, self.space)
            # wall.model.removeNode()
            self.addObject(wall)
            objlist.append(wall)
        return room,objlist

    def setupGround(self, isisworld):

        cm = CardMaker("ground")
        groundTexture = loader.loadTexture("media/textures/env_ground.jpg")
        cm.setFrame(-100, 100, -100, 100)
        cm.setUvRange((0, 1), (1, 0)) 
        groundNP = render.attachNewNode(cm.generate())
        groundNP.setTexture(groundTexture)
        groundNP.setPos(0, 0, 0); groundNP.lookAt(0, 0, -1) 
        groundGeom = OdePlaneGeom(self.space, Vec4(0, 0, 1, 0))
        groundGeom.setCollideBits(BitMask32.bit(1))
        groundGeom.setCategoryBits(BitMask32.bit(1))
        self.space.setSurfaceType(groundGeom, 1)

        return
        #box = loader.loadModel("media/models/box")
        #self.makeRoom(render,box,self.world, 1,1, [-20.0,-20.0,0.2], [20.0,20.0,30.0], 5.0, 5)
        """
        Get the map's panda node. This will allow us to find the objects
        that the map consists of.
        """
        isisworld.map = loader.loadModel("media/models/kitchen")
        isisworld.map.reparentTo(render)
        #isisworld.map.hide()
        isisworld.mapNode = isisworld.map.find("-PandaNode")
        isisworld.room = isisworld.mapNode.find("Wall")

        roomGeomData = OdeTriMeshData(isisworld.room, True)
        roomGeom = OdeTriMeshGeom(self.space, roomGeomData)
        roomGeom.setPosition(isisworld.room.getPos(render))
        roomGeom.setQuaternion(isisworld.room.getQuat(render))
        roomGeom.setCollideBits(BitMask32.bit(1))
        roomGeom.setCategoryBits(BitMask32.bit(1))

        isisworld.steps = isisworld.mapNode.find("Steps")
        stepsGeomData = OdeTriMeshData(isisworld.steps, True)
        stepsGeom = OdeTriMeshGeom(self.space, stepsGeomData)
        stepsGeom.setPosition(isisworld.steps.getPos(render))
        stepsGeom.setCollideBits(BitMask32.bit(1))
        stepsGeom.setCategoryBits(BitMask32.bit(1))
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
        self._globalClock=ClockObject.getGlobalClock()
        self._globalClock.setMode(ClockObject.MSlave)

    def simulationTask(self, task):
        self.space.autoCollide()
        self.world.quickStep(self.stepSize)
        self.contactGroup.empty()
        # collision traverser
        self.traverser.traverse(render)
        for i in range(self.queue.getNumEntries()):
            entry = self.queue.getEntry(i)
            fromName = entry.getFromNodePath().getName()
            intoName = entry.getFromNodePath().getName()
            print fromName, intoName
        # update agents objects
        for agent in self.agents.values():
            agent.update(self.stepSize)
        for obj in self.kinematic.values(): 
            if True:# obj.isDynamic():
                # update based on body position
                obj.update(self.stepSize)
        return task.cont 

    def startPhysics(self, stopAt=None):
        """
        Here's another thing that's different than in the Panda Manual.
        I don't use the time accumulator to make the simulation run
        with a fixed time step, but instead I use the doMethodLater with
        task.again as the return value in self.simulationTask.

        This gave me better results than using the time accumulator method.
        """
        base.accept("collision",self.handleCollisions)
        print "starting physics"
        if stopAt != None:
            assert stopAt > 0.0
            assert stopAt > self.stepSize # cannot step less than physical simulator
            taskMgr.doMethodLater(stopAt, self.stopPhysics, "ODE_simulationTaskEnder")
            # or can you 
            taskMgr.doMethodLater(min(self.stepSize,stopAt), self.simulationTask, "ODE_simulationTask")
        else:
            taskMgr.doMethodLater(self.stepSize, self.simulationTask, "ODE_simulationTask")
