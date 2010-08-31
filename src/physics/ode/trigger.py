from system.odeWorldManager import staticObject

"""
A generic Area Trigger for ODE

IMPORTANT

Don't confuse odeTrigger objects with isTrigger value of the OdeGeomData class.
These are two different things.

The odeTrigger class represents an Area Trigger, with it's required behaviour,
which supports the process of entering and exiting the trigger.

The isTrigger = True setting in OdeGeomData, on the other hand, is only meant
to tell the OdeWorldManager to handle some object's collision in a specific way,
i.e. get one-direction collisions and execute callbacks, but don't set contact
joints.

Obviously, odeTriggers set their isTrigger to true, but so do Rays and CCD helper
geoms, which are not considered area triggers.


You can also easily change this into a kinematic object, by changing it's parent
class to kinematicObject, adding a dummy node (as self.nodePath) for animating
with Panda's intervals (or however else), and calling kinematicObject.update(self,
stepSize) in the update method. However, for static triggers it's pointless.
"""
class odeTrigger(staticObject):
	def __init__(self, map, model, name):
		staticObject.__init__(self, map)
		
		"""
		The message that will be sent, suffixed with _enter or _exit when
		a geom, which this trigger is meant to collide with, enters or exits
		the trigger.
		"""
		
		self.objectType = "trigger"
		
		self.message = ""
		
		self.oldObjects = []
		self.newObjects = []
		
		"""
		Setting a required shape
		"""
		if isinstance(model, list):
			x = model[0]; y = model[1]; z = model[2]
			self.setBoxGeom(Vec3(x, y, z))
		elif isinstance(model, float):
			self.setSphereGeom(model)
		else:
			self.setNodePath(model)
			self.setTrimeshGeom(model)
			self.nodePath.detachNode()
		
		self.map.worldManager.addObject(self)
	
	def destroy(self):
		staticObject.destroy(self)
		del self.oldObjects
		del self.newObjects
	
	def collisionCallback(self, entry, object1, object2):
		print "trigger collision!"
		if object2 not in self.newObjects:
			self.newObjects.append(object2)
		
	"""
	Find out which objects left the area and add the new ones.
	"""
	def update(self, stepSize):
		for object in self.newObjects:
			if object not in self.oldObjects:
				messenger.send(self.message+"_enter", [object, self])
		for object in self.oldObjects:
			if object not in self.newObjects:
				messenger.send(self.message+"_exit", [object, self])
				
		self.oldObjects = list(self.newObjects)
		self.newObjects = []
		

"""
An example of a trigger I use to make ladders.
"""
class odeTriggerLadder(odeTrigger):
	def __init__(self, map, model, name):
		odeTrigger.__init__(self, map, model, name)
		self.setCatColBits("charTrigger")
		self.message = "ladder_trigger"
