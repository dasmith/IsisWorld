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
        # Load the environment model
        self.environ = self.loader.loadModel("models/environment")
        # Reparent model to render
        self.environ.reparentTo(self.render)
        # Apply scale and position transforms
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0)
        
        # Add the spinCameraTask
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        self.addAModel(modelName)

        # Testing if i can use os.system
        # Yes, I can do it. 
        # I could probably use os.system to make calls to egg_optchar
        #print "Calling os.system"
        #os.system("echo hi")
        self.drawGUI()

    def drawGUI(self):
        self.reloadButton = DirectButton(text=("Reload Model"), scale=.15,
                                         command=self.buttonResp,
                                         pos = (0, 0, -0.85))
        #textInp = "This will be executed by the shell"
        #self.textInp = OnscreenText(text = textInp, pos = (0.95, -0.95),
              #  scale = 0.07, fg=(1, 0.5, 0.5, 1), align=TextNode.ACenter,
             #   mayChange = 1)

        # Clear the text in the DirectEntry field
        def clearText():
            self.textInp.enterText('')

        def systemCallText(command):
            os.system("echo " + command)
            clearText()

        # add button
        self.textInp = DirectEntry(text = "", scale=.05, command=systemCallText, 
                initialText="This will go to shell", numLines = 2, focus = 1, 
                focusInCommand = clearText)

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
        self.model = loader.loadModel(self.modelName)
        self.model.reparentTo(self.render)

    def addAModel(self, model):
        self.model = loader.loadModel(model)
        self.model.reparentTo(self.render)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Please specify a model to show. Using models/panda-model_copy as the default."
        modelName = "models/panda-model_copy"
    else:
        modelName = sys.argv[1]
    md = ModelDisplayer(modelName)
    md.run()
