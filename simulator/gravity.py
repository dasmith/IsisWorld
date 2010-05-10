#from direct.stdpy.threading import Thread, Lock
from threading import Thread, Lock # the panda3d threading modules don't work well
from pandac.PandaModules import  CollisionTraverser, CollisionRay, CollisionNode, CollisionHandlerQueue
from pandac.PandaModules import VBase3,VBase4,Vec3,Vec4,BitMask32

class ObjectGravitySimulator:
	"""
	"""
	falling_velocity = 10.0  # Z units per second
	
	def __init__(self, attach_object, object_bottom_buffer_distance = 0.1):
		#print "creating ObjectGravitySimulator for " + attach_object.name + ".\n"
		self.attach_object = attach_object
		self.object_bottom_buffer_distance = object_bottom_buffer_distance
		self.initialize_collision_handling()
	
	def initialize_collision_handling(self):
		self.collision_handling_mutex = Lock()
		
		self.cTrav = CollisionTraverser()
		
		self.groundRay = CollisionRay()
		self.groundRay.setOrigin(0,0,1000)
		self.groundRay.setDirection(0,0,-1)
		self.groundCol = CollisionNode(self.attach_object.name + "_collision_node")
		self.groundCol.setIntoCollideMask(BitMask32.bit(0))
		self.groundCol.setFromCollideMask(BitMask32.bit(0))
		self.groundCol.addSolid(self.groundRay)
		self.groundColNp = self.attach_object.render_model.attachNewNode(self.groundCol)
		self.groundHandler = CollisionHandlerQueue()
		self.cTrav.addCollider(self.groundColNp, self.groundHandler)
		
		# Uncomment this line to see the collision rays
		#self.groundColNp.show()
		
                #Uncomment this line to show a visual representation of the 
		#collisions occuring
                #self.cTrav.showCollisions(render)

	def destroy_collision_handling(self):
		self.collision_handling_mutex.acquire()
    
	def handle_collisions(self, seconds):
		self.collision_handling_mutex.acquire()
		self.groundCol.setIntoCollideMask(BitMask32.bit(0))
		self.groundCol.setFromCollideMask(BitMask32.bit(1))
		
		# Now check for collisions.
		self.cTrav.traverse(render)
		
		# Adjust the object's Z coordinate.  If the object's ray hit anything,
		# update its Z.
		
		current_z = self.attach_object.render_model.getZ() - self.object_bottom_buffer_distance
		entries = []
		for i in range(self.groundHandler.getNumEntries()):
			entry = self.groundHandler.getEntry(i)
			if (entry.getSurfacePoint(render).getZ() - 0.001 < current_z):
				entries.append(entry)

		entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
					     x.getSurfacePoint(render).getZ()))
		if (len(entries)>0):
			surface_z = entries[0].getSurfacePoint(render).getZ()
			#print "> " + self.attach_object.name + " is falling toward " + entries[0].getIntoNode().getName() + "\n"
			new_z = current_z - (self.falling_velocity * seconds)
			if (new_z < surface_z):
				new_z = surface_z
			if ((new_z > current_z + 0.00001) or (new_z < current_z - 0.00001)):
				self.attach_object.render_model.setZ(new_z + self.object_bottom_buffer_distance)
		
		self.groundCol.setIntoCollideMask(BitMask32.bit(0))
		self.groundCol.setFromCollideMask(BitMask32.bit(0))
		self.collision_handling_mutex.release()


	def step_simulation_time(self, seconds):
		#print "stepping object."
		self.handle_collisions(seconds)

class ObjectGravitySimulatorList:
	"""
	"""
	def __init__(self):
		self.attach_objects = []

	def add_attach_object(self, attach_object, object_bottom_buffer_distance=0):
		object_gravity_simulator = ObjectGravitySimulator(attach_object, object_bottom_buffer_distance=object_bottom_buffer_distance)
		self.attach_objects.append(object_gravity_simulator)
		return object_gravity_simulator

	def step_simulation_time(self, seconds):
		for attach_object in self.attach_objects:
			attach_object.step_simulation_time(seconds)

	def destroy_collision_handling(self):
		for attach_object in self.attach_objects:
			attach_object.destroy_collision_handling()