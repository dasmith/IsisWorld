"""
This file determines the type of physics to be used, allowing
it to be changed simply in this file, verus all of the locations
it is called from.

Each *WorldManager must have the following methods defined:

 - PhysicsCharacterController:  this is a class sub-classed by the ralph
 actor,
   * updateCharacter() which controls the position of the character
     (both geometry and the Actor avatar)

 - PhysicsWorldManager:
   * __init__()
   * setupGround(groundNodePath) -- initializes the floor
   * addObjectToWorld(nodePath) -- allows objects to be added to the world


"""

from pandaWorldManager import *
# from odeWorldManager import *
