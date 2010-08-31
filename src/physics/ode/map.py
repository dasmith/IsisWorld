from direct.actor import Actor
from pandac.PandaModules import *

from system.odeWorldManager import *
from system.trigger import *
from character import *
from inventory import *

from assets.door import *
from assets.chair import *
from weapons.grenade import *
from weapons.guns import *

"""
The map class loads models from an Egg file and creates python objects
according to tags set on the models.
"""
class map(object):
	def __init__(self):
		self.defaultShowCCD = False
		
		"""
		A dictionary with object types.
		Makes it easier to manage what gets removed and when.
		"""
		self.mapObjects = {
			"static": [],
			"triggers": [],
			"characters": [],
			"dynamics": [],
			"kinematics": [],
			}
			
		self.mapFile = "./graphics/models/map"
		
		"""
		Setting up an ODE World Manager.
		"""
		self.worldManager = odeWorldManager()
		"""
		I found 60 Hz to be an optimal time step. However, with simple maps
		and more powerful computers this value might become too small,
		occasionally causing the ODE objects to move not fluently.
		Adjust according to needs.
		"""
		self.simTimeStep = 1.0/60.0
	
	def create(self):
		"""
		Load the map Egg file and get it's root node
		"""
		# MAP PARENT
		self.map = loader.loadModel(self.mapFile)
		self.map.reparentTo(render)
		self.mapRootNode = self.map.find("-PandaNode")
		
		"""
		See the processBranch method definition lower
		"""
		self.processBranch(self.mapRootNode)
		
		"""
		Start the simulation at the required time step size
		"""
		self.worldManager.startSimulation(self.simTimeStep)
		
		"""
		Enable player
		"""
		self.player.enableInput()
		self.player.enableMovement()
	
	def destroy(self):
		print "DESTROYING MAP"
		
		render.clearLight()
		self.worldManager.stopSimulation()
		
		print "map -> destroy -> map objects:\n"+"="*60
		print self.mapObjects, "\n"+"="*60
		
		for catName, category in self.mapObjects.iteritems():
			for obj in list(category):
				print "map -> destroy -> removing", obj, obj.objectType
				obj.destroy()
		
		print "map -> destroy -> finished removing objects"
		self.mapObjects = {}
		
		print "map -> destroy -> removing player"
		self.player.destroy()
		print "map -> destroy -> destroy world manager"
		self.worldManager.destroy()
		print "map -> destroy -> world manager destroyed, unload map model"
		loader.unloadModel(self.map)
		self.mapRootNode.remove()
		self.map.removeNode()
		
		del self.mapObjects
		del self.worldManager
		del self.player
		del self.map
		del self.mapRootNode
		
		print "FINISHED DESTROYING MAP"
		
	"""
	This method is used to recursively process a branch of the map's Egg file.
	"""
	def processBranch(self, branch):
		"""
		Loop through the parent node's children
		"""
		for childNode in branch.getChildren():
			"""
			Get the type tag, which indicates what kind of object
			we want this node to become.
			
			Obviously, you can change the name of the tag to whatever
			you want.
			"""
			type = childNode.getTag("type")
			
			"""
			If this child node represents another branch, process it
			as well.
			"""
			if childNode.getNumChildren() > 0:
				self.processBranch(childNode)
			
			"""
			If this node has no type, just do nothing and continue looping.
			This is usefull, for example, when you just want to parent
			something to an empty for convenience, and not for some
			mechanics-related reason.
			"""
			if not type:
				continue
			
			"""
			If there is a type tag, get the appropriate method for
			loading this kind of objects.
			
			Look into ./graphics/blender/map.egg file and you'll see
			that the tags assigned to objects reesamble the method names
			"""
			methodName = "self."+type
			method = eval(methodName)
			method(childNode)
	
	"""
	Remove object when you don't know it's category
	"""
	def removeObject(self, object):
		for category in self.mapObjects.keys():
			if object in self.mapObjects[category]:
				self.removeObjectByCategory(object, category)
	
	"""
	Remove object from a specified category
	"""
	def removeObjectByCategory(self, object, category):
		self.worldManager.removeObject(object)
		try:
			idx = self.mapObjects[category].index(object)
			self.mapObjects[category].pop(idx)
			return True
		except:
			return False
	
	# LOADER METHODS
	
	"""
	This method creates a static OdeBoxGeom from an object
	created in a 3D modeling program.
	"""
	def solidBoxGeom(self, node):
		pos = node.getPos(render)
		quat = node.getQuat(render)
		
		object = staticObject(self)
		
		"""
		See the definition of this method for details
		"""
		object.setBoxGeomFromNodePath(node)
		
		object.setPos(pos)
		object.setQuat(quat)
		
		object.setCatColBits("environment")
		
		self.worldManager.addObject(object)
		
		self.mapObjects["static"].append(object)
	
	"""
	This is similar to solidBoxGeom, but instead of a box it creates
	a detailed representation of the given model using Ode's Trimesh.
	
	WARRNING: Trimesh is generally a rather unstable geom. The KCC
	may tunnel through it or 'shake' noticably when colliding with it.
	Also, dynamic objects, most importantly Spheres, sometimes 'sink'
	in trimeshes for no apparent reason.
	
	This is why I advice against using TriMeshes whenever they can be
	replaced with boxes. Usually boxes, or other shapes which can't
	currently be loaded automatically with this system, should do
	the trick. Try to use TriMesh only for details that can't be
	approximated.
	"""
	def solidTriMeshGeom(self, node):
		static = staticObject(self)
		static.setNodePath(node)
		
		static.setTrimeshGeom(node)
		
		static.setCatColBits("environment")
		
		self.worldManager.addObject(static)
		
		self.mapObjects["static"].append(static)
		return static
		
	# Lights
	"""
	Lights can't be exported with Chicken, so I use empties. For now
	there's a lot of hardcodding here, but this is fairly standard stuff.
	"""
	def alight(self, node):
		alight = AmbientLight("ambientLight")
		alight.setColor(Vec4(.7, .7, .7, 1.0))
		alightNP = self.mapRootNode.attachNewNode(alight)
		render.setLight(alightNP)
		return alightNP
		
	def dlight(self, node):
		dlight = DirectionalLight("directionalLight")
		dlight.setDirection(Vec3(node.getHpr()))
		dlight.setColor(Vec4(0.3, 0.3, 0.3, 1))
		dlightNP = self.mapRootNode.attachNewNode(dlight)
		render.setLight(dlightNP)
		return dlightNP
		
	def plight(self, node):
		plight = PointLight('plight')
		plight.setColor(VBase4(0.2, 0.2, 0.2, 1))
		plightNP = self.mapRootNode.attachNewNode(plight)
		plightNP.setPos(node.getPos(self.mapRootNode))
		render.setLight(plightNP)
		return plightNP
	
	"""
	These are gemeplay objects.
	"""
	# Assets
	def chair(self, node):
		c = chair(self, node)
		self.mapObjects["static"].append(c)
		return c
	
	"""
	The Player's starting position is set with an empty with
	type tag set to 'playerPosition'.
	"""
	def playerPosition(self, node):
		self.player = playerController(self, None)
		self.player.setPos(node.getPos())
		self.player.setQuat(node.getQuat())
		return self.player
	
	"""
	Here I process other empties, that are not lights nor playerPosition.
	"""
	def position(self, node):
		pos = node.getPos(render)
		quat = node.getQuat(render)
		
		"""
		Get the item tag
		"""
		item = node.getTag("item")
		
		if item == "box":
			asset = pickableBox()
		elif item == "ball":
			asset = pickableBall()
		elif item == "grenade":
			asset = grenade()
		elif item == "door":
			asset = door()
			asset.state = "close"
			
		elif item == "gun":
			asset = gun()
		elif item == "rifle":
			asset = assaultRifle()
		elif item == "shotgun":
			asset = shotgun()
		
		"""
		I have separated creating an item from actually putting it into the world.
		I find it more convenient to do it this way.
		"""
		print "Creating:", item
		asset.setupGeomAndPhysics(self, pos, quat)
		asset.showCCD = self.defaultShowCCD
		
		"""
		Add the object to a currect category based on yet another tag.
		This could also be done with a variable inside the actuall
		object class.
		"""
		if node.getTag("category") == "dynamic":
			self.mapObjects["dynamics"].append(asset)
		elif node.getTag("category") == "kinematic":
			self.mapObjects["kinematics"].append(asset)
		
		return asset
	
	"""
	Setup triggers.
	
	If you've used the previous version of my Framework, you might have
	had noticed tha I was using a trigger to lock Player to crouching there.
	This is no longer needed.
	"""
	def fly_trigger(self, node):
		trigger = odeTriggerLadder(self, node, "ladderTrigger")
		self.mapObjects["triggers"].append(trigger)
		return trigger
