import direct.directbase.DirectStart 
from pandac.PandaModules import CollisionTraverser,CollisionNode 
from pandac.PandaModules import CollisionHandlerQueue,CollisionRay 
from pandac.PandaModules import Filename 
from pandac.PandaModules import PandaNode,NodePath,Camera,TextNode 
from pandac.PandaModules import Vec3,Vec4,BitMask32 
from direct.gui.OnscreenText import OnscreenText 
from direct.actor.Actor import Actor 
from direct.task.Task import Task 
import random, sys, os, math

class FloatingCamera:
    """ Based on Erik Hazzard's EOA camera

    http://github.com/enoex/eoa
    http://vasir.net
"""
    def __init__(self,actor):
        """init_camera Set up the camera.  Allow for camera autofollow, freemove, etc"""
        base.disableMouse()
        base.camera.reparentTo(render)
        base.camera.setPos(0, -15, 25)
        self.actor = actor
        base.camera.lookAt(self.actor.getX(),self.actor.getY()+2)
        angledegrees = 2
        angleradians = angledegrees * (math.pi / 180.0)
        base.camera.setPos(20*math.sin(angleradians),-20.0*\
                    math.cos(angleradians),3)
        base.camera.setHpr(angledegrees, 0, 0)

        self.controlMap = {"left":0, "right":0, "zoom-in":0, "zoom-out":0}
        """Set up some camera controls"""
        #Camera timer is used to control how long a button is being held
        #to control the camera
        self.timer = 0
        self.zoom = 20


    def setControl(self, control, value):
        self.controlMap[control] = value

    def update_camera(self,task):
        """Check for camera control input and update accordingly"""
        # Get the time self.elapsed since last frame. We need this
        # for framerate-independent movement.
        self.elapsed = globalClock.getDt()

        """---------Keyboard movement-------------------"""
        """Rotate Camera left / right"""
        if self.controlMap['left'] != 0:
            """Rotate the camera to the left"""
            #increment the camera timer, determines speed of camera rotation
            self.timer += .1
            angledegrees = self.timer * 50
            angleradians = angledegrees * (math.pi / 180.0)

            #Set the X, Y as the zoom value * sine or cosine (respectively) of
            #   angle radians, which is determined by rotating the camera left
            #   or right around the character.  The zoom variable determines
            #   in essence, the zoom level which is calcuated simply as
            #   self.elapsed * 20.  Notice this is also the value we use to
            #   setY when we zoom in or out - no coincidence, these numbers
            #   are the same because we want to know the location of the
            #   camera when we pan around the character (this location is
            #   multiplied by sin or cos of angleradians
            base.camera.setPos(self.zoom * math.sin(angleradians), -self.zoom* math.cos(angleradians), base.camera.getZ())

            #Set the heading / yaw (h) of the camera to point at the character
            base.camera.setHpr(angledegrees, 0, 0)

        if self.controlMap['right'] !=0:
            """Rotate the camera to the right"""
            #increment the camera timer
            self.timer -= .1
            angledegrees = self.timer * 50
            angleradians = angledegrees * (math.pi / 180.0)
            base.camera.setPos(self.zoom* math.sin(angleradians), -self.zoom * math.cos(angleradians), base.camera.getZ())
            base.camera.setHpr(angledegrees, 0, 0)

        """Zoom camera in / out"""
        #ZOOM IN
        if self.controlMap['zoom-in'] !=0:
            #Zoom in
            base.camera.setY(base.camera, +(self.elapsed*20))
            #Store the camera position
            self.zoom -= self.elapsed*20

        #ZOOM OUT
        if self.controlMap['zoom-out'] !=0:
            #Zoom out
            base.camera.setY(base.camera, -(self.elapsed*20))
            #Store the camera position
            self.zoom += self.elapsed*20

        return Task.cont
        """---------Mouse movement-------------------"""
        #Zoom in on mouse scroll forward
        if self.controls['key_map']['scroll_up'] !=0:
            #Zoom in
            base.camera.setY(base.camera, +(self.elapsed*20))
            #Store the camera position
            self.controls['camera_settings']['zoom'] -= .1
            #Reset the scroll state to off
            self.controls['key_map']['scroll_up'] = 0

        #Zoom in on mouse scroll forward
        if self.controls['key_map']['scroll_down'] !=0:
            #Zoom in
            base.camera.setY(base.camera, -(self.elapsed*20))
            #Store the camera position
            self.controls['camera_settings']['zoom'] -= .1
            #Reset the scroll state to off
            self.controls['key_map']['scroll_down'] = 0

        #Move camera left / right by mouseclick
        #mous3 is right click button
        if self.controls['key_map']['mouse3'] != 0:
            """Rotate the camera to the left or right"""

            #We know right click is being held, checked to see if it's moving
            #   left or right
            if base.mouseWatcherNode.hasMouse():
                cur_mouse_x=base.mouseWatcherNode.getMouseX()
                cur_mouse_y=base.mouseWatcherNode.getMouseY()
            else:
                #The base does not have the mouse watcher node, meaning the
                #   mouse is probably outside the game window.  If this is
                #   the case, set the cur mouse x and y to the prev coords
                cur_mouse_x = self.controls['mouse_prev_x']
                cur_mouse_y = self.controls['mouse_prev_y']

            #Check to see if the camera is being dragged.  This ensures that
            #   the camera won't move when the mouse is first clicked
            if self.controls['mouse_camera_dragging'] is True:
                #compare the previous mouse x position (if it exists).  If the
                #   cur position is greater, it means the mouse has moved to the
                #   left side of the screen, so update the camera position
                if cur_mouse_x > self.controls['mouse_prev_x']:
                    #Camera will be moving to the right
                    self.controls['camera_settings']['timer'] -= .1

                elif cur_mouse_x < self.controls['mouse_prev_x']:
                    #Camera will be moving to the left
                    self.controls['camera_settings']['timer'] += .1

                #Move the camera
                angledegrees = self.controls['camera_settings']['timer'] * 50
                angleradians = angledegrees * (math.pi / 180.0)

                #Set the X, Y as the zoom value ... see camera rotation code
                #   above for more details
                base.camera.setPos(self.controls['camera_settings']['zoom']*\
                                    math.sin(angleradians),
                                    -self.controls['camera_settings']['zoom']*\
                                    math.cos(angleradians),
                                    base.camera.getZ())

                #Set the yaw of the camera to point at the character
                base.camera.setHpr(angledegrees, 0, 0)

            #Set current x,y mouse coordinates as previous coordinates so we
            #   can do comparisons the next time the function is called
            self.controls['mouse_prev_x'] = cur_mouse_x
            self.controls['mouse_prev_y'] = cur_mouse_y
            self.controls['mouse_camera_dragging'] = True
        elif self.controls['key_map']['mouse3'] == 0:
            #The right click button has been depressed, so the camera is
            #   no longer being dragged
            self.controls['mouse_camera_dragging'] = False

        #self.entities['PC'].physics['playerWalker'].getCollisionsActive()

