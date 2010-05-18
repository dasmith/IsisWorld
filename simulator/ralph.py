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

from odeWorldManager import *
from direct.interval.IntervalGlobal import *
from direct.actor.Actor import Actor
from direct.gui.DirectGui import DirectLabel
from pandac.PandaModules import PandaNode,NodePath,Camera
import math
#import time

class Ralph(PhysicsCharacterController):
    def __init__(self, worldManager, agentSimulator, myName):

        self.name = myName
        self.agent_simulator = agentSimulator
	
        self.controlMap = {"turn_left":0, "turn_right":0, "move_forward":0, "move_backward":0, "move_right":0, "move_left":0,\
                           "look_up":0, "look_down":0, "look_left":0, "look_right":0}
        
        self.actor = Actor("models/ralph/ralph",{"walk":"models/ralph/ralph-walk", "run": "models/ralph/ralph-run"})
        self.actor.reparentTo(render)
        self.actor.setScale(0.4)


        PhysicsCharacterController.__init__(self,worldManager)

        # Expose agent's right hand joint to attach objects to
        self.actor_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'RightHand')
        self.actor_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'LeftHand')
        
        self.right_hand_holding_object = False
        self.left_hand_holding_object  = False

        # speech bubble
        self.last_spoke = 0
        self.speech_bubble=DirectLabel(parent=self.actor, text="", text_wordwrap=10, pad=(3,3),\
                       relief=None, text_scale=(.5,.5), pos = (0,0,6), frameColor=(.6,.2,.1,.5),\
                       textMayChange=1, text_frame=(0,0,0,1), text_bg=(1,1,1,1))
        self.speech_bubble.component('text0').textNode.setCardDecal(1)
        self.speech_bubble.setBillboardAxis()
        
        # visual processing
        self.actor_eye = self.actor.exposeJoint(None, 'modelRoot', 'LeftEyeLid')
        # put a camera on ralph
        self.fov = NodePath(Camera('RaphViz'))
        self.fov.reparentTo(self.actor_eye)
        self.fov.setHpr(180,0,0)


        lens = self.fov.node().getLens()
        lens.setFov(60) #  degree field of view (expanded from 40)
        lens.setNear(0.2)
        #self.fov.node().showFrustum() # displays a box around his head


        self.actor_neck = self.actor.controlJoint(None, 'modelRoot', 'Neck')
	
        # Define subpart of agent for when he's standing around
        self.actor.makeSubpart("arms", ["LeftShoulder", "RightShoulder"])

        self.prevtime = 0
        self.isMoving = False
	
        self.current_frame_count = 0.

        #self.name = "Ralph"

        """
        The ray sticking out of the camera and meant for clicking at
        objects in the world.
        """
        #self.aimRay = OdeRayGeom(self.worldManager.raySpace, 2.5)
        #self.aimed = None

        """
        I've added that mainly for sitting, but the later might be
        usefull for other things too.
        """
        self.isSitting = False
        self.isDisabled = False

    def setPosQuat(self, render, pos, quat):
        self.actor.setPos(render, pos)
        self.actor.setQuat(render, quat)

    def setControl(self, control, value):
        """Set the state of one of the character's movement controls.
        """
        self.controlMap[control] = value


    def get_objects(self):
        """ Looks up all of the model nodes that are 'isInView' of the camera"""

        def project_carelessly(lens, point): 
           ''' Similar to Lens.project(), but never returns None-- returning
           inverted image when object is BEHIND camera
           
           code from https://www.panda3d.org/phpbb2/viewtopic.php?p=20245 ''' 

           projection_mat = lens.getProjectionMat() 
           full = projection_mat.xform( VBase4(point[0], point[1], point[2], 1.0) ) 
           if full[3] == 0.0: 
              # There is no meaningful projection for the nodal point of the lens. 
              # So return a value that is Very Far Away. 
              return (1000000.0, 1000000.0, -1000000.0) 

           recip_full3 = 1.0 / full[3] 
           return (full[0] * recip_full3, 
                   full[1] * recip_full3, 
                   full[2] * recip_full3) 

        def map3dToAspect2d(node, point): 
           """Maps the indicated 3-d point (a Point3), which is relative to 
              the indicated NodePath, to the corresponding point in the aspect2d 
              scene graph. Returns the corresponding Point3 in aspect2d. 
              Returns None if the point is not onscreen. """ 

           # Convert the point to the 3-d space of the camera 
           p3 = self.fov.getRelativePoint(node, point) 

           # Convert from camera 3d space to camera 2d space. 
           # Manual override. 
           p2 = project_carelessly(self.fov.node().getLens(), p3) 

           r2d = Point3(p2[0], 0, p2[1]) 

           # And then convert it to aspect2d coordinates 
           a2d = aspect2d.getRelativePoint(render2d, r2d) 

           return a2d

        objs = render.findAllMatches("**/+ModelNode")
        in_view = {}
        for o in objs:
            o.hideBounds() # in case previously turned on
            o_pos = o.getPos(self.fov)
            if self.fov.node().isInView(o_pos):
                if True:#self.agent_simulator.world_objects.has_key(o.getName()):
                    b_min, b_max =  o.getTightBounds()
                    a_min = map3dToAspect2d(render, b_min)
                    a_max = map3dToAspect2d(render, b_max)
                    if a_min == None or a_max == None:
                        continue
                    x_diff = math.fabs(a_max[0]-a_min[0])
                    y_diff = math.fabs(a_max[2]-a_min[2])
                    area = 100*x_diff*y_diff  # percentage of screen
                    object_dict = {'x_pos': (a_min[2]+a_max[2])/2.0,\
                                   'y_pos': (a_min[0]+a_max[0])/2.0,\
                                   'distance':o.getDistance(self.fov), \
                                   'area':area,\
                                   'orientation': o.getH(self.fov)}
                    in_view[o.getName()]=object_dict
                    print o.getName(), object_dict
                    print o.getAncestor(1).getName()
                    print o.getAncestor(1).listTags()
                    print self.actor_neck.getH()
##                    if (o.getAncestor(1).getName() == "Ralph"):
##                       for agent in self.agent_simulator.agents:
##                           if agent.
        return in_view


            
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

    def can_grasp(self, object_name):
        objects = self.get_objects()
        if objects.has_key(object_name):
            object_view = objects[object_name]
            distance = object_view['distance']
            if (distance < 5.0):
                return True
        return False

    def control__say(self, message):
       self.speech_bubble['text'] = message
       self.last_spoke = 0

    def talk_to_agent(self, agentName, message):
        self.agent_simulator.communicate(self.name, agentName, message)

    #here one can tell the agent what to do when someone talks with him.
    def hear(self, speaker, text):
        #self.control__jump()
        self.control__say(("I hear ya, " + speaker))

        

    def control__pick_up_with_right_hand(self, pick_up_object):
        print "attempting to pick up " + pick_up_object + " with right hand.\n"
        if self.right_hand_holding_object:
            return 'right hand is already holding ' + self.right_hand_holding_object.getName() + '.'
        if self.can_grasp(pick_up_object):
            world_object = self.agent_simulator.world_objects[pick_up_object]
            object_parent = world_object.getParent()
            if (object_parent == self.agent_simulator.env):
                world_object.wrtReparentTo(self.actor_right_hand)
                world_object.setPos(0, 0, 0)
                world_object.setHpr(0, 0, 0)
                self.right_hand_holding_object = world_object
                return 'success'
            else:
                return 'object (' + pick_up_object + ') is already held by something or someone.'
        else:
            return 'object (' + pick_up_object + ') is not graspable (i.e. in view and close enough).'

    def put_object_in_empty_left_hand(self, object_name):
        if (self.left_hand_holding_object is not False):
            return False
        world_object = self.agent_simulator.world_objects[object_name]
        world_object.wrtReparentTo(self.actor_left_hand)
        world_object.setPos(0, 0, 0)
        world_object.setHpr(0, 0, 0)
        self.left_hand_holding_object = world_object
        return True

    def control__pick_up_with_left_hand(self, pick_up_object):
        print "attempting to pick up " + pick_up_object + " with left hand.\n"
        if self.left_hand_holding_object:
            return 'left hand is already holding ' + self.left_hand_holding_object.getName() + '.'
        if self.can_grasp(pick_up_object):
            world_object = self.agent_simulator.world_objects[pick_up_object]
            object_parent = world_object.getParent()
            if (object_parent == self.agent_simulator.env):
                self.put_object_in_empty_left_hand(pick_up_object)
                return 'success'
            else:
                return 'object (' + pick_up_object + ') is already held by something or someone.'
        else:
                return 'object (' + pick_up_object + ') is not graspable (i.e. in view and close enough).'

    def control__drop_from_right_hand(self):
        print "attempting to drop object from right hand.\n"
        if self.right_hand_holding_object is False:
            return 'right hand is not holding an object.'
        world_object = self.right_hand_holding_object
        self.right_hand_holding_object = False
        world_object.wrtReparentTo(self.agent_simulator.env)
        world_object.setHpr(0, 0, 0)
        world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'

    def control__drop_from_left_hand(self):
        print "attempting to drop object from left hand.\n"
        if self.left_hand_holding_object is False:
            return 'left hand is not holding an object.'
        world_object = self.left_hand_holding_object
        self.left_hand_holding_object = False
        world_object.wrtReparentTo(self.agent_simulator.env)
        world_object.setHpr(0, 0, 0)
        world_object.setPos(self.position() + self.forward_normal_vector() * 0.5)
        world_object.setZ(world_object.getZ() + 1.0)
        return 'success'

    def is_holding(self, object_name):
        return ((self.left_hand_holding_object  and (self.left_hand_holding_object.getName()  == object_name)) \
             or (self.right_hand_holding_object and (self.right_hand_holding_object.getName() == object_name)))

    def empty_hand(self):
        if (self.left_hand_holding_object is False):
            return self.actor_left_hand
        elif (self.right_hand_holding_object is False):
            return self.actor_right_hand
        return False

    def has_empty_hand(self):
        return (self.empty_hand() is not False)

    def control__use_object_with_object(self, use_object, with_object):
        if ((use_object == 'knife') and (with_object == 'loaf_of_bread')):
            if self.is_holding('knife'):
                if self.can_grasp('loaf_of_bread'):
                    if self.has_empty_hand():
                        empty_hand      = self.empty_hand()
                        new_object_name = self.agent_simulator.create_object__slice_of_bread([float(x) for x in empty_hand.getPos()])
                    if (empty_hand == self.actor_left_hand):
                        self.put_object_in_empty_left_hand(new_object_name)
                    elif (empty_hand == self.actor_right_hand):
                        self.put_object_in_empty_right_hand(new_object_name)
                    else:
                        return "simulator error: empty hand is not left or right.  (are there others?)"
                    return 'success'
                else:
                    return 'failure: one hand must be empty to hold loaf_of_bread in place while using knife.'
            else:
                return 'failure: loaf of bread is not graspable (in view and close enough)'
        else:
            return 'failure: must be holding knife object to use it.'
        return 'failure: don\'t know how to use ' + use_object + ' with ' + with_object + '.'

    def sitOnChair(self, chair):
        """
        Thanks to this method the character is able to sit on chairs (and possibly
        in cars or wherever you need it to).
        """
        chairQuat = chair.chairNP.getQuat(render)
        newPos0 = chair.chairNP.getPos(render) + chairQuat.xform(Vec3(0, 1.0, 1.8))
        newPos1 = chair.chairNP.getPos(render) + chairQuat.xform(Vec3(0, 0.0, 1.4))
        newHpr = chair.chairNP.getHpr(render)

        startHpr = base.cam.getHpr(render)
        startHpr[0] = self.capsuleGeom.getQuaternion().getHpr().getX()

        """
        The mighty Panda Sequence
        """
        Sequence(
                Func(self.setSitting, chair),
                Func(self.disable),
                LerpPosHprInterval(base.cam, 1.0, newPos0, newHpr, None, startHpr),
                LerpPosInterval(base.cam, .5, newPos1),
        ).start()

    def standUpFromChair(self):
        """
        And this allows the player to stand up from a chair.
        """
        chairQuat = self.isSitting.chairNP.getQuat(render)
        newPos0 = self.isSitting.chairNP.getPos(render) + chairQuat.xform(Vec3(0, 1.0, 1.7))
        newPos1 = self.capsuleGeom.getPosition()
        newPos1.setZ(newPos1.getZ()+self.camH)
        newHpr = self.capsuleGeom.getQuaternion().getHpr()

        chair = self.isSitting

        Sequence(
                Func(self.setSitting, None),
                LerpPosInterval(base.cam, 0.3, newPos0),
                LerpPosHprInterval(base.cam, 0.5, newPos1, newHpr),
                Func(self.enable),
                Func(chair.setState, "vacant")
        ).start()

    def setSitting(self, chair):
        """
        Note that the isSitting variable is actually used to store the chair
        we're currently sitting on, but, as everything in Python, it's
        also a bool value.
        """
        self.isSitting = chair

    def disable(self):
        """
        Disable collisions for this character
        """
        self.isDisabled = True
        self.capsuleGeom.disable()
        self.footRay.disable()

    def enable(self):
        """
        Enable collisions for this character
        """
        self.footRay.enable()
        self.capsuleGeom.enable()
        self.isDisabled = False

    def setFly(self, fly):
        """
        Fly mode. In this mode the character is not kept on the ground.
        Instead it can fly around the map.

        I've made this for ladders, but it can easily be used for swimming
        or for implementing a noclip cheat.
        """
        if fly:
            self.state = "fly"
            self.movementParent = base.cam
        else:
            self.state = "ground"
            self.movementParent = self.capsuleGeom


    def control__use_aimed(self):
        """
        Try to use the object that we aim at.
        A similar mechanics can be used to create a gun.

        Note the usage of the doRaycast method from the odeWorldManager.
        """
        dir = render.getRelativeVector(self.fov, Vec3(0, 1.0, 0))
        pos = self.fov.getPos(render) 
        print "relative vector", pos
        self.aimRay.set(pos, dir)

        # raycast
        closestEntry, closestGeom = self.worldManager.doRaycast(self.aimRay, [self.capsuleGeom])
        if not closestGeom:
            return
        print "Closest geom", closestEntry
        data = self.worldManager.getGeomData(closestGeom)
        print data.name
        if data.selectionCallback:
            data.selectionCallback(self, dir)



    def control__jump(self):
        """
        Crouching and jumping don't seem to like each other, so I decided
        to make it impossible to jump while crouching.
        """
        if inputState.isSet("crouch") or self.crouchLock:
            return
        odeKinematicCharacterController.jump(self)



    def update(self, stepSize):
         # save the character's initial position so that we can restore it,
         # in case he falls off the map or runs into something.
         
        print "update-ralph"
        if self.isSitting:
            if inputState.isSet("forward"):
                self.standUpFromChair()
            return
        elif self.isDisabled:
            return

        moveAtSpeed = 4.0
        self.speed = [0.0, 0.0]


        self.startpos = self.actor.getPos()
        # enforces bounds on a numeric value
        def bound(i, mn = -1, mx = 1): return min(max(i, mn), mx)
        # move the character if any of the move controls are activated.

        if (self.controlMap["turn_left"]!=0):        self.setH(self.getH() + stepSize*80)
        if (self.controlMap["turn_right"]!=0):       self.setH(self.getH() - stepSize*80)
        if (self.controlMap["move_forward"]!=0):     self.speed[1] = -moveAtSpeed
        if (self.controlMap["move_backward"]!=0):    self.speed[1] = moveAtSpeed
        if (self.controlMap["move_left"]!=0):        self.speed[0] = -moveAtSpeed
        if (self.controlMap["move_right"]!=0):       self.speed[0] = moveAtSpeed
        if (self.controlMap["look_left"]!=0):      
            self.actor_neck.setP(bound(self.actor_neck.getP(),-60,60)+1*(stepSize*50))
        if (self.controlMap["look_right"]!=0):
            self.actor_neck.setP(bound(self.actor_neck.getP(),-60,60)-1*(stepSize*50))
        if (self.controlMap["look_up"]!=0):
            self.actor_neck.setH(bound(self.actor_neck.getH(),-60,80)+1*(stepSize*50))
        if (self.controlMap["look_down"]!=0):
            self.actor_neck.setH(bound(self.actor_neck.getH(),-60,80)-1*(stepSize*50))

        # allow dialogue window to gradually decay (changing transparancy) and then disappear
        self.last_spoke += stepSize
        self.speech_bubble['text_bg']=(1,1,1,1/(2*self.last_spoke+0.01))
        self.speech_bubble['frameColor']=(.6,.2,.1,.5/(2*self.last_spoke+0.01))
        if self.last_spoke > 2:
            self.speech_bubble['text'] = ""

        # If the character is moving, loop the run animation.
        # If he is standing still, stop the animation.

        PhysicsCharacterController.update(self, stepSize )

        if (self.controlMap["move_forward"]!=0) or (self.controlMap["move_backward"]!=0) or (self.controlMap["move_left"]!=0) or (self.controlMap["move_right"]!=0):
            if self.isMoving is False:
                self.isMoving = True
        else:
            if self.isMoving:
                self.current_frame_count = 5.0
                self.isMoving = False

        total_frame_num = self.actor.getNumFrames('walk')
        if self.isMoving:
            self.current_frame_count = self.current_frame_count + (stepSize*1000.0)
            while (self.current_frame_count >= total_frame_num + 1):
                self.current_frame_count -= total_frame_num
                self.actor.pose('walk', self.current_frame_count)

