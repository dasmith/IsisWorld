from odeWorldManager import *

"""
The class implementing a Kinematic Character Controller for ODE.

The KCC is the standard approach to character controllers in engines like
PhysX or Havok. Another possible implementation is the Dynamic Character
Controller, but it's much less stable and predictable, and much more inert
than the KCC.

This Kinematic Character Controller implementation has the following features:

1) Movement in 2 dimensions for walking.
2) Movement in 3 dimensions (flying) for walking ladders, swimming etc.
3) Jumping with space awareness:
	3.1) Ceiling-penetration prevention,
	3.2) Automatic crouching when you jump into a space too small for the KCC to stand in,
	3.3) The capsule should never fit into spaces too small for the KCC to stand or crouch in.
4) Walking steps
5) Crouching with space awareness. The KCC never stands up when there's not enough space above it's head.

My todo includes integrating it with PandaAI for NPCs.

Note that the KCC doesn't inherit from the kinematicObject class. There was simply no such need.
This also means, that your classes also don't need to inherit from that (or from any *Object class
for that matter) as long as they implement all methods and variables required for WorldManager
to understand them (like objectType variable and collisionCallback method).
"""

class kinematicCharacterController(object):
	def __init__(self, game, charNP=None):
		self.map = game
		self.map.worldManager = self.map.worldManager
		
		"""
		Those values don't really matter, but they need to be here for
		world manager.
		"""
		self.surfaceFriction = 0.0
		self.surfaceBounce = 0.0
		self.surfaceBounceVel = 0.0
		self.surfaceSoftERP = 0.0
		self.surfaceSoftCFM = 0.00001
		self.surfaceSlip = 0.0
		self.surfaceDampen = 2.0
		
		self.body = None
		
		self.objectType = "kinematic"
		
		"""
		Levitation, capsule radius and capsule length values.
		
		The levitation indicates how high above the ground is the capsule kept, and
		thus how high steps can the KCC walk up.
		
		These are the values I use. I still haven't worked on any "setHeight" method for the
		whole KCC, so if those values don't work for you, you'll have to find the correct ones
		by trial and error. Still, I advice leaving them as they are, because they seem to be
		the most stable ones.
		"""
		self.radius = .5
		self.walkLength = .7
		self.walkLevitation = 1.5
		self.crouchLength = .1
		self.crouchLevitation = 1.2
		
		self.length = self.walkLength
		self.levitation = self.walkLevitation
		
		"""
		Setup the Capsule for the character
		"""
		self.geom = OdeCappedCylinderGeom(self.map.worldManager.getSpace(), self.radius, self.length)
		
		self.movementParent = self.geom
		
		"""
		Setup the Ray, which serves as the character's feet, making sure
		the capsule levitates correctly above the ground.
		
		You might notice a change here comparing to version 0.9. Before,
		the footRay was a "naked" geom, now I operate solely on *Objects.
		"""
		self.footRay = rayObject(self.map)
		self.footRay.objectType = "ray"
		self.footRay.setRayGeom(5.0, [Vec3(0,0,0), Vec3(0,0,-1)])
		
		"""
		Make sure we grab the collisions from this object.
		"""
		self.footRay.collisionCallback = self.footCollision
		self.map.worldManager.addObject(self.footRay)
		
		"""
		Another ray, this time upwards. This makes sure we don't penetrate the
		ceiling no matter what, and that we don't stand up when there's not
		enough space to do it.
		"""
		self.envCheckerRay = rayObject(self.map)
		self.envCheckerRay.objectType = "ray"
		self.envCheckerRay.setRayGeom(2.0, [Vec3(0, 0, 0), Vec3(0, 0, 1.0)])
		
		"""
		Again, redirect the collision callback to this class.
		"""
		self.envCheckerRay.collisionCallback = self.envCheckerCollision
		self.map.worldManager.addObject(self.envCheckerRay)
		
		"""
		Set the bitmasks for the whole object.
		"""
		self.setCatColBits("generalKCC")
		
		"""
		Variables used for movement, jumping and falling.
		"""
		self.speed = [0, 0]
		self.jumpStartPos = 0.0
		self.jumpTime = 0.0
		self.jumpSpeed = 0.0
		self.fallStartPos = 0.0
		self.fallSpeed = 0.0
		self.fallTime = 0.0
		
		"""
		State variable which can take one of four values:
		ground, jumping, falling or fly
		"""
		self.state = ""
		
		"""
		Crouching is a special kind of a state. It's not a value of the
		self.state variable because you can, for example, fall while crouching.
		"""
		self.isCrouching = False
		
		"""
		This is used by stability insurance.
		"""
		self.prevfootContact = None
		self.footContact = None
		self.envCheckerContact = None
		
		self.map.worldManager.addObject(self)
	
	def getGeom(self):
		return self.geom
	
	def setCatColBits(self, name):
		self.bitsName = name
		self.geom.setCollideBits(bitMaskDict[name][0])
		self.geom.setCategoryBits(bitMaskDict[name][1])
		self.footRay.setCatColBits(name)
	
	def destroy(self):
		self.map.removeObject(self)
		self.map.worldManager.removeObject(self)
		self.geom.destroy()
		
		self.map.worldManager.removeObject(self.footRay)
		self.map.worldManager.removeObject(self.envCheckerRay)
		self.footRay.destroy()
		self.envCheckerRay.destroy()
		
		del self.map
		del self.geom
		del self.footRay
		
	def setPos(self, pos):
		self.geom.setPosition(pos)
		self.currentPos = pos
	
	def getPos(self):
		return self.currentPos
	
	"""
	Convenience method for setting the capsule's heading.
	"""
	def setH(self, h):
		quat = self.getQuat()
		hpr = quat.getHpr()
		hpr[0] = h
		quat.setHpr(hpr)
		self.setQuat(quat)
		
	def setQuat(self, quat):
		self.geom.setQuaternion(Quat(quat))
		
	def getQuat(self):
		return self.geom.getQuaternion()
	
	"""
	Start crouching
	"""
	def crouch(self):
		self.levitation = self.crouchLevitation
		self.geom.setParams(self.radius, self.crouchLength)
		self.isCrouching = True
		return True
	
	"""
	Stop crouching
	"""
	def crouchStop(self):
		if not self.isCrouching:
			return False
		
		"""
		Did the envCheckerRay detect any collisions? If so, prevent the
		KCC from standing up as there's not enough space for that.
		
		This removes the need for crouch locking triggers.
		"""
		if self.envCheckerContact is not None:
			return False
		
		self.levitation = self.walkLevitation
		self.geom.setParams(self.radius, self.walkLength)
		
		self.isCrouching = False
		
		return True
		
	"""
	Handle a collision of the capsule.
	"""
	def collisionCallback(self, entry, object1, object2):
		"""
		Ignore collisions with following object types...
		"""
		if not entry.getNumContacts() or object2.objectType in ["trigger", "ray", "ccd"]:
			return
		
		if object2.objectType != "dynamic":
			for i in range(entry.getNumContacts()):
				point = entry.getContactPoint(i)
				geom = entry.getContactGeom(i)
				depth = geom.getDepth()
				normal = geom.getNormal()
				
				if entry.getGeom1() == self.geom:
					for i in range(3):
						self.currentPos[i] += depth * normal[i]
				else:
					for i in range(3):
						self.currentPos[i] -= depth * normal[i]
			
			"""
			Make sure we don't jump through the ceiling.
			"""
			if normal[2] == -1:
				if self.state == "jumping":
					self.fallStartPos = self.geom.getPosition()[2]
					self.fallSpeed = 0.0
					self.fallTime = 0.0
					self.state = "falling"
	
	"""
	Handle a collision involving the environment checker ray.
	"""
	def envCheckerCollision(self, entry, object1, object2):
		if not entry.getNumContacts():
			return
		if object2 is self:
			return
		
		"""
		Get the lowest contact.
		"""
		for i in range(entry.getNumContacts()):
			contact = entry.getContactPoint(i)[2]
			
			if self.envCheckerContact is None or (contact < self.envCheckerContact):
				self.envCheckerContact = contact
	
	"""
	Handle a collision of the foot ray.
	"""
	def footCollision(self, entry, object1, object2):
		if not entry.getNumContacts():
			return
		if object2 is self:
			return
		
		for i in range(entry.getNumContacts()):
			contact = entry.getContactPoint(i)[2]
			
			if self.footContact is None or (contact > self.footContact):
				self.footContact = contact
	
	"""
	UPDATE THE KCC
	"""
	def update(self, stepSize):
		pos = self.geom.getPosition()
		
		height = None
		if self.footContact is not None:
			height = self.geom.getPosition()[2] - self.footContact
		
		newPos = self.currentPos
		
		if self.envCheckerContact is not None:
			d = self.envCheckerContact - pos[2]
			
			if self.isCrouching:
				limit = 0.55
			else:
				limit = 1.5
				
			if d < limit and height < self.levitation:
				self.crouch()
				self.footContact = self.prevfootContact
		
		if self.state == "fly" :
			pass
			
		elif self.state == "jumping":
			newPos[2] = self.processJump(newPos, stepSize, self.footContact)
		
		elif height is None:
			newPos = self.fall(newPos, stepSize, self.footContact)
			
		elif height > self.levitation + 0.01 and height < self.levitation + 0.65 and self.state == "ground":
			newPos = self.stickToGround(newPos, stepSize, self.footContact)
		
		elif height > self.levitation + 0.01:
			newPos = self.fall(newPos, stepSize, self.footContact)
			
		elif height <= self.levitation + 0.01:
			newPos = self.stickToGround(newPos, stepSize, self.footContact)
		
		speedVec = Vec3(self.speed[0], self.speed[1], 0)
		try:
			quat = self.movementParent.getQuaternion()
		except AttributeError:
			quat = self.movementParent.getQuat(render)
			
		speedVec = quat.xform(speedVec)
		newPos += speedVec * stepSize
			
		self.currentPos = newPos
		self.geom.setPosition(newPos)
		
		self.envCheckerRay.setPos(newPos)
		
		rayPos = Vec3(newPos)
		rayPos[2] -= self.length/2
		self.footRay.setPos(rayPos)
		
		npPos = Vec3(newPos)
		npPos[2] -= self.levitation + 0.15
		
		self.prevfootContact = self.footContact
		self.footContact = None
		self.envCheckerContact = None
	
	"""
	METHODS FOR PROCESSING STATES
	"""
	def processJump(self, newPos, stepSize, footContact):
		self.jumpTime += stepSize
		
		self.fallSpeed = self.jumpSpeed*self.jumpTime + (-9.81)*(self.jumpTime)**2
		
		np = self.jumpStartPos + self.fallSpeed
		
		if footContact is not None and np <= footContact + self.levitation:
			self.state = "ground"
			return footContact + self.levitation
		
		return np
		
	def stickToGround(self, newPos, stepSize, footContact):
		if self.fallSpeed:
			self.fallCallback(self.fallSpeed)
		self.fallSpeed = 0.0
		
		self.state = "ground"
		
		newPos[2] = footContact + self.levitation
		
		return newPos
		
	def fall(self, newPos, stepSize, footContact):
		if self.state != "falling":
			self.fallStartPos = self.geom.getPosition()[2]
			self.fallSpeed = 0.0
			self.fallTime = 0.0
			self.state = "falling"
		else:
			self.fallTime += stepSize
			self.fallSpeed = (-9.81)*(self.fallTime)**2
		newPos[2] = self.fallStartPos + self.fallSpeed
		return newPos
	
	"""
	This is called when the KCC hits the ground after a fall.
	Here you can put health related stuff.
	"""
	def fallCallback(self, speed):
		print "A character has hit the ground with speed:", speed
	
	def setSpeed(self, x, y):
		self.speed[0] = x
		self.speed[1] = y
	
	"""
	Start a jump
	"""
	def jump(self):
		if self.state != "ground":
			return
		self.jumpSpeed = 8.0
		self.jumpStartPos = self.geom.getPosition()[2]
		self.jumpTime = 0.0
		self.state = "jumping"
		###print "JUMP"
