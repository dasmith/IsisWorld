

# -*- coding: utf-8 -*-
# Copyright Tom SF Haines
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import posixpath

from pandac.PandaModules import *

import math

from pandac.PandaModules import *
from direct.showbase import DirectObject

def eggToOde(np,surfaceType): # ,depth = 0
  """Given a node path, usually from an egg that has been octreed, this constructs the same structure in ode, using a space for each node with tri-meshes within. Implimented as a generator so it doesn't screw with the framerate; final yield will return the root geom, or None if there was nothing to collide with. (This geom will probably be a space, but only probably.)"""
  output = []
  np.flattenLight()

  # Check if there is any mesh data at this level that we need to turn into a trimesh...
  if np.node().isGeomNode(): # np.node().getClassType()==CollisionNode.getClassType()
    tmd = OdeTriMeshData(np,True)
    tmg = OdeTriMeshGeom(tmd)
    
    nt = np.getNetTransform()
    tmg.setPosition(nt.getPos())
    tmg.setQuaternion(nt.getQuat())
    
    output.append(tmg)
    #print ('|'*depth) + 'geom, ' + str(np.node().getClassType()) + ', ' + str(tmg.getNumTriangles())
  else:
    #print ('|'*depth) + 'notgeom, ' + str(np.node().getClassType())
    # Check the children for useful data...
    children = np.getChildren()
    for i in xrange(children.size()):
      child = children[i]
      
      for r in eggToOde(child,surfaceType): # ,depth+1
        yield None
        geom = r
      if geom!=None:
        output.append(geom)

  if len(output)==0:
    yield None
  else:
    space = OdeSimpleSpace()
    for geom in output:
      space.add(geom)
      space.setSurfaceType(geom,surfaceType)
    yield OdeUtil.spaceToGeom(space)

class PhysicsWorldManager(DirectObject.DirectObject):
  """This creates the various ODE core objects, and exposes them to other plugins. Should be called ode."""
  def __init__(self):
    # Setup the physics world...
    erp = 0.8#float(xml.find('param').get('erp',0.8))
    cfm = 1e-3#float(xml.find('param').get('cfm',1e-3))
    slip = 0.0#float(xml.find('param').get('slip',0.0))
    dampen = 0.1#float(xml.find('param').get('dampen',0.1))

    print "INITTTTTTTTT"
    self.world = OdeWorld()
    self.world.setGravity(0.0, 0.0, -9.81)#self.world.setErp(erp)
    self.world.setCfm(cfm)
    self.world.setAutoDisableFlag(True)

    # Create a surface table - contains interactions between different surface types - loaded from config file...
    #surElem = [x for x in xml.findall('surface')]
    self.world.initSurfaceTable(1)# number of surfaces #len(surElem))
    self.surFromName = dict()
    for a in []:#xrange(len(surElem)):
      self.surFromName[surElem[a].get('name')] = a

      # Maths used below is obviously wrong - should probably work out something better.

      # Interaction with same surface...
      mu = float(surElem[a].get('mu'))
      bounce = float(surElem[a].get('bounce'))
      absorb = float(surElem[a].get('absorb'))
      self.world.setSurfaceEntry(a,a,mu,bounce,absorb,erp,cfm,slip,dampen)

      # Interaction with other surfaces...
      for b in xrange(a+1,len(surElem)):
        mu = float(surElem[a].get('mu')) * float(surElem[b].get('mu'))
        bounce = float(surElem[a].get('bounce')) * float(surElem[b].get('bounce'))
        absorb = float(surElem[a].get('absorb')) + float(surElem[b].get('absorb'))
        self.world.setSurfaceEntry(a,b,mu,bounce,absorb,erp,cfm,slip,dampen)

    self.world.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0 , 0.002)
    # Create a space to manage collisions...
    self.space = OdeHashSpace()
    self.space.setAutoCollideWorld(self.world)

    # Setup a contact group to handle collision events...
    self.contactGroup = OdeJointGroup()
    self.space.setAutoCollideJointGroup(self.contactGroup)


    # Create the synch database - this is a database of NodePath and ODEBodys - each frame the NodePaths have their positions synched with the ODEBodys...
    self.synch = dict() # dict of tuples (node,body), indexed by an integer that is written to the NodePath as a integer using setPythonTag into 'ode_key'
    self.nextKey = 0
    self.nextDampKey = 0

    # Create the extra function databases - pre- and post- functions for before and after each collision step...
    self.preCollide = dict() # id(func) -> func
    self.postCollide = dict()

    # Create the damping database - damps objects so that they slow down over time, which is very good for stability...
    self.damping = dict() # id(body) -> (body,amount)

    # Variables for the physics simulation to run on automatic - start and stop are used to enable/disable it however...
    self.timeRem = 0.0
    self.step = 1.0/50.0
    
    # Arrange variables for collision callback, enable the callbacks...
    self.collCB = dict() # OdeGeom to func(entry,flag), where flag is False if its in 1, true if its in 2.
    self.space.setCollisionEvent("collision")


  def reload(self):
    pass # No-op: This makes this module incorrect, but only because you can't change the configuration during runtime without unloading it first. Physics setup tends to remain constant however.


  def simulationTask(self,task):
    # Step the simulation and set the new positions - fixed time step...
    self.timeRem += globalClock.getDt()
    while self.timeRem>self.step:
      # Call the pre-collision functions...
      for ident,func in self.preCollide.iteritems():
        func()

      # Apply damping to all objects in damping db...
      for key,data in self.damping.iteritems():
        if data[0].isEnabled():
          vel = data[0].getLinearVel()
          if vel.length()>1e3: # Cap dangerous motion.
            data[0].setLinearVel(vel*(1e3/vel.length()))
          else:
            vel *= -data[1]
            data[0].addForce(vel)

          rot = data[0].getAngularVel()
          if rot.length()>1e3: # Cap dangerous rotation.
            data[0].setAngularVel(rot*(1e3/rot.length()))
          else:
            rot *= -data[2]
            data[0].addTorque(rot)

      # A single step of collision detection...
      self.space.autoCollide() # Setup the contact joints
      self.world.quickStep(self.step)
      self.timeRem -= self.step
      self.contactGroup.empty() # Clear the contact joints

      # Call the post-collision functions...
      for ident,func in self.postCollide.iteritems():
        func()

    # Update all objects registered with this class to have their positions updated...
    for key, data in self.synch.items():
      node, body = data
      node.setPosQuat(render,body.getPosition(),Quat(body.getQuaternion()))

    return task.cont


  def onCollision(self,entry):
    geom1 = entry.getGeom1()
    geom2 = entry.getGeom2()

    for geom,func in self.collCB.iteritems():
      if geom==geom1:
        func(entry,False)
      if geom==geom2:
        func(entry,True)


  def start(self):
    self.task = taskMgr.add(self.simulationTask,'Physics Sim',sort=100)
    self.accept("collision",self.onCollision)

  def stop(self):
    taskMgr.remove(self.task)
    del self.task

    self.timeRem = 0.0
    self.ignoreAll()
    
  def getWorld(self):
    """Retuns the ODE world"""
    return self.world

  def getSpace(self):
    """Returns the ODE space used for automatic collisions."""
    return self.space

  def getSurface(self,name):
    """This returns the surface number given the surface name. If it doesn't exist it prints a warning and returns 0 instead of failing."""
    if self.surFromName.has_key(name):
      return self.surFromName[name]
    else:
      print 'Warning: Surface %s does not exist'%name
      return 0

  def getDt(self):
    return self.step

  def getRemTime(self):
    return self.timeRem


  def regBodySynch(self,node,body):
    """Given a NodePath and a Body this arranges that the NodePath tracks the Body."""
    body.setData(node)
    self.synch[node.getKey()] = (node,body)

  def unregBodySynch(self,node):
    """Removes a NodePath/Body pair from the synchronisation database, so the NodePath will stop automatically tracking the Body."""
    if self.synch.has_key(node.getKey()):
      self.synch[node.getKey()][1].setData(None)
      del self.synch[node.getKey()]

  def regPreFunc(self,name,func):
    """Registers a function under a unique name to be called before every step of the physics simulation - this is different from every frame, being entirly regular."""
    self.preCollide[name] = func

  def unregPreFunc(self,name):
    """Unregisters a function to be called every step, by name."""
    if self.preCollide.has_key(name):
      del self.preCollide[name]

  def regPostFunc(self,name,func):
    """Registers a function under a unique name to be called after every step of the physics simulation - this is different from every frame, being entirly regular."""
    self.postCollide[name] = func

  def unregPostFunc(self,name):
    """Unregisters a function to be called every step, by name."""
    if self.postCollide.has_key(name):
      del self.postCollide[name]

  def regCollisionCB(self,geom,func):
    """Registers a callback that will be called whenever the given geom collides. The function must take an OdeCollisionEntry followed by a flag, which will be False if geom1 is the given geom, True if its geom2."""
    self.collCB[geom] = func

  def unregCollisionCB(self,geom):
    """Unregisters the collision callback for a given geom."""
    if self.collCB.has_key(geom):
      del self.collCB[geom]

  def regDamping(self,body,linear,angular):
    """Given a body this applies a damping force, such that the velocity and rotation will be reduced in time. If the body is already registered this will update the current setting."""
    self.damping[body.getData().getKey()] = (body,linear,angular)

  def unregDampingl(self,body):
    """Unregisters a body from damping."""
    key = body.getId()
    if self.damping.has_key(key):
      del self.air_resist[key]


class PhysicsCharacterController:
  """A Player class - doesn't actually do that much, just arranges collision detection and provides a camera mount point, plus an interface for the controls to work with. All configured of course."""
  def __init__(self,manager):
    # Create the nodes...
    self.stomach = self.actor.attachNewNode('player-stomach')
    self.feet = self.stomach.attachNewNode('player-feet')
    self.neck = self.stomach.attachNewNode('player-neck')
    self.view = self.neck.attachNewNode('player-head')

    # Other variables...
    self.body = None
    self.colStanding = None
    self.colCrouching = None
    self.standCheck = None

    # Do the setup code...
    self.reload(manager)


  def destroy(self):
    self.stomach.removeNode()
    self.feet.removeNode()
    self.neck.removeNode()
    self.view.removeNode()
    
    if self.body!=None:
      self.body.destroy()
    if self.colStanding!=None:
      self.colStanding.destroy()
    if self.colCrouching!=None:
      self.colCrouching.destroy()
    if self.standCheck!=None:
      self.standCheck.destroy()


  def reload(self,manager):
    self.manager = manager

    # Get the players dimensions...

    self.height = 1.55
    self.crouchHeight = 0.7
    self.radius = 0.3
    self.headHeight = 1.4
    self.crouchHeadHeight = 0.6
    self.playerBaseImpulse = 15000.0# float(power.get('baseImpulse',15000.0))
    self.playerImpulse = 75000.0#float(power.get('feetImpulse',75000.0))
    self.crouchSpeed = 4.0#float(power.get('crouchSpeed',4.0))
    self.jumpForce = 16000.0#float(power.get('jumpForce',16000.0))
    self.jumpThreshold = 0.1#float(power.get('jumpLeeway',0.1))
    
    # Get the players mass and terminal velocity...

    self.mass = 70.0
    self.airResistance = 9.8/(30.0**2.0)


    # Setup the node positions...
    self.stomach.setPos(render,0.0,0.0,0.5*self.height)
    self.view.setPos(render,0.0,0.0,0.0 + self.headHeight)

    # Get the physics object...
    odeName = 'ode'
    self.ode = manager

    # Clean up any previous collision objects...
    if self.body!=None:
      self.body.destroy()
    if self.colStanding!=None:
      self.colStanding.destroy()
    if self.colCrouching!=None:
      self.colCrouching.destroy()
    if self.standCheck!=None:
      self.standCheck.destroy()

    # Setup the body...
    self.body = OdeBody(self.ode.getWorld())
    mass = OdeMass()
    mass.setCapsuleTotal(self.mass,3,self.radius,self.height - self.radius*2.0)
    self.body.setMass(mass)
    self.body.setPosition(self.stomach.getPos(render))
    self.body.setAutoDisableFlag(False)

    # Create a collision object - a capsule - we actually make two - one for standing, the other for crouching...
    self.colStanding = OdeCappedCylinderGeom(self.radius,self.height - self.radius*2.0)
    self.colStanding.setBody(self.body)
    self.colStanding.setCategoryBits(BitMask32(1))
    self.colStanding.setCollideBits(BitMask32(1))
    self.ode.getSpace().add(self.colStanding)
    self.ode.getSpace().setSurfaceType(self.colStanding,self.ode.getSurface('player'))

    self.colCrouching = OdeCappedCylinderGeom(self.radius,self.crouchHeight - self.radius*2.0)
    self.colCrouching.setBody(self.body)
    self.colCrouching.setCategoryBits(BitMask32(0))
    self.colCrouching.setCollideBits(BitMask32(0))
    self.ode.getSpace().add(self.colCrouching)
    self.ode.getSpace().setSurfaceType(self.colCrouching,self.ode.getSurface('player'))

    # Create a collision object ready for use when checking if the player can stand up or not - just a sphere with the relevant radius...
    self.standCheck = OdeSphereGeom(self.radius)
    self.standCheck.setCategoryBits(BitMask32(0xFFFFFFFE))
    self.standCheck.setCollideBits(BitMask32(0xFFFFFFFE))
    
    # We also need to store when a jump has been requested...
    self.doJump = False
    self.midJump = False
    self.surNormal = None # Surface normal the player is standing on.
    self.lastOnFloor = 0.0 # How long ago since the player was on the floor - we give a threshold before we stop allowing jumping. Needed as ODE tends to make you alternate between touching/not touching.

    # Need to know if we are crouching or not...
    self.crouching = False
    self.crouchingTarget = False

    # Used to slow the player down as they walk up a ramp...
    self.forceFalloff = 1.0


  # Player task - basically handles crouching as everything else is too physics engine dependent to be per frame...
  def playerTask(self,task):
    dt = globalClock.getDt()
    
    # Crouching - this switches between the two cylinders immediatly on a mode change...
    if self.crouching!=self.crouchingTarget:
      if self.crouchingTarget:
        # Going down - always possible...
        self.crouching = self.crouchingTarget

        self.colStanding.setCategoryBits(BitMask32(0))
        self.colStanding.setCollideBits(BitMask32(0))
        self.colCrouching.setCategoryBits(BitMask32(1))
        self.colCrouching.setCollideBits(BitMask32(1))

        offset = Vec3(0.0,0.0,0.5*(self.crouchHeight-self.height))
        self.body.setPosition(self.body.getPosition() + offset)
        self.stomach.setPos(self.stomach,offset)
        self.view.setPos(self.view,-offset)
      else:
        # Going up - need to check its safe to do so...
        pos = self.body.getPosition()

        canStand = True
        pos[2] += self.height - 0.5*self.crouchHeight
        space = self.ode.getSpace()

        sc = int(math.ceil((self.height-self.crouchHeight)/self.radius))
        for h in xrange(sc): # This is needed as a cylinder can miss collisions if tested this way.
          pos[2] -= self.radius
          self.standCheck.setPosition(pos)
          if ray_cast.collides(space,self.standCheck):
            canStand = False
            break

        if canStand:
          self.crouching = self.crouchingTarget

          self.colStanding.setCategoryBits(BitMask32(1))
          self.colStanding.setCollideBits(BitMask32(1))
          self.colCrouching.setCategoryBits(BitMask32(0))
          self.colCrouching.setCollideBits(BitMask32(0))

          offset = Vec3(0.0,0.0,0.5*(self.height-self.crouchHeight))
          self.body.setPosition(self.body.getPosition() + offset)
          self.stomach.setPos(self.stomach,offset)
          self.view.setPos(self.view,-offset)

    # Crouching - this makes the height head towards the correct height, to give the perception that crouching takes time...
    currentHeight = self.view.getZ() - self.neck.getZ()
    if self.crouching:
      targetHeight = self.crouchHeadHeight - 0.5*self.crouchHeight
      newHeight = max(targetHeight,currentHeight - self.crouchSpeed * dt)
    else:
      targetHeight = self.headHeight - 0.5*self.height
      newHeight = min(targetHeight,currentHeight + self.crouchSpeed * dt)
    self.view.setZ(newHeight)

    return task.cont


  def playerPrePhysics(self):
    # Get the stuff we need - current velocity, target velocity and length of time step...
    vel = self.body.getLinearVel()
    targVel = self.feet.getPos()
    dt = self.ode.getDt()

    # Check if the player is standing still or moving - if moving try and obtain the players target velocity, otherwsie try to stand still, incase the player is on a slope and otherwise liable to slide (Theres a threshold to keep behaviour nice - slope too steep and you will slide.)...
    if targVel.lengthSquared()<1e-2 and vel.lengthSquared()<1e-1:
      # Player standing still - head for last standing position...
      targVel = self.targPos - self.stomach.getPos()
      targVel /= 0.1 # Restoration time
      targVel[2] = 0.0 # Otherwise a vertical drop onto a slope can causes the player to do mini jumps to try and recover (!).
    else:
      # Player moving - use targVel and update last standing position...
      self.targPos = self.stomach.getPos()

      # Rotate the target velocity to account for the players facing direction...
      rot = Mat3()
      self.neck.getQuat().extractToMatrix(rot)
      targVel = rot.xformVecGeneral(targVel)


    # Find out if the player is touching the floor or not - we check if the bottom hemisphere has touched anything - this uses the lowest collision point from the last physics step...
    if (self.surNormal!=None) and (self.surNormal[2]>0.0):
      self.lastOnFloor = 0.0
    else:
      self.lastOnFloor += dt
    onFloor = self.lastOnFloor<self.jumpThreshold

    # Calculate the total force we would *like* to apply...
    force = targVel - vel
    force *= self.mass/dt
    
    # Cap the liked force by how strong the player actually is and fix the player to apply force in the direction of the floor...
    forceCap = self.playerBaseImpulse
    if onFloor: forceCap += self.playerImpulse
    forceCap *= dt

    if self.surNormal==None:
      force[2] = 0.0
    else:
      # This projects the force into the plane of the surface the player is standing on...
      fx  = force[0] * (1.0-self.surNormal[0]*self.surNormal[0])
      fx += force[1] * -self.surNormal[0]*self.surNormal[1]
      fx += force[2] * -self.surNormal[0]*self.surNormal[2]

      fy  = force[0] * -self.surNormal[1]*self.surNormal[0]
      fy += force[1] * (1.0-self.surNormal[1]*self.surNormal[1])
      fy += force[2] * -self.surNormal[1]*self.surNormal[2]

      fz  = force[0] * -self.surNormal[2]*self.surNormal[0]
      fz += force[1] * -self.surNormal[2]*self.surNormal[1]
      fz += force[2] * (1.0-self.surNormal[2]*self.surNormal[2])

      force[0] = fx
      force[1] = fy
      force[2] = fz

      # If the ramp is too steep, you get no force - and fall back down again...
      if force[2]>1e-3:
        forceCap *= max(self.surNormal[2] - 0.8,0.0)/(1.0-0.8)

    fLen = force.length()
    if fLen>forceCap:
      force *= forceCap/fLen

    # Add to the force so far any pending jump, if allowed...
    if self.doJump and onFloor and not self.midJump:
      force[2] += self.jumpForce
      self.midJump = True
    self.doJump = False

    # Apply air resistance to the player - only for falling - air resistance is direction dependent!
    if vel[2]<0.0:
      force[2] -= self.airResistance*vel[2]*vel[2]
      self.midJump = False

    # Apply the force...
    self.body.addForce(force)

    # Simple hack to limit how much air the player gets off the top of ramps - need a better solution. It still allows for some air, but other solutions involve the player punching through ramps...
    if (not onFloor) and (not self.midJump) and (vel[2]>0.0):
      vel[2] = 0.0
      self.body.setLinearVel(vel)
    
    # We have to reset the record of the lowest point the player is standing on ready for the collision callbacks to recalculate it ready for the next run of this handler...
    self.surNormal = None


  def playerPostPhysics(self):
    # Zero out all rotation...
    self.body.setQuaternion(Quat())
    self.body.setAngularVel(Vec3(0.0,0.0,0.0))
    
    # Update the panda node position to match the ode body position...
    pp = self.body.getPosition() + self.body.getLinearVel()*self.ode.getRemTime() # Interpolation from physics step for smoother movement - due to physics being on a constant frame rate.
    self.stomach.setPos(render,pp)


  def onPlayerCollide(self,entry,which):
    # Handles the players collisions - used to work out the orientation of the surface the player is standing on...
    for i in xrange(entry.getNumContacts()):
      n = entry.getContactGeom(i).getNormal()
      if which:
        n *= -1.0

      if self.surNormal==None or n[2]>self.surNormal[2]:
        self.surNormal = n


  def start(self):
    self.reset()
    
    # Arrange all the tasks/callbacks required...
    self.task = taskMgr.add(self.playerTask, 'PlayerTask')
    self.ode.regPreFunc('playerPrePhysics', self.playerPrePhysics)
    self.ode.regPostFunc('playerPostPhysics', self.playerPostPhysics)

    # To know if the player is on the floor or airborne we have to intecept collisions between the players capsules and everything else...
    self.ode.regCollisionCB(self.colStanding, self.onPlayerCollide)
    self.ode.regCollisionCB(self.colCrouching, self.onPlayerCollide)


  def stop(self):
    taskMgr.remove(self.task)
    self.ode.unregPreFunc('playerPrePhysics')
    self.ode.unregPostFunc('playerPostPhysics')

    self.ode.unregCollisionCB(self.colStanding)
    self.ode.unregCollisionCB(self.colCrouching)


  def reset(self):
    """Resets the player back to their starting position. (Leaves rotation alone - this is for debuging falling out the level kinda stuff.)"""
    start = self.manager.get('level').getByIsA('PlayerStart')
    if len(start)>0:
      start = random.choice(start) # If there are multiple player starts choose one at random!
      self.neck.setH(start.getH(render))
      self.stomach.setPos(start.getPos(render))
    else:
      self.neck.setH(0.0)
      self.stomach.setPos(Vec3(0.0,0.0,0.0))

    self.stomach.setPos(self.stomach,0.0,0.0,0.5*self.height)
    self.body.setPosition(self.stomach.getPos(render))
    self.body.setLinearVel(Vec3(0.0,0.0,0.0))

    self.targPos = self.stomach.getPos()


  def crouch(self):
    """Makes the player crouch, unless they are already doing so."""
    self.crouchingTarget = True

  def standup(self):
    """Makes the player stand up from crouching."""
    self.crouchingTarget = False

  def isCrouched(self):
    """Tells you if the player is crouching or not."""
    return self.crouching


  def jump(self):
    """Makes the player jump - only works when the player is touching the ground."""
    self.doJump = True


class PhysicsObject:
  """Provides a simple physics object capability - replaces all of a specific IsA in a scene with a specific mesh and specific physics capabilities. Initialises such objects with simulation off, so they won't move until they itnteract with the player or an AI somehow - needed to restrict computation but means such objects must be positioned very accuratly in the level.
  It can also contain a bunch of <instance> tags, that way you can specify positions yourself instead of doing it in the world model."""
  def __init__(self,manager):
    self.reload(manager)
    self.node = render.attachNewNode('PhysicsObjects')
    self.node.hide()

    self.things = [] # Tuple of (mesh,body,collider)

  def reload(self,manager):
    self.manager = manager

  def destroy(self):
    for mesh,body,collider in self.things:
      mesh.removeNode()
      body.destroy()
      collider.destroy()

    self.node.removeNode()


  def postInit(self):
    for i in self.postReload():
      yield i

  def postReload(self):
    # We need to delete any old objects from before this reload...
    for mesh,body,collider in self.things:
      mesh.removeNode()
      body.destroy()
      collider.destroy()
      yield
    self.things = []
    yield
    
    # Mesh path, physics plugin and physics type...
    basePath = "/" #self.manager.get('paths').getConfig().find('objects').get('path')
    
    self.ode = self.manager

    pType = phys.get('type').lower()

    # Find all instances of the object to obtain...
    toMake = []
    for isa in self.xml.findall('isa'):
      level = self.manager.get(isa.get('source'))
      toMake += level.getByIsA(isa.get('name'))
      yield

    for inst in self.xml.findall('instance'):
      # Find <instance> tags that can be used to create instances of the physics object.
      make = NodePath('physicsObject')
      make.setPos(  float(inst.get('x', '0')), float(inst.get('y', '0')), float(inst.get('z', '0')))
      make.setHpr(  float(inst.get('h', '0')), float(inst.get('p', '0')), float(inst.get('r', '0')))
      make.setScale(float(inst.get('sx','1')), float(inst.get('sy','1')), float(inst.get('sz','1')))
      toMake.append(make)
      yield

    # Make all of the relevant instances...
    for make in toMake:
      # Load the mesh, parent to render...
      filename = posixpath.join(basePath, self.xml.find('mesh').get('filename'))
      model = loader.loadModel(filename)
      model.reparentTo(self.node)
      model.setShaderAuto()
      model.setPosQuat(make.getPos(render),make.getQuat(render))
        
      if pType=='mesh':
        # Need some way of calculating/obtaining an inertial tensor - currently using a box centered on the object with the dimensions of the collision meshes bounding axis aligned box...
        colMesh = loader.loadModel(posixpath.join(basePath,phys.get('filename')))

      # Create the collision object...
      if pType=='sphere':
        col = OdeSphereGeom(self.ode.getSpace(), float(phys.get('radius')))
      elif pType=='box':
        col = OdeBoxGeom(self.ode.getSpace(), float(phys.get('lx')), float(phys.get('ly')), float(phys.get('lz')))
      elif pType=='cylinder':
        col = OdeCylinderGeom(self.ode.getSpace(), float(phys.get('radius')), float(phys.get('height')))
      elif pType=='capsule':
        col = OdeCappedCylinderGeom(self.ode.getSpace(), float(phys.get('radius')), float(phys.get('height')))
      elif pType=='mesh':
        col = OdeTriMeshGeom(self.ode.getSpace(), OdeTriMeshData(colMesh,True))

      col.setPosition(make.getPos(render))
      col.setQuaternion(make.getQuat(render))

      surface = phys.get('surface')
      self.ode.getSpace().setSurfaceType(col,self.ode.getSurface(surface))

      # Create the body and mass objects for the physics...
      body = OdeBody(self.ode.getWorld())
      if hasattr(body, 'setData'):
        body.setData(model)
      col.setBody(body)
      mass = OdeMass()
      if pType=='sphere':
        mass.setSphereTotal(float(phys.get('mass')), float(phys.get('radius')))
      elif pType=='box':
        mass.setBoxTotal(float(phys.get('mass')), float(phys.get('lx')), float(phys.get('ly')), float(phys.get('lz')))
      elif pType=='cylinder':
        mass.setCylinderTotal(float(phys.get('mass')), 3, float(phys.get('radius')), float(phys.get('height')))
      elif pType=='capsule':
        mass.setCapsuleTotal(float(phys.get('mass')), 3, float(phys.get('radius')), float(phys.get('height')))
      elif pType=='mesh':
        low, high = colMesh.getTightBounds()
        mass.setBoxTotal(float(phys.get('mass')), high[0]-low[0], high[1]-low[1], high[2]-low[2])
      else:
        raise Exception('Unrecognised physics type')

      body.setMass(mass)
      body.setPosition(make.getPos(render))
      body.setQuaternion(make.getQuat(render))
      body.disable() # To save computation until the player actually interacts with 'em. And stop that annoying jitter.

      damp = self.xml.find('damping')
      if damp!=None:
        self.ode.regDamping(body,float(damp.get('linear')),float(damp.get('angular')))

      # Tie everything together...
      self.ode.regBodySynch(model,body)
      self.things.append((model,body,col))

      yield

    
  def start(self):
    self.node.show()

  def stop(self):
    self.node.hide()

