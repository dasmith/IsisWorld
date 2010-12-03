from math import pi, sin, cos

import os
import sys
import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.DirectGui import *

def buttonResp():
    print "Button was clicked!!"

class ModelDisplayer(ShowBase):
    
    def __init__(self):
        ShowBase.__init__(self)

        # Load the environment model
        self.environ = self.loader.loadModel("models/environment")
        # Reparent model to render
        self.environ.reparentTo(self.render)
        # Apply scale and position transforms
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)
        
        # Add the spinCameraTask
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        self.addAModel("models/teapot")

        # Testing if i can use os.system
        # Yes, I can do it. 
        # I could probably use os.system to make calls to egg_optchar
        print "Calling os.system"
        os.system("echo hi")


        b = DirectButton(text=("Click me!"), scale=.25, command=buttonResp)
        # The teapot stays there, though...
        #self.addAModel("models/box")
        #print "added box"

    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

    def addAModel(self, model):
        self.pandaActor = loader.loadModel(model)
        #self.pandaActor = Actor("models/teapot")
        #self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.reparentTo(self.render)
        #self.pandaActor.loop("walk") 

md = ModelDisplayer()
md.run()

def start():
    print "sys.argv: ", sys.argv
    print "len(sys.argv) ", len(sys.argv)
    if len(sys.argv) != 2:
        print "Please specify a model to show. Using panda.egg as the default."
        modelName = "panda.egg"
    else:
        modelName = sys.argv[1]
    viewCmd = 'pview %s' % modelName
    
    # Doesn't actually display?
    #panda = render.attachNewNode("panda.egg")
    
    #os.system(viewCmd)
    inp = raw_input("What do you want to do?")
    print "You inputted ", inp
