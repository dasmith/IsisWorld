from math import pi, sin, cos
import os
import sys
import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.DirectGui import *

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

        self.addAModel("models/panda-model_copy")

        # Testing if i can use os.system
        # Yes, I can do it. 
        # I could probably use os.system to make calls to egg_optchar
        #print "Calling os.system"
        #os.system("echo hi")


        b = DirectButton(text=("Reload Model"), scale=.25,
                         command=self.buttonResp)

    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

    def buttonResp(self):
        # Example of how to replace a model
        # We could refresh models by replacing the model with
        # itself
        print "Button was clicked!!"
        self.model.detachNode()
        loader.unloadModel(self.model)
        self.model = loader.loadModel('models/panda-model_copy')
        self.model.reparentTo(self.render)

    def addAModel(self, model):
        self.model = loader.loadModel(model)
        self.model.reparentTo(self.render)

if __name__ == '__main__':
    #print "sys.argv: ", sys.argv
    #print "len(sys.argv) ", len(sys.argv)
    if len(sys.argv) != 2:
        print "Please specify a model to show. Using models/panda-model_copy as the default."
        modelName = "models/panda-model_copy"
    else:
        modelName = sys.argv[1]
    md = ModelDisplayer()
    md.run()
