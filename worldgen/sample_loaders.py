from direct.actor.Actor import Actor
from direct.showbase.ShowBase import ShowBase

LOADER = None

class PandaLoader():
	def generate(self):
		panda = Actor("models/panda-model", {"walk": "models/panda-walk4"})
		panda.setScale(.005, .005, .005)
		return panda

class ForestLoader():
	def generate(self):
		global LOADER
		if LOADER:
			forest = LOADER.loadModel("models/environment")
		else:
			LOADER = showBase().loader
			forest = LOADER.laodModel("models/environment")
		forest.setScale(0.025, 0.025, 0.025)
		return forest

def compile():
	return {"panda":PandaLoader(),
		"forest":ForestLoader()}

def setLoader(l):
	global LOADER
	LOADER = l