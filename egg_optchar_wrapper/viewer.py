# Rahul Rajagopalan
# Graphical frontend for egg-optchar to make it a bit easier for users
# to tweak .egg models. This script displays the model in question and
# reloads it after every change to provide visual feedback.

from math import pi, sin, cos
import os
import sys
#import direct.directbase.DirectStart
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.DirectGui import *
from direct.directtools.DirectGeometry import LineNodePath
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
        
        # add Isis Agent
        self.actor= Actor("../media/models/boxman",
                          {"walk":"../media/models/boxman-walk", 
                           "idle": "../media/models/boxman-idle"})
        self.actor.setScale(1.0)
        self.actor.setH(0)
        # move actor to the left
        self.actor.setPos(0,-6,0)
        self.actor.loop("walk")

        self.actor.reparentTo(render)
        # Expose agent's right hand joint to attach objects to
        self.player_right_hand = self.actor.exposeJoint(None, 'modelRoot', 'Hand.R')
        self.player_left_hand  = self.actor.exposeJoint(None, 'modelRoot', 'Hand.L')
        
        
        # add lines 
        lines = LineNodePath(parent = render, thickness = 4.0, colorVec = Vec4(1, 0, 0, 1))
        lines.reset()
        lines.drawLines([((0,0,0),(0,0,5)),
                         ((0,0,0),(0,5,0)),
                         ((0,0,0),(5,0,0))])
        lines.create()
        
        self.spinning = False
        # Add the spinCameraTask
        base.camera.setPos(0,20,20) 
        base.camera.lookAt(0,0,0) 
          # Gives the camera an initial position and rotation. 

        #self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        self.model = None
        self.loadModel(modelName)

        self.camera.lookAt(self.model)
        self.drawGUI()
        self.accept("space", self.toggleSpinning)
    
    #http://www.panda3d.org/forums/viewtopic.php?t=9868
    #http://www.panda3d.org/forums/viewtopic.php?t=2248            
    def toggleSpinning(self):
        if self.spinning:
            self.taskMgr.remove("SpinCameraTask")
            self.camera.setPos(0, 0, 3)
            self.camera.setHpr(0, 0, 0)
        else:
            self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        self.spinning = not self.spinning
    def drawGUI(self):

        def systemCallText():
            x,y,z = self.model.getPos(render)
            h,p,r = self.model.getHpr(render)
            sx,sy,sz = self.model.getScale()
            newName = self.modelName[0:-4] +"-new.egg"
            theCmd = "egg-trans -o " + newName + " "
            theCmd += "-TT %f,%f,%f " % (x,y,z)
            theCmd += "-TS %f,%f,%f " % (sx,sy,sz)
            theCmd += "-TR %f,%f,%f " % (h,p,r)
            theCmd += "-cs z-up -t " # Standardize coordinate system
            theCmd += "-T " # Collapse equivalent texture references.
            theCmd += "-F " # Flatten out transforms.
            #theCmd += "-C " # Clean out higher-order polygons by subdividing into triangles.
            theCmd +=  self.modelName
            print theCmd
            os.system(theCmd)
            self.loadModel(newName)
    
        self.transformButton = DirectButton(text=("Transform Model"), scale=.15,
                                            command=systemCallText,
                                            pos = (0, 0, -0.85))


    def spinCameraTask(self, task):
        # From the Panda3D tutorial, I left it in because it looks a bit
        # nicer than a fixed camera, and previously the camera wasn't
        # perfectly centered
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont

    def loadModel(self, name):
        # We can refresh models by replacing the model with itself
        # That is, detach the model, and then reload it
        if self.model:
            self.model.detachNode()
            loader.unloadModel(self.model)
        self.model = loader.loadModel(name)
        self.model.reparentTo(self.render)
        self.model.place()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Please specify a model to show. Using pandaModCopy.egg as the default."
        modelName = "/c//Users/Rahul_2/Documents/IsisWorldUROP/egg_optchar_wrapper/pandaModCopy.egg"
    else:
        modelName = sys.argv[1]
    md = ModelDisplayer(modelName)
    md.run()
