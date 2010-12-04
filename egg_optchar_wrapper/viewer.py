from math import pi, sin, cos
import os
import sys
import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText
from pandac.PandaModules import *

class ModelDisplayer(ShowBase):
    
    def __init__(self, modelName):
        ShowBase.__init__(self)
        self.modelName = modelName
        # Load the environment model (right now using models/environment)
        self.environ = self.loader.loadModel("models/environment")
        # Reparent model to render
        self.environ.reparentTo(self.render)
        # Apply scale and position transforms
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)
        
        # Add the spinCameraTask
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        self.addAModel(modelName)

        self.drawGUI()

    def drawGUI(self):
        self.reloadButton = DirectButton(text=("Reload Model"), scale=.15,
                                         command=self.reloadModel,
                                         pos = (0, 0, -0.85))

        # Clear the text in the DirectEntry field
        def clearText():
            self.textInp.enterText('')

        def systemCallText(command):
            theCmd = "egg-optchar -o " + self.modelName + " " + \
                     command + " " + self.modelName 
            print theCmd
            os.system(theCmd)
            self.reloadModel()
            clearText()

        # add button
        self.textInp = DirectEntry(text = "", scale=.05, command=systemCallText, 
                initialText="This will go to shell", numLines = 5, focus = 1, 
                focusInCommand = clearText)

    def spinCameraTask(self, task):
        # From the Panda3D tutorial, I left it in because it looks a bit
        # nicer than a fixed camera, and previously the camera wasn't
        # perfectly centered
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

    def reloadModel(self):
        # We can refresh models by replacing the model with itself
        # That is, detach the model, and then reload it
        self.model.detachNode()
        loader.unloadModel(self.model)
        self.model = loader.loadModel(self.modelName)
        self.model.reparentTo(self.render)

    def addAModel(self, model):
        self.model = loader.loadModel(model)
        self.model.reparentTo(self.render)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Please specify a model to show. Using pandaModCopy.egg as the default."
        modelName = "/c//Users/Rahul_2/Documents/IsisWorldUROP/egg_optchar_wrapper/pandaModCopy.egg"
    else:
        modelName = sys.argv[1]
    md = ModelDisplayer(modelName)
    md.run()
