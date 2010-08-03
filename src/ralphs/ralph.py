import direct.directbase.DirectStart 
from direct.showbase.DirectObject import DirectObject 
from direct.actor.Actor import Actor 
from direct.task import Task 

from direct.controls.ControlManager import CollisionHandlerRayStart
from pandac.PandaModules import CollisionTraverser 
from pandac.PandaModules import ActorNode

from direct.showbase import DirectObject
from direct.interval.IntervalGlobal import *
from direct.actor.Actor import Actor
from direct.gui.DirectGui import DirectLabel
#from direct.controls.GravityWalker import GravityWalker
from pandac.PandaModules import *# PandaNode,NodePath,Camera
#from panda3d.core import CollisionHandlerPusher, CollisionHandlerGravity, CollisionTraverser
import math, random
from time import time
# project stuff
from ..actions.actions import *
from ..physics.panda.manager import *

def frange(x,y,inc):
    """ Floating point xrange """
    while x <= y:
        if x < 0:
            yield -(abs(x)**2)
        else:
            yield x**2
        x += inc


class Ralph(DirectObject.DirectObject):
    
    def __init__(self, physicsManager, agentSimulator, name, queueSize = 100):

        # setup the visual aspects of ralph
        self.actor= Actor("media/models/boxman",{"walk":"media/models/boxman-walk", "idle": "media/models/boxman-idle"})
        self.actor.setScale(1.0)
        self.actor.setH(0)

        self.actor.setColorScale(random.random(), random.random(), random.random(), 1.0)
        self.actorNode = ActorNode('physicsControler-%s' % name)
        self.actorNodePath = NodePath('agent-%s' % name)
        self.actorNodePath.attachNewNode(self.actorNode)
        #self.actorNode = self.actorNodePath.node()
        self.actorNodePath.reparentTo(render)
        self.actor.setPos(self.actorNodePath,0,0,-.2)
        self.actor.reparentTo(self.actorNodePath)
        self.actor.setCollideMask(BitMask32.allOff())
        self.name = name
        self.isMoving = False
        
        boundingBox, offset = getOrientedBoundedBox(self.actor)
        self.radius = boundingBox[0]/2.0
        low, high = self.actor.getTightBounds()
        self.height = high[0]-low[0]

        DirectObject.DirectObject.__init__(self) 
        self.agent_simulator = agentSimulator
        self.physicsManager = physicsManager    
        #x = random.randint(0,10)
        #y = random.randint(0,10)
        #z = random.randint(12,25)
        #self.actorNodePath.setFluidPos(Vec3(x,y,z))
        
        self.setupCollisionSpheres()

    
        self.actor.makeSubpart("arms", ["LeftShoulder", "RightShoulder"])    
        
        # Expose agent's right hand joint to attach objects to
        self.player_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'Hand.R')
        self.player_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'Hand.L')

        #if name == "Lauren":
        #    toaster = loader.loadModel("media/models/toaster")
        #    toaster.setScale(0.7)
        #    toaster.setPos(0,0,0)
        #    toaster.reparentTo(self.player_right_hand)
        #    toaster.setPos(Vec3(.2,0,.6))
        #    toaster.place()
        #toaster.setPos(1,0.4,0)


        self.player_right_hand.setColorScaleOff()
        self.player_left_hand.setColorScaleOff()
        self.player_head  = self.actor.exposeJoint(None, 'modelRoot', 'Head')
        self.neck = self.actor.controlJoint(None, 'modelRoot', 'Head')

        self.controlMap = {"turn_left":0, "turn_right":0, "move_forward":0, "move_backward":0, "move_right":0, "move_left":0,\
                           "look_up":0, "look_down":0, "look_left":0, "look_right":0, "jump":0}
        # see update method for uses, indices are [turn left, turn right, move_forward, move_back, move_right, move_left]
        # turns are in degrees per second, moves are in units per second
        self.speeds = [270, 270, 5, 5, 5, 5]

        self.originalPos = self.actor.getPos()

        # ray for pointing at things
        self.aimRay = None
        self.aimed = None

    
        self.right_hand_holding_object = False
        self.left_hand_holding_object  = False

        # speech bubble
        self.last_spoke = 0
        self.speech_bubble=DirectLabel(parent=self.actor, text="", text_wordwrap=10, pad=(3,3),\
                       relief=None, text_scale=(.3,.3), pos = (0,0,3.6), frameColor=(.6,.2,.1,.5),\
                       textMayChange=1, text_frame=(0,0,0,1), text_bg=(1,1,1,1))
        # stop the speech bubble from being colored like the agent
        self.speech_bubble.setColorScaleOff()
        self.speech_bubble.component('text0').textNode.setCardDecal(1)
        self.speech_bubble.setBillboardAxis()
        
        # put a camera on ralph
        self.fov = NodePath(Camera('RaphViz'))
        
        # position the camera to be infront of Boxman's face.
        self.fov.reparentTo(self.player_head)
        # x,y,z are not in standard orientation when parented to player-Head
        self.fov.setPos(0, 0.2, 0)
        # if P=0, canrea is looking directly up. 90 is back of head. -90 is on face.
        self.fov.setHpr(0,-90,0)

        lens = self.fov.node().getLens()
        lens.setFov(60) #  degree field of view (expanded from 40)
        lens.setNear(0.2)
        #self.fov.node().showFrustum() # displays a box around his head
        #self.fov.place()
 
        self.prevtime = 0
        self.current_frame_count = 0

        #self.name = "Ralph"
        self.isSitting = False
        self.isDisabled = False
        self.msg = None
        self.actorNodePath.setPythonTag("agent", self)

        """
        Object used for picking objects in the field of view
        """
        self.picker = Picker(self.fov, self)

        # Initialize the action queue, with a maximum length of queueSize
        self.queue = []
        self.queueSize = queueSize
        self.lastSense = 0
        
        # when you're done, register yourself with physical simulator
        # so it can call update() at each step of the physics
        self.physicsManager.addAgent(self)


    def setControl(self, control, value):
        """Set the state of one of the character's movement controls.  """
        self.controlMap[control] = value
    
    def getObjectsInFieldOfVision(self):
        """ This works in an x-ray vision style. Fast"""
        objects = {}
        for obj in base.render.findAllMatches("**/IsisObject*"):
            if not obj.hasPythonTag("isisobj"):
                continue
            o = obj.getPythonTag("isisobj")
            bounds = o.activeModel.getBounds() 
            bounds.xform(o.activeModel.getMat(self.fov))
            if self.fov.node().isInView(o.activeModel.getPos(self.fov)):
                pos = o.activeModel.getPos(render)
                pos = (pos[0], pos[1], pos[2]+o.getHeight()/2)
                p1 = self.fov.getRelativePoint(render,pos)
                p2 = Point2()
                self.fov.node().getLens().project(p1, p2)
                p3 = aspect2d.getRelativePoint(render2d, Point3(p2[0], 0, p2[1]) )
                object_dict = {'x_pos': p3[0],\
                               'y_pos': p3[2],\
                               'distance':o.activeModel.getDistance(self.fov), \
                               'orientation': o.activeModel.getH(self.fov)}
                objects[o] = object_dict
        self.control__say("If I were wearing x-ray glasses, I could see %i items"  % len(objects)) 
        return objects

    def getAgentsInFieldOfVision(self):
        """ This works in an x-ray vision style as well"""
        agents = {}
        for agent in base.render.findAllMatches("**/agent-*"):
            if not agent.hasPythonTag("agent"):
                continue
            a = agent.getPythonTag("agent")
            bounds = a.actorNodePath.getBounds()
            bounds.xform(a.actorNodePath.getMat(self.fov))
            pos = a.actorNodePath.getPos(self.fov)
            if self.fov.node().isInView(pos):
                p1 = self.fov.getRelativePoint(render,pos)
                p2 = Point2()
                self.fov.node().getLens().project(p1, p2)
                p3 = aspect2d.getRelativePoint(render2d, Point3(p2[0], 0, p2[1]))
                agentDict = {'x_pos': p3[0],\
                             'y_pos': p3[2],\
                             'distance':a.actorNodePath.getDistance(self.fov),\
                             'orientation': a.actorNodePath.getH(self.fov)}
                agents[a] = agentDict
        return agents

    def setPosition(self,position):
        self.actorNodePath.setPos(position)

    def getObjectsInView(self):
        """ Gets objects through ray tracing.  Slow"""
        return self.picker.getObjectsInView()
            
    def control__turn_left__start(self, speed=None):
        self.setControl("turn_left",  1)
        self.setControl("turn_right", 0)
        if speed:
            self.speeds[0] = speed
        return "success"

    def control__turn_left__stop(self):
        self.setControl("turn_left",  0)
        return "success"

    def control__turn_right__start(self, speed=None):
        self.setControl("turn_left",  0)
        self.setControl("turn_right", 1)
        if speed:
            self.speeds[1] = speed
        return "success"

    def control__turn_right__stop(self):
        self.setControl("turn_right", 0)
        return "success"

    def control__move_forward__start(self, speed=None):
        self.setControl("move_forward",  1)
        self.setControl("move_backward", 0)
        if speed:
            self.speeds[2] = speed
        return "success"

    def control__move_forward__stop(self):
        self.setControl("move_forward",  0)
        return "success"

    def control__move_backward__start(self, speed=None):
        self.setControl("move_forward",  0)
        self.setControl("move_backward", 1)
        if speed:
            self.speeds[3] = speed
        return "success"

    def control__move_backward__stop(self):
        self.setControl("move_backward", 0)
        return "success"

    def control__move_left__start(self, speed=None):
        self.setControl("move_left",  1)
        self.setControl("move_right", 0)
        if speed:
            self.speeds[4] = speed
        return "success"

    def control__move_left__stop(self):
        self.setControl("move_left",  0)
        return "success"

    def control__move_right__start(self, speed=None):
        self.setControl("move_right",  1)
        self.setControl("move_left", 0)
        if speed:
            self.speeds[5] = speed
        return "success"

    def control__move_right__stop(self):
        self.setControl("move_right",  0)
        return "success"

    def control__look_left__start(self):
        self.setControl("look_left",  1)
        self.setControl("look_right", 0)
        return "success"

    def control__look_left__stop(self):
        self.setControl("look_left",  0)
        return "success"

    def control__look_right__start(self):
        self.setControl("look_right",  1)
        self.setControl("look_left", 0)
        return "success"

    def control__look_right__stop(self):
        self.setControl("look_right",  0)
        return "success"

    def control__look_up__start(self):
        self.setControl("look_up",  1)
        self.setControl("look_down", 0)
        return "success"

    def control__look_up__stop(self):
        self.setControl("look_up",  0)
        return "success"

    def control__look_down__start(self):
        self.setControl("look_down",  1)
        self.setControl("look_up",  0)
        return "success"

    def control__look_down__stop(self):
        self.setControl("look_down",  0)
        return "success"

    def control__jump(self):
        self.setControl("jump",  1)
        return "success"

    def control__view_objects(self):
        """ calls a raytrace to to all objects in view """
        objects = self.getObjectsInFieldOfVision()
        print "Objects in view:", objects
        return objects

    def control__sense(self):
        """ perceives the world, returns percepts dict """
        percepts = dict()
        # eyes: visual matricies
        percepts['vision'] = self.sense__get_vision()
        # objects in purview (cheating object recognition)
        percepts['objects'] = self.sense__get_objects()
        # global position in environment - our robots can have GPS :)
        percepts['position'] = self.sense__get_position()
        # language: get last utterances that were typed
        percepts['language'] = self.sense__get_utterances()
        # agents: returns a map of agents to a list of actions that have been sensed
        percepts['agents'] = self.sense__get_agents()
        print percepts
        return percepts
        
    def control__open_fridge(self):
        print "Opening fridge"
        print self.control__use_right_hand(target='fridge',action="open")

    def control__say_meta(self, message = "Hello!"):
       self.speech_bubble['text'] = "META: "+message
       self.last_spoke = 0
       return "success"

 
    def control__say_goal(self, message = "Hello!"):
       self.speech_bubble['text'] = "GOAL: "+message
       self.last_spoke = 0
       return "success"

    def control__say(self, message = "Hello!"):
       self.speech_bubble['text'] = message
       self.last_spoke = 0
       return "success"

    def control__pick_up_with_right_hand(self, target=None):
        print target
        if not target:
            d = self.picker.pick((0, 0))
            if d:
                target = d[0]
            else:
                print "no target in reach"
                return
        else:
            target = render.find("**/*" + target + "*").getPythonTag("isisobj")
        print "attempting to pick up " + target.name + " with right hand.\n"
        if self.right_hand_holding_object:
            return 'right hand is already holding ' + self.right_hand_holding_object.getName() + '.'
        if self.can_grasp(target):
            result = target.call(self, "pick_up",self.player_right_hand)
            print "Result of trying to pick up %s:" % target.name, result
            if result == 'success':
                self.right_hand_holding_object = target 
            return result
        else:
            print "that item is not graspable"
            return 'object (' + target.name + ') is not graspable (i.e. in view and close enough).'

    def control__pick_up_with_left_hand(self, target = None):
        if not target:
            d = self.picker.pick((0, 0))
            if d:
                target = d[0]
            else:
                print "no target in reach"
                return
        else:
            target = render.find("**/*" + target + "*").getPythonTag("isisobj")
        print "attempting to pick up " + target.name + " with left hand.\n"
        if self.left_hand_holding_object:
            return 'left hand is already holding ' + self.left_hand_holding_object.getName() + '.'
        if self.can_grasp(target):
            result = target.call(self, "pick_up",self.player_left_hand)
            print "Result of trying to pick up %s:" % target.name, result
            if result == 'success':
                self.left_hand_holding_object = target
            return result
        else:
            print "that item is not graspable"
            return 'object (' + target.name + ') is not graspable (i.e. in view and close enough).'

    def control__put_object_in_empty_left_hand(self, object_name):
        if (self.left_hand_holding_object is not False):
            return "left hand not empty"
        world_object = self.agent_simulator.worldObjects[object_name]
        world_object.reparentTo(self.player_left_hand)
        world_object.setPos(0, 0, 0)
        world_object.setHpr(0, 0, 0)
        self.left_hand_holding_object = world_object
        return "success"

    def control__put_object_in_empty_right_hand(self, object_name):
        if (self.right_hand_holding_object is not False):
            return "right hand not empty"
        world_object = self.agent_simulator.worldObjects[object_name]
        world_object.reparentTo(self.player_right_hand)
        world_object.setPos(0, 0, 0)
        world_object.setHpr(0, 0, 0)
        self.right_hand_holding_object = world_object
        return "success"

    def control__drop_from_right_hand(self):
        print "attempting to drop object from right hand.\n"
        if self.right_hand_holding_object is False:
            return 'right hand is not holding an object.'
        result = self.right_hand_holding_object.call(self, 'drop', render)
        if result == 'success':
            self.right_hand_holding_object = False
        return result

    def control__drop_from_left_hand(self):
        print "attempting to drop object from left hand.\n"
        if self.left_hand_holding_object is False:
            return 'left hand is not holding an object.'
        result = self.left_hand_holding_object.call(self, 'drop', render)
        if result == 'success':
            self.left_hand_holding_object = False
        return result

    def control__use_right_hand(self, target = None, action = None):
        if not action:
            if self.msg:
                action = self.msg
            else:
                action = "divide"
        if not target:
            target = self.picker.pick((0, 0))
            if not target:
                print "no target specified"
                return
            else:
                target = target[0]
        else:
            target = render.find("**/*" + target + "*")
        if self.can_grasp(target):
            if(target.call(self, action, self.right_hand_holding_object) or
              (self.right_hand_holding_object and self.right_hand_holding_object.call(self, action, target))):
                return "success"
            return str(action) + " not associated with either target or object"
        return "target not within reach"

    def control__use_left_hand(self, target = None, action = None):
        if not action:
            if self.msg:
                action = self.msg
            else:
                action = "divide"
        if not target:
            target = self.picker.pick((0, 0))
            if not target:
                print "no target specified"
                return
            else:
                target = target[0]
        else:
            target = render.find("**/*" + target + "*")
        if self.can_grasp(target):
            target.call(self, action, self.left_hand_holding_object)
            return "success"
        return "target not within reach"

    def can_grasp(self, object):
        return object.getDistance(self.fov) < 5.0

    def is_holding(self, object_name):
        return ((self.left_hand_holding_object  and (self.left_hand_holding_object.getName()  == object_name)) \
             or (self.right_hand_holding_object and (self.right_hand_holding_object.getName() == object_name)))

    def empty_hand(self):
        if (self.left_hand_holding_object is False):
            return self.player_left_hand
        elif (self.right_hand_holding_object is False):
            return self.player_right_hand
        return False

    def has_empty_hand(self):
        return (self.empty_hand() is not False)

    def control__use_aimed(self):
        """
        Try to use the object that we aim at.
        A similar mechanics can be used to create a gun.

        Note the usage of the doRaycast method from the odeWorldManager.
        """
        dir = render.getRelativeVector(self.fov, Vec3(0, 1.0, 0))
        pos = self.fov.getPos(render) 
        print "relative vector", pos
        # FIXME: work with non-ODE
        return
        #self.aimRay.set(pos, dir)

        # raycast
        closestEntry, closestGeom = self.physicsManager.doRaycast(self.aimRay, [self.capsuleGeom])
        if not closestGeom:
            return
        print "Closest geom", closestEntry
        data = self.physicsManager.getGeomData(closestGeom)
        print data.name
        if data.selectionCallback:
            data.selectionCallback(self, dir)
        return "success"

    def sense__get_position(self):
        x,y,z = self.actorNodePath.getPos()
        h,p,r = self.actorNodePath.getHpr()
        #FIXME
        # neck is not positioned in Blockman nh,np,nr = self.agents[agent_id].actor_neck.getHpr()
        left_hand_obj = "" 
        right_hand_obj = "" 
        if self.left_hand_holding_object:  left_hand_obj = self.left_hand_holding_object.getName()
        if self.right_hand_holding_object: right_hand_obj = self.right_hand_holding_object.getName()
        return {'body_x': x, 'body_y': y, 'body_z': z,'body_h':h,\
                'body_p': p, 'body_r': r,  'in_left_hand': left_hand_obj, 'in_right_hand':right_hand_obj}

    def sense__get_vision(self):
        # TODO: not yet implemented
        return []

    def sense__get_objects(self):
        return dict([x.getName(),y] for (x,y) in self.getObjectsInFieldOfVision().items())

    def sense__get_agents(self):
        curSense = time()
        agents = {}
        for k, v in self.getAgentsInFieldOfVision().items():
            v['actions'] = k.getActions(self.lastSense, curSense)
            agents[k.name] = v
        self.lastSense = curSense
        return agents

    def sense__get_utterances(self):
        """ Clear out the buffer of things that the teacher has typed,
        FIXME: this doesn't work right now """
        return []
        utterances = self.teacher_utterances
        self.teacher_utterances = []
        return utterances

    def debug__print_objects(self):
        text = "Objects in FOV: "+ ", ".join(self.sense__get_objects().keys())
        print text

    def addAction(self, action, args, result = 0):
        self.queue.append((time(), action, args, result))
        if len(self.queue) > self.queueSize:
            self.queue.pop(0)

    def getActions(self, start = 0, end = None):
        if not end:
            end = time()
        actions = []
        for act in self.queue:
            if act[0] >= start:
                if act[0] < end:
                    actions.append(act)
                else:
                    break
        return actions

    def setupCollisionSpheres(self, bitmask=AGENTMASK):
        """ This function sets up three separate collision systems:
          1- cSphereNode handled by cWall traverser, stops agents from
           walking into other agents and walls 
          2- cRay handled by cFloor keeps Ralph on the ground
          3- cEvent is a general purpose collision handler that registers
           and delegates collision callbacks, as defined in the physics/panda/manager.py file """
           
        cSphereNode = CollisionNode('agent')
        cSphereNode.addSolid(CollisionSphere(0.0, 0.0, self.height, self.radius))
        cSphereNode.addSolid(CollisionSphere(0.0, 0.0, self.height + 2.2 * self.radius, self.radius))
        cSphereNode.setFromCollideMask(AGENTMASK|WALLMASK|OBJMASK)
        cSphereNode.setIntoCollideMask(AGENTMASK)
        cSphereNodePath = self.actorNodePath.attachNewNode(cSphereNode)
        #cSphereNodePath.show()
        self.physicsManager.cWall.addCollider(cSphereNodePath, self.actorNodePath)
        base.cTrav.addCollider(cSphereNodePath, self.physicsManager.cWall)
        # add same colliders to cEvent
        cEventSphereNode = CollisionNode('agent')
        cEventSphere = CollisionSphere(0.0, 0.0, self.height, self.radius)
        cEventSphere.setTangible(0)
        cEventSphereNode.addSolid(cEventSphere)
        cEventSphereNode.setFromCollideMask(AGENTMASK )
        cEventSphereNode.setIntoCollideMask(AGENTMASK | OBJMASK)
        cEventSphereNodePath = self.actorNodePath.attachNewNode(cEventSphereNode)
        
        base.cTrav.addCollider(cEventSphereNodePath, base.cEvent)

        # add collision ray to keep ralph on the ground
        cRay = CollisionRay(0.0, 0.0, CollisionHandlerRayStart, 0.0, 0.0, -1.0)
        cRayNode = CollisionNode('actor-raynode')
        cRayNode.addSolid(cRay)
        cRayNode.setFromCollideMask(FLOORMASK)
        cRayNode.setIntoCollideMask(BitMask32.allOff()) 
        self.cRayNodePath = self.actorNodePath.attachNewNode(cRayNode)
        # add colliders
        self.physicsManager.cFloor.addCollider(self.cRayNodePath, self.actorNodePath)
        base.cTrav.addCollider(self.cRayNodePath, self.physicsManager.cFloor)


    def addBlastForce(self, vector):
        self.lifter.addVelocity(vector.length())



    def update(self, stepSize=0.1):
        self.speedvec = [0.0, 0.0]

        # the values in self.speeds are used as coefficientes for turns and movements
        if (self.controlMap["turn_left"]!=0):        self.actorNodePath.setH(self.actorNodePath.getH() + stepSize*self.speeds[0])
        if (self.controlMap["turn_right"]!=0):       self.actorNodePath.setH(self.actorNodePath.getH() - stepSize*self.speeds[1])
        if (self.controlMap["move_forward"]!=0):     self.speedvec[1] =  self.speeds[2]
        if (self.controlMap["move_backward"]!=0):    self.speedvec[1] = -self.speeds[3]
        if (self.controlMap["move_left"]!=0):        self.speedvec[0] = -self.speeds[4]
        if (self.controlMap["move_right"]!=0):       self.speedvec[0] =  self.speeds[5]
        if (self.controlMap["look_left"]!=0):        self.neck.setR(bound(self.neck.getR(),-60,60)+stepSize*80)
        if (self.controlMap["look_right"]!=0):       self.neck.setR(bound(self.neck.getR(),-60,60)-stepSize*80)
        if (self.controlMap["look_up"]!=0):          self.neck.setP(bound(self.neck.getP(),-60,80)+stepSize*80)
        if (self.controlMap["look_down"]!=0):        self.neck.setP(bound(self.neck.getP(),-60,80)-stepSize*80)

        speedVec = Vec3(self.speedvec[0]*stepSize, self.speedvec[1]*stepSize, 0)
        quat = self.actor.getQuat(render)
        # xform applies rotation to the speedVector
        speedVec = quat.xform(speedVec)
        # compute the new position
        newPos = self.actorNodePath.getPos()+speedVec

        self.actorNodePath.setFluidPos(newPos)

        # allow dialogue window to gradually decay (changing transparancy) and then disappear
        self.last_spoke += stepSize/2
        self.speech_bubble['text_bg']=(1,1,1,1/(self.last_spoke+0.01))
        self.speech_bubble['frameColor']=(.6,.2,.1,.5/(self.last_spoke+0.01))
        if self.last_spoke > 2:
            self.speech_bubble['text'] = ""

        # update animation
        # If the character is moving, loop the run animation.
        # If he is standing still, stop the animation.
        if (self.controlMap["move_forward"]!=0) or (self.controlMap["move_backward"]!=0) or (self.controlMap["move_left"]!=0) or (self.controlMap["move_right"]!=0):
            if self.isMoving is False:
                self.isMoving = True
        else:
            if self.isMoving:
                self.current_frame_count = 5.0
                self.isMoving = False

        total_frame_num = self.actor.getNumFrames('walk')
        if self.isMoving:
            self.current_frame_count = self.current_frame_count + (stepSize*250.0)
            if self.current_frame_count > total_frame_num:
                self.current_frame_count = self.current_frame_count%total_frame_num
            self.actor.pose('walk', self.current_frame_count)
        elif self.current_frame_count != 0:
            self.current_frame_count = 0
            self.actor.pose('idle', 0)
        return Task.cont
        
def map3dToAspect2d(node, point):
    """Maps the indicated 3-d point (a Point3), which is relative to 
    the indicated NodePath, to the corresponding point in the aspect2d 
    scene graph. Returns the corresponding Point3 in aspect2d. 
    Returns None if the point is not onscreen. """ 
    # Convert the point to the 3-d space of the camera 
    p3 = self.fov.getRelativePoint(node, point) 

    # Convert it through the lens to render2d coordinates 
    p2 = Point2()
    if not self.fov.node().getLens().project(p3, p2):
        return None 
    r2d = Point3(p2[0], 0, p2[1])
    # And then convert it to aspect2d coordinates 
    a2d = aspect2d.getRelativePoint(render2d, r2d)
    return a2d


class Picker(DirectObject.DirectObject):
    """Picker class derived from http://www.panda3d.org/phpbb2/viewtopic.php?p=4532&sid=d5ec617d578fbcc4c4db0fc68ee87ac0"""
    def __init__(self, camera, agent, tag = 'pickable', value = 'true'):
        self.camera = camera
        self.tag = tag
        self.value = value
        self.agent = agent
        self.queue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)

        self.pickerNode.setFromCollideMask(OBJPICK|AGENTMASK)
        self.pickerNode.setIntoCollideMask(BitMask32.bit(0))

        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)

        base.cTrav.addCollider(self.pickerNP, self.queue)

    def pick(self, pos):
        self.pickerRay.setFromLens(self.camera.node(), pos[0], pos[1])
        base.cTrav.traverse(render)
        if self.queue.getNumEntries() > 1:
            self.queue.sortEntries()
            parent = self.queue.getEntry(1).getIntoNodePath().getParent()
            point = self.queue.getEntry(1).getSurfacePoint(self.agent.fov)    
            object_dict = {'x_pos': point.getY(),\
                           'y_pos': point.getY(),\
                           'distance':self.queue.getEntry(1).getIntoNodePath().getDistance(self.agent.fov)}
            while parent != render:
                if(self.tag == None):
                    return (parent, object_dict)
                elif parent.getTag(self.tag) == self.value:
                    print "FOUND OBJECT:", parent
                    return (parent.getPythonTag("isisobj"), object_dict)
                else:
                    parent = parent.getParent()
        return None


    def getObjectsInView(self, xpoints = 20, ypoints = 15):
        objects = {}
        for x in frange(-1, 1, 2.0/xpoints):
            for y in frange(-1, 1, 2.0/ypoints):
                o = self.pick((x, y))
                if o and (o[0] not in objects or o[1] < objects[o[0]]):
                    objects[o[0]] = o[1]
        return objects
