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
            self.timer -= .01
            angledegrees = self.timer * 50
            angleradians = angledegrees * (math.pi / 180.0)
            base.camera.setPos(self.zoom* math.sin(angleradians), -self.zoom * math.cos(angleradians), base.camera.getZ())
            base.camera.setHpr(angledegrees, 0, 0)

        """Zoom camera in / out"""
        #ZOOM IN
        if self.controlMap['zoom-in'] !=0:
            #Zoom in
            base.camera.setY(base.camera, +(self.elapsed*10))
            #Store the camera position
            self.zoom -= self.elapsed*10

        #ZOOM OUT
        if self.controlMap['zoom-out'] !=0:
            #Zoom out
            base.camera.setY(base.camera, -(self.elapsed*10))
            #Store the camera position
            self.zoom += self.elapsed*10

        return Task.cont


