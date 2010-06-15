from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
import sample_loaders
from object_loader import ObjectLoader

FILE = "testWorld.txt"

class Test(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)

		sample_loaders.setLoader(self.loader)
		loader = ObjectLoader(sample_loaders.compile(), self.render)
		loader.parseFile(FILE)

		self.taskMgr.add(self.spinCameraTask, "SpinCameraTAsk")
	def spinCameraTask(self, task):
		angle = task.time*10.0
		angleRads = angle*(pi/180.0)
		self.camera.setPos(40*sin(angleRads), -40.0*cos(angleRads), 10)
		self.camera.setHpr(angle, -15, 0)
		return Task.cont

test = Test()
test.run()