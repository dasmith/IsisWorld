# Isis World Simulator

The IsisWorld simulator is available to researchers for building and evaluating problem solving and language learning systems with everyday problems that take place in a kitchen (on a campground?  house coming soon!).  Some documentation and arguments about theoretical underpinnings aimed toward the metareasoning community are available in this paper: 
 
  * [An open source commonsense simulator for AI researchers](http://web.media.mit.edu/~dustin/simulator_metacog_aaai_2010.pdf).  Dustin Smith and Bo Morgan.  *Submitted to AAAI-10 Workshop on Metacognition*.

# Improvements to the Simulator

Over the summer of 2010, we plan to make many significant improvements to IsisWorld.  These will manifest as completion of several projects:

## Implementation of Physics

Angular and linear forces will be applied, and densities of objects will be represented by a Physical simulator. Because [ODE integration](http://www.panda3d.org/wiki/index.php/Using_ODE_with_Panda3D) in Panda3D is still preliminary [#1](http://www.panda3d.org/phpbb2/viewtopic.php?t=8207),
[#2](http://www.panda3d.org/phpbb2/viewtopic.php?t=9200&sid=cd4e0c8166aadd14238c2e88f1a55282), and commitment to open source principles has eliminated NVidia's mature PhysX platform as a viable option, our
only option is to use Panda3D's built-in [physics support](http://www.panda3d.org/wiki/index.php/Panda3D_Physics_Engine) and [collision detection](http://www.panda3d.org/wiki/index.php/Collision_Detection).
Some decent tutorials exist [#1](http://www.panda3d.org/phpbb2/viewtopic.php?t=4806) [#2](http://www.panda3d.org/phpbb2/viewtopic.php?t=7918),  and also some for ODE, when Panda3D's support becomes more robust [#1](http://www.panda3d.org/phpbb2/viewtopic.php?t=7913).

### Design ideas

 - Make the physics handling modular, accessible through the `IsisWorld.worldManager` variable
 - Agents, Objects, and Environment items are initialized separately:
    - **Agents**: Are sub-classed instances, defined in `simulator/ralph.py` of `PhysicsCharacterController` class, which has an `updatePhysics` method.  Geometrically, these are represented as capped cylinders, as TriMeshes are too computationally expensive.
    - **Objects**: In ODE, there are two types of objects: kinematic (non-self propelled) and dynamic (capable of self-motion).  Most objects can be represented as a boundedBox, although some are best represented as cylinder or sphere.
        - Objects can be added through `worldManager.addObjectToPhysics`
    - **Environment**:  The ground is represented as an infinite plane.  Should represent walls of house as blocks, not TriMesh.
 - Gravity is represented as a linear force downward

## Initialization scripts for designing and loading environments

As mentioned in the [position paper](http://web.media.mit.edu/~dustin/simulator_metacog_aaai_2010.pdf), we want environments to be *generated* from a space of possible dimensions.  Most of the variable properties of the items (size, location, plurality, color, state) could be left to future work.  Default locations can be specified in a configuration file corresponding to prepositions:
   - X on|in Y:  "on" and "in" are less descriptive than 3D (relative) coordinates

This will require a general module for describing and loading components, a large range of visual, physical, linguistic, spatial (default locations), and functions (properties, methods to modify properties) for each object.

  * **Physical**: shape (for Physical collision mask), dynamic or kinesthetic
  * **Visual**: visibility, color mask, transparency level, scale size (of model)
  * **Spatial**: default orientation of model, default locations (as represented in abstract descriptions: "in kitchen on table")
  * **Functional**: use a commonsense **type system** and inheritance structure for **attributes** and **values**  and their defaults (e.g., `{'is_on': {'domain': [True,False], 'default': False}}`) and **event listeners** to change the properties of these actions, some of which can affect the other kinds of item properties (physical), etc.

### Design ideas

  - Read `kitchen.isis` world in, creating a labeled graph structure: "X on Y" becomes: *graph.addEdge(x,y,label='on')*
  - With root node "kitchen", [Topological sort](http://en.wikipedia.org/wiki/Topological_sorting) all nodes, and being rendering nodes in sorted order
  - Visually, add models to their parent renderer `attachNodeWrtParent()`
  - Set default properties of the item
  - Physically, register item within physics handler

## Extending corpus of models

Lots that can possibly be added.  Stay focused on the kitchen and the use cases (make toast)

 - Can add models from Google's [3D warehouse](http://sketchup.google.com/3dwarehouse/), export them to **egg** files. Instructions: [#1](http://www.panda3d.org/phpbb2/viewtopic.php?t=9013)
 - Blender models can be exported using Chicken.
 - [Alice](http://www.alice.org/index.php?page=gallery/index) I saw a list of these somewhere that were already in the egg file format. Some of these already have animation methods!
 - List of [game models](http://www.panda3d.org/phpbb2/viewtopic.php?t=6880)
 - [not-immediately useful list of resources](http://code.google.com/p/panda3d-models/wiki/Resources)

## Event Handling in simulated world

In addition to items being able to re-act to actions of the character, events can be initiated by states of the world.  For example, when a toaster "is_on" and "contains_item", then after 5 minutes, it changes the state of the item inside to "burned", darkens the color, and turns itself off.

### Design Ideas

Use the [FSM](http://www.panda3d.org/wiki/index.php/Finite_State_Machines) of Panda3D to do this.  Possible approach: using Honda's OMICS corpus

## Low Priority Improvements

  - Replace Ralph with nicer model(s)
  - Obtain copyright information for all models
  - Multi-client implementation
  - Improving granularity of actions:  kinesthetic grasp, move items between arms, damage to body depending on forces
  - Adding animation methods to graphics
  - Configuration parameters to disable non-essential, CPU intensive visual effects, like the clouds in the sky.

## Resources for Developers

Here is a list of resources for developers that are getting started working with IsisWorld.

  [Panda3d.org](http://panda3d.org) has a really good manual, though it doesn't have 100% coverage of all the features in the API.  Also [the Panda3D forum](http://Panda3d.org/phpbb2/) is very valuable resource.

To learn about Git, I recommend [GitHub's videos](http://learn.github.com).
