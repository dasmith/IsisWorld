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
    
    def __init__(self, worldManager, agentSimulator, name, worldObjectsDict, queueSize = 100):

        # setup the visual aspects of ralph
        self.actor= Actor("media/models/boxman",{"walk":"media/models/boxman-walk", "idle": "media/models/boxman-idle"})
        self.actor.setScale(1.0)
        self.actor.setH(0)

        self.actor.setColorScale(random.random(), random.random(), random.random(), 1.0)
        self.actorNode = ActorNode('physicsControler-%s' % name)
        self.actorNodePath = render.attachNewNode(self.actorNode)
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
        self.worldManager = worldManager    
        x = random.randint(0,10)
        y = random.randint(0,10)
        z = random.randint(12,25)
        self.actorNodePath.setFluidPos(Vec3(x,y,z))
        
        self.setupCollisionSpheres()

    
        self.actor.makeSubpart("arms", ["LeftShoulder", "RightShoulder"])    
        
        # Expose agent's right hand joint to attach objects to
        self.player_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'Hand.R')
        self.player_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'Hand.L')
        self.player_right_hand.setColorScaleOff()
        self.player_left_hand.setColorScaleOff()
        self.player_head  = self.actor.exposeJoint(None, 'modelRoot', 'Head')
        self.neck = self.actor.controlJoint(None, 'modelRoot', 'Head')

        self.controlMap = {"turn_left":0, "turn_right":0, "move_forward":0, "move_backward":0, "move_right":0, "move_left":0,\
                           "look_up":0, "look_down":0, "look_left":0, "look_right":0, "jump":0}

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

        """
        Object used for picking objects in the field of view
        """
        self.picker =Picker(self.fov, worldObjectsDict)

        # Initialize the action queue, with a maximum length of queueSize
        self.queue = []
        self.queueSize = queueSize
        
        # when you're done, register yourself with physical simulator
        # so it can call update() at each step of the physics
        self.worldManager.addAgent(self)


    def setControl(self, control, value):
        """Set the state of one of the character's movement controls.  """
        self.controlMap[control] = value

    def getObjectsInFieldOfVision(self):
        """ This works in an x-ray vision style. Fast"""
        objects_inview=0
        objects = []
        objs=base.render.findAllMatches("**/IsisObject*")
        for o in objs:
            if self.fov.node().isInView(o.getPos(self.fov)):
                o.setColor((1,0,0,1))
                objects_inview+=1
                objects.append(o)
            else: 
                o.setColor((1,1,1,1))
        self.control__say("If I were wearing x-ray glasses, I could see %i items"  % objects_inview) 
        return objects

    def getObjectsInView(self):
        """ Gets objects through ray tracing.  Slow"""
        return self.picker.getObjectsInView()
            
    def control__turn_left__start(self):
        self.setControl("turn_left",  1)
        self.setControl("turn_right", 0)

    def control__turn_left__stop(self):
        self.setControl("turn_left",  0)

    def control__turn_right__start(self):
        self.setControl("turn_left",  0)
        self.setControl("turn_right", 1)

    def control__turn_right__stop(self):
        self.setControl("turn_right", 0)

    def control__move_forward__start(self):
        self.setControl("move_forward",  1)
        self.setControl("move_backward", 0)

    def control__move_forward__stop(self):
        self.setControl("move_forward",  0)

    def control__move_backward__start(self):
        self.setControl("move_forward",  0)
        self.setControl("move_backward", 1)

    def control__move_backward__stop(self):
        self.setControl("move_backward", 0)

    def control__move_left__start(self):
        self.setControl("move_left",  1)
        self.setControl("move_right", 0)

    def control__move_left__stop(self):
        self.setControl("move_left",  0)

    def control__move_right__start(self):
        self.setControl("move_right",  1)
        self.setControl("move_left", 0)

    def control__move_right__stop(self):
        self.setControl("move_right",  0)

    def control__look_left__start(self):
        self.setControl("look_left",  1)
        self.setControl("look_right", 0)

    def control__look_left__stop(self):
        self.setControl("look_left",  0)

    def control__look_right__start(self):
        self.setControl("look_right",  1)
        self.setControl("look_left", 0)

    def control__look_right__stop(self):
        self.setControl("look_right",  0)

    def control__look_up__start(self):
        self.setControl("look_up",  1)
        self.setControl("look_down", 0)

    def control__look_up__stop(self):
        self.setControl("look_up",  0)

    def control__look_down__start(self):
        self.setControl("look_down",  1)
        self.setControl("look_up",  0)

    def control__look_down__stop(self):
        self.setControl("look_down",  0)

    def control__jump(self):
        self.setControl("jump",  1)

    def control__view_objects(self):
        """ calls a raytrace to to all objects in view """
        objects = self.getObjectsInView()
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
        return percepts
 
    def can_grasp(self, object_name):
        objects = self.get_objects()
        print object_name
        print objects
        if objects.has_key(object_name):
            print "found object"
            object_view = objects[object_name]
            distance = object_view['distance']
            print distance
            if (distance < 5.0):
                return True
        return False

    def control__say(self, message):
       self.speech_bubble['text'] = message
       self.last_spoke = 0

    def talk_to_agent(self, agentName, message):
        self.agent_simulator.communicate(self.name, agentName, message)

    def control__pick_up_with_right_hand(self, pick_up_object=None):
        if not pick_up_object:
            d = self.raytrace_getAllObjectsInView()
            if len(d) > 0:
                pick_up_object = d.keys()[0]
            else:
                print "no objects in view to pick up"
                return
        print "attempting to pick up " + pick_up_object.name + " with right hand.\n"
        if self.right_hand_holding_object:
            return 'right hand is already holding ' + self.right_hand_holding_object.getName() + '.'
        if d[pick_up_object] < 5.0:
            if pick_up_object.getNetTag('heldBy') == '':
                pick_up_object.wrtReparentTo(self.player_right_hand)
                # pick_up_object.setPos(0, 0, 0)
                #pick_up_object.setHpr(0, 0, 0)
                self.right_hand_holding_object = pick_up_object
                pick_up_object.setTag('heldBy', self.name)
                print "sucess!"
                print self.player_right_hand.getPos()
                print pick_up_object.getPos()
                return 'success'
            else:
                print "Object being held by " + str(pick_up_object.node().getTag('heldBy'))
                return 'object (' + pick_up_object.name + ') is already held by something or someone.'
        else:
            print "Object not graspable, dist=" + str(d[pick_up_object])
            return 'object (' + pick_up_object.name + ') is not graspable (i.e. in view and close enough).'

    def control__pick_up_with_left_hand(self, pick_up_object = None):
        if not pick_up_object:
            d = self.raytrace_getAllObjectsInView()
            if len(d) > 0:
                pick_up_object = d.keys()[0]
            else:
                print "no objects in view to pick up"
                return
        print "attempting to pick up " + pick_up_object.name + " with left hand.\n"
        if self.left_hand_holding_object:
            return 'left hand is already holding ' + self.left_hand_holding_object.getName() + '.'
        if d[pick_up_object] < 5.0:
            if pick_up_object.getNetTag('heldBy') == '':
                pick_up_object.wrtReparentTo(self.player_left_hand)
                # pick_up_object.setPos(0, 0, 0)
                #pick_up_object.setHpr(0, 0, 0)
                self.left_hand_holding_object = pick_up_object
                pick_up_object.setTag('heldBy', self.name)
                print "sucess!"
                print self.player_left_hand.getPos()
                print pick_up_object.getPos()
                return 'success'
            else:
                print "Object being held by " + str(pick_up_object.node().getTag('heldBy'))
                return 'object (' + pick_up_object.name + ') is already held by something or someone.'
        else:
            print "Object not graspable, dist=" + str(d[pick_up_object])
            return 'object (' + pick_up_object.name + ') is not graspable (i.e. in view and close enough).'

    def control__put_object_in_empty_left_hand(self, object_name):
        if (self.left_hand_holding_object is not False):
            return False
        world_object = self.agent_simulator.world_objects[object_name]
        world_object.wrtReparentTo(self.player_left_hand)
        world_object.setPos(0, 0, 0)
        world_object.setHpr(0, 0, 0)
        self.left_hand_holding_object = world_object
        return True

    def control__put_object_in_empty_right_hand(self, object_name):
        if (self.right_hand_holding_object is not False):
            return False
        world_object = self.agent_simulator.world_objects[object_name]
        world_object.wrtReparentTo(self.player_right_hand)
        world_object.setPos(0, 0, 0)
        world_object.setHpr(0, 0, 0)
        self.right_hand_holding_object = world_object
        return True

    def control__drop_from_right_hand(self):
        print "attempting to drop object from right hand.\n"
        if self.right_hand_holding_object is False:
            return 'right hand is not holding an object.'
        world_object = self.right_hand_holding_object
        world_object.clearTag('heldBy')
        self.right_hand_holding_object = False
        world_object.wrtReparentTo(render)
        world_object.setHpr(0, 0, 0)
        #world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'

    def control__drop_from_left_hand(self):
        print "attempting to drop object from left hand.\n"
        if self.left_hand_holding_object is False:
            return 'left hand is not holding an object.'
        world_object = self.left_hand_holding_object
        world_object.clearTag('heldBy')
        self.left_hand_holding_object = False
        world_object.wrtReparentTo(render)
        world_object.setHpr(0, 0, 0)
        #world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'

    def control__use_right_hand(self, target = None, action = "divide"):
        if not target:
            target = self.picker.pick((0, 0))
            if not target:
                return
            else:
                target = target[0]
        else:
            target = self.agent_simulator.world_objects[target]
        if self.can_grasp(target.name):
            target.call(self, action, self.right_hand_holding_object)

    def control__use_left_hand(self, target = None, action = "divide"):
        if not target:
            target = self.picker.pick((0, 0))
            if not target:
                return
            else:
                target = target[0]
        else:
            target = self.agent_simulator.world_objects[target]
        if self.can_grasp(target.name):
            target.call(self, action, self.left_hand_holding_object)

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
        closestEntry, closestGeom = self.worldManager.doRaycast(self.aimRay, [self.capsuleGeom])
        if not closestGeom:
            return
        print "Closest geom", closestEntry
        data = self.worldManager.getGeomData(closestGeom)
        print data.name
        if data.selectionCallback:
            data.selectionCallback(self, dir)


    def sense__get_position(self):
        x,y,z = self.actor.getPos()
        h,p,r = self.actor.getHpr()
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
        return self.getObjectsInView()

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

    def addAction(self, timeStamp, action, args):
        self.queue.append((timeStamp, action, args))
        if len(self.queue) > self.queueSize:
            self.queue.pop(0)

    def getActionsSince(self, timeStamp):
        actions = []
        for ts, a, args in self.queue:
            if ts >= timeStamp:
                actions.append((ts, a, args))
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
        cSphereNode.setFromCollideMask(WALLMASK | AGENTMASK)
        cSphereNode.setIntoCollideMask(WALLMASK | AGENTMASK | OBJMASK)
        cSphereNodePath = self.actorNodePath.attachNewNode(cSphereNode)
        #cSphereNodePath.show()
        base.cWall.addCollider(cSphereNodePath, self.actorNodePath)
        base.cTrav.addCollider(cSphereNodePath, base.cWall)
        # add same colliders to cEvent
        cEventSphereNode = CollisionNode('agent')
        cEventSphere = CollisionSphere(0.0, 0.0, self.height, self.radius)
        cEventSphere.setTangible(0)
        cEventSphereNode.addSolid(cEventSphere)
        cEventSphereNode.setFromCollideMask(AGENTMASK | OBJMASK)
        cEventSphereNode.setIntoCollideMask(AGENTMASK)
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
        base.cFloor.addCollider(self.cRayNodePath, self.actorNodePath)
        base.cTrav.addCollider(self.cRayNodePath, base.cFloor)


    def addBlastForce(self, vector):
        self.lifter.addVelocity(vector.length())



    def update(self, stepSize=0.1):
        moveAtSpeed = 10.0

        self.speed = [0.0, 0.0]

        if (self.controlMap["turn_left"]!=0):        self.actor.setH(self.actor.getH() + stepSize*220)
        if (self.controlMap["turn_right"]!=0):       self.actor.setH(self.actor.getH() - stepSize*220)
        if (self.controlMap["move_forward"]!=0):     self.speed[1] =  moveAtSpeed
        if (self.controlMap["move_backward"]!=0):    self.speed[1] = -moveAtSpeed
        if (self.controlMap["move_left"]!=0):        self.speed[0] = -moveAtSpeed
        if (self.controlMap["move_right"]!=0):       self.speed[0] =  moveAtSpeed
        if (self.controlMap["look_left"]!=0):        self.neck.setR(bound(self.neck.getR(),-60,60)+1*(stepSize*50))
        if (self.controlMap["look_right"]!=0):       self.neck.setR(bound(self.neck.getR(),-60,60)-1*(stepSize*50))
        if (self.controlMap["look_up"]!=0):          self.neck.setP(bound(self.neck.getP(),-60,80)+1*(stepSize*50))
        if (self.controlMap["look_down"]!=0):        self.neck.setP(bound(self.neck.getP(),-60,80)-1*(stepSize*50))

        speedVec = Vec3(self.speed[0]*stepSize, self.speed[1]*stepSize, 0)
        quat = self.actor.getQuat(render)
        # xform applies rotation to the speedVector
        speedVec = quat.xform(speedVec)
        # compute the new position
        newPos = self.actorNodePath.getPos()+speedVec

        self.actorNodePath.setFluidPos(newPos)

        # allow dialogue window to gradually decay (changing transparancy) and then disappear
        self.last_spoke += stepSize
        self.speech_bubble['text_bg']=(1,1,1,1/(2*self.last_spoke+0.01))
        self.speech_bubble['frameColor']=(.6,.2,.1,.5/(2*self.last_spoke+0.01))
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
            self.current_frame_count = self.current_frame_count + (stepSize*8000.0)
            while (self.current_frame_count >= total_frame_num + 1):
                self.current_frame_count -= total_frame_num
                self.actor.pose('walk', self.current_frame_count)
        return Task.cont

class Picker(DirectObject.DirectObject):
    """Picker class derived from http://www.panda3d.org/phpbb2/viewtopic.php?p=4532&sid=d5ec617d578fbcc4c4db0fc68ee87ac0"""
    def __init__(self, camera, worldObjects, tag = 'pickable', value = 'true'):
        self.camera = camera
        self.tag = tag
        self.value = value
        #self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)

        self.pickerNode.setFromCollideMask(OBJMASK|AGENTMASK)

        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)

        base.cTrav.addCollider(self.pickerNP, self.queue)
        self.worldObjects = worldObjects

    def pick(self, pos):
        self.pickerRay.setFromLens(self.camera.node(), pos[0], pos[1])
        base.cTrav.traverse(render)
        if self.queue.getNumEntries() > 1:
            self.queue.sortEntries()
            parent = self.queue.getEntry(1).getIntoNodePath().getParent()
            point = self.queue.getEntry(1).getSurfacePoint(self.camera)
            dist = math.sqrt(point.getX()**2+point.getY()**2+point.getZ()**2)
            while parent != render:
                if(self.tag == None):
                    return (parent, dist)
                elif parent.getTag(self.tag) == self.value:
                    name = str(parent)
                    return (self.worldObjects[name[name.rfind("IsisObject"):]], dist)
                else:
                    parent = parent.getParent()
        return None


    def getObjectsInView(self, xpoints = 16, ypoints = 12):
        objects = {}
        for x in frange(-1, 1, 2.0/xpoints):
            for y in frange(-1, 1, 2.0/ypoints):
                o = self.pick((x, y))
                if o and (o[0] not in objects or o[1] < objects[o[0]]):
                    objects[o[0]] = o[1]
        return objects
