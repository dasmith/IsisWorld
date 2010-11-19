
# To Do List
 
  - build tool for normalizing the position and rotations for objects.
  - UI triggered exit should first kill xmlrpc (and join thread?) before shutting down
  - Loading and running [IsisScenarios](#IsisScenarios) files:
    - buttons for starting a task, running a training and test scenario
    - recording statistics about the task: how many steps since it started, state of task (failed/completed/ongoing)
    - displaying state of task in the menu
  - documenting a skeleton generator file with all possible superclass attributes, so that other people can work on the project by adding / describing models.
  - fix problem of dynamically loading scenario files in panda3d packages.
  - separating actions from the `main.py` as a different data structure in a different file.
  - IsisEvent class
  - Storing and resuming game states
  - UI overhaul: clean up, make UI much more thin.
  - re-write layout managers
  
## Model adding tool

One of the main goals of IsisWorld is to allow end users to easily add new models to the simulator. Thee most tedious and time consuming part of building a scenario is making the objects' positions look realistic.  When loading a new model, the middle point (0,0,0) is arbitrarily defined and sometimes does not even intersect the 3D visual model!  We need a standard: each model should be realistically scaled (with respect to the 2 meter tall Robot), have its bottom center at 0,0,0, being standing upright, with its "Front" facing (1,1,1).    I have been accommodating these differences using two vectors that are added to the default positions of the objects

  - **offset_vector** = (x,y,z,h,p,r):  whenever an object is put in, or on, another object.
  - **pickup_vector** = (x,y,z,h,p,r): whenever the object is picked up, i.e., attached to one of the agent's hands.

Another problems is with the arbitrary scale of a model.  Often a model is way too large and needs to scaled to a tenth or hundred of the original size.  This is bad, because some of Panda's visual optimization techniques don't work with very scaled-down models.

What IsisWorld needs is a script that allows the user to view the model to tweak it.  I'm thinking something like [pview](http://www.panda3d.org/manual/index.php/Previewing_3D_Models_in_Pview), with an IsisAgent inside for scale and seeing what it looks like when an agent is holding an object, that we could use to compute the scaling parameter and the offset vectors using Panda3D's built-in `model.place()` GUI. Currently, the tedious process involves: loading the scene, having an agent pick it up, figuring out which dimension to rotate/scale it, and then editing the file.

The script could be as a wrapper to [egg-optchar](http://www.panda3d.org/manual/index.php/List_of_Panda3D_Executables), then we could do away with the offset/pickup vectors altogether.

For example, this is how you scale the model by a, rotate it by h,p,r and translate it by x,y,z.

    egg-optchar -o output.egg -TS a -TS h,p,r -TT x,y,z input.egg

Resources for adding new models:

  -Google's [3D warehouse](http://sketchup.google.com/3dwarehouse/) is a huge resource that can be exported to **egg** files. Instructions: [#1](http://www.panda3d.org/phpbb2/viewtopic.php?t=9013).  (Works better with Sketchup Pro and using one of the alternative proprietary export options)
  - Blender models can be exported using Chicken.
  - [Alice](http://www.alice.org/index.php?page=gallery/index) I saw a list of these somewhere that were already in the egg file format. Some of these already have animation methods!
  - List of [game models](http://www.panda3d.org/phpbb2/viewtopic.php?t=6880)
  - [(not? immediately useful?) list of resources](http://code.google.com/p/panda3d-models/wiki/Resources)

## Has Been Done List

GitHub does not appear to interpret Markdown's ~~strikethrough~~ operator, so here's the list of changes that have been made since the last version:

  - specifying scale ranges for some of the common models sizes, the same way the size of the kitchen is chosen from a random range.
  - in isis_agent:pick_object_up_with, special handling for objects on surfaces and objects in containers: Items being removed from containers first have their parent checked to see if `is_open` is True. If it is not, then the pickup action fails.  Objects like the toaster, have `is_open` as a hidden property, that is turned to `False` iff the toaster `is_on`.
  - creation of `IsisAttribute` with consistency checks.
  - scenario files allow defaults to be specified as keyword arguments. `k = kitchen(width=10, height=7)`
  - objects can have "front" orientation that is used to place objects around a room, with their backs to the wall
  - checking for whether the goal state is met
  - migrating the `kitchen.isis` into an "scene initialization" section of the "scenario/" files.
  - a DirectGUI for loading tasks, which is the default screen when the simulator loads.
  - recording state of task/scenario in logging file
  - exporting screen shots
  - RoomLayout layout manager that puts objects around the walls


# How to use the simulator.

*Note: This section of the README is incomplete and will be constantly changing.*

## Starting the simulator

To run the source code (non-packaged), you first need to have installed the [Panda3D](http://panda3d.com) SDK such that its library files are locatable from your Python's loading path.  Then you can run the simulator:

    python main.py

There are several command-line options:

    -D:  loads the first task of the first scenario by default
    -f:  initializes off-screen frame buffers, enabling the `sense_retina_image' commands through XML-RPC.
    -p [NUMBER]: changes the port from 8001 to another number for the XML-RPC server.
    -h:  a list of the current command line options.

After you have started the agent, you need to 1) load a scenario, and 2) load a task, and 3) unpause the simulator.

## Writing a client / agent

You can control the agent running the key-bindings (press `4` to have a list of all keybindings appear on the screen) or by writing a client that connects to the simulator using [XML-RPC](http://en.wikipedia.org/wiki/XML-RPC).  Examples of Python XML-RCP IsisWorld clients can be found in the `agents` folder, although XML-RPC libraries are available for many other languages.


### Example client in Python

Here are a few helper functions to connect to the simulator:

    import xmlrpclib as xml
    import time

    def connect_to_isis_world(server, port=8001):
        # connect to environment via XML-RPC
        e = xml.ServerProxy('http://%s:%i' % (server, port))
        print "Connecting to server"
        return e


    def sense():
        return e.do('sense', {'agent':'Ralph'})

    def step(t):
        e.do('meta_pause')
        e.do('meta_step', {'seconds':t})
        while e.do('meta_running'):
            time.sleep(0.001)

    def do(command, args = None):
        if not args:
            args = {}
        args['agent'] = 'Ralph'
        return e.do(command, args)

    # connect to isisworld
    e = connect_to_isis_world(server="localhost", port=8001)

    # list scenarios
    scenarios = e.do('meta_list_scenarios')
    print "Listing scenarios: %s" % (scenarios)

    # load the toast scenario
    print e.do('meta_load_scenario', {'scenario': 'make_toast.py'})

    tasks = e.do('meta_list_tasks')
    print "Listing tasks: %s" % (tasks)

    # load the toast scenario
    print e.do('meta_load_task', {'task': tasks[0]})

    # enter training mode
    print e.do('meta_train')
    
    # pick up butter
    print do('pick_up_with_left_hand', {'target':'butter'})
    step(.2)

    # pick up loaf
    do('pick_up_with_right_hand', {'target':'loaf'})
    step(0.8)



### Running commands through an XML-RPC client:

The following **meta commands** are defined that allow you to query and change the state of the simulator: 

    'meta_step',
    'meta_pause',
    'meta_resume',
    'meta_reset',
    'meta_list_actions',
    'meta_list_scenarios',
    'meta_load_scenario',
    'meta_list_tasks',
    'meta_load_task',
    'meta_train',
    'meta_test',
    'meta_setup_thought_layers',
    'meta_physics_is_active'

Additionally, agents can execute actions.  For an up-to-date list of actions available to the agent, use the `meta_list_actions` command to return a list.


## How to add a new scenario

IsisWorld uses scenario files to define the state of the world and, optionally, a task specification to evaluate the agent's performance.  A scenario file contains  a description of what the generated world will look like along with *tasks* that check to see if a goal state of the world has been reached.   Isis Scenarios are Python files found in the `scenarios/` directory that implement a `Scenario` class.  For example, the file "scenarios/make_toast"


    from src.isis_scenario import IsisScenario

    class Scenario(IsisScenario):
    
        description = "making toast in isisworld"
        author = "dustin smith"
        version = 1

        def environment():
            k = kitchen(length=15, width=15)
            put_in_world(k)
        
            f = fridge()
            put_in(f, k)

            b = butter()
            put_in(b, f)

            ta = table(scale=7)
            put_in(ta, k)
            
            lauren = IsisAgent("Lauren")
            put_in_world(lauren)
            put_in_front_of(lauren,f)
            
            # required at the end of the environment setup
            store(locals())


        def task_toaster_in_view():
  
            def train():
                k.put_in(r) # put ralph in the kitchen

            def goal_toaster_in_view():
                return ralph.in_view(t)

            store(locals())


## Environment function

This function `Scenario.environment()` specifies how to generate an IsisWorld.  The classes that are initialized correspond to objects in the `isis_objects/generators.py` file.  Properties like scale, length, and width are commonly drawn at random from values defined uniformly over an interval; however, these can be fixed by specifying a particular value as a keyword argument, as has been done for the `kitchen` object.


## Tasks

Each isisScenario has one or more **tasks**, defined using the python `def task__name_of_task`.  Each task can contain a  **training** phase and one or more **test** functions.  Allows you to specify different versions of Actions to use during training/test.


### Training

For example, putting ralph in front of various objects.


### Test

Any function that returns *true* or *false*.  Has access to the entirety of IsisWorld.



# About the IsisWorld Simulator

The IsisWorld simulator is available to researchers for building and evaluating problem solving and language learning systems with everyday problems that take place in a kitchen.  We aim to use IsisWorld to simulate everyday commonsense reasoning problems that span many realms, such as the social, visual, kinesthetic, physical, spatial and mental. 

What is a problem "realm"?  Consider the problem of *hailing a taxi*.  You could represent and reason about this problem in several different ways.

 1. **Temporally**: Wait for a taxi. Maybe if you stay put, a taxi will drive by
 2. **Spatially**:  Find a taxi. You must eliminate the distance between yourself and a taxi.
 2. **Socially**: Call a taxi.  Communicate your position to a dispatching agent and an available taxi will come to you. 

It is this resourcefulness---having many ways to solve a problem---that allows human problem solvers to flexibly adapt to many problem solving situations.  A system that lacks these abilities is *brittle*.

Further, we are looking for test bed to study the problems of meta-reasoning: where a super-level planning system reasons about the world of a sub-planning system.  Returning to a taxi example, we could consider the failure mode which causes a meta-level reasoner to step in and change the state of the planner.  For example, it could ask the system to *elevate* the problem description to pursue the parent goal:  *instead of "searching for a taxi" reconsider the problem as "traveling to your destination" and pursue other options: e.g., walking, train, asking a friend etc*.

 More detailed arguments about using a simulator for studying AI and the choice to use kitchen problem domain is explain in this paper:

  * [An open source commonsense simulator for AI researchers](http://web.media.mit.edu/~dustin/simulator_metacog_aaai_2010.pdf).  Dustin Smith and Bo Morgan.  *Proceedings of AAAI-10. Workshop on Metacognition*. 
  * [IsisWorld Presentation](http://web.media.mit.edu/~dustin/isisworld.pdf) *Presented at the AAAI-10 Workshop on Metacognition*. 


## Use cases / Problem Scenarios

The development of the simulator is focused on the following  test scenarios

### 1. Toast Making: studying first-level planning

Ralph is in the kitchen and has the goals of making and eating toast.  Ralph has to "use" the knife to cut the bread, and then put the bread in the toaster. Problems addressed [[#1](http://web.media.mit.edu/~push/Push.Phd.Proposal.pdf)]:
  
  * Bodily, what actions does Ralph have available?
  * Functional, how objects states can change: the effects of actions upon them and how they affect each other.
  * Spatially, navigating through space without bumping into objects
  * Motor routines:  what macro actions can be represented to coordinate common sequences of primitive actions?
  * Self models: how does the situation of Ralph's model (e.g., location of limbs in space, objects in hand, eyes opened or closed) influence the functions of actions he can perform.
  * Visual:  what objects are in the environment, how far are they, what shape and texture do they have?
  * Mental debugging: if all toast-making problem solvers reach impasses, Ralph could reflect on his problem and pop up to his higher goal.

### 2. Knife sharing: studying social interactions

Ralph and his mother Sue are in the kitchen.  Sue is currently using the only knife.  Ralph has to ask Sue to use the knife.  If he grabs the knife from her hand, he will be cut.

  * Mental: what is Sue's active goal ("intention"), does she have the same intention? how will she react to my actions? 
  * Social representations, from [[#1](http://web.media.mit.edu/~push/Push.Phd.Proposal.pdf)]
     - Social networks: who knows who?  who has interacted with whom?
     - Dominance: who sets the goals of this group?  who to listen to?
     - Goal interactions: do my actions help or hinder others?  Who might interfere with my goals?
     - Impriming: can they do something I can't?  what can I learn from them?
     - Groups: what are the roles in this group?  What are the functions of these roles?


### 3. Learning by observation

Sue is communicating a new sequence of actions.  Ralph must identify Sue's plan and then recognize her goal as different, and then learn the new plan as some deviation of the existing plan (e.g., making toast with jelly)
  
  * Plan and goal recognition
  * Planning and debugging in simulated mental worlds

### 4. Imprimer learning

Sue is teaching Ralph how *not* to use a kitchen.  He must learn that the faucet must be turned off after being used, doors closed after they are opened, not to leave the refrigerator open for more time than necessary, etc.  He must learn these how to represent and pursue these imagined goals and antigoals of his imprimer.   This must cover the problem of **shared attention**, where the teacher deliberately acts a certain way to encourage the learner to focus on a relevant aspect of the shared situation.

  * Shared attention and shared models of inference:  "What will Sue think if she sees the mess on the floor?"

### 5. Language learning and instruction execution

Learning the labels of objects from examples. Learning to label events/actions with verb phrases at different temporal resolutions.  Learning how to use and resolve pronouns, the linguistic equivalent of pointing.   Learning the proper sequence to carry out a sequence of actions from a linguistic description

  - learning and representing labels for things (nouns) in the world ("toast")
  - learning and representing adjectives ("black", "hot", "large") -- re-representing items in a perceptual measure space (concept domain) and using adjectives evoke discriminative boundaries with respect to a shared world model.
  - learning and representing composition of linguistic concepts (e.g., "red" in "red wine" is different than "red hair") or the linking constraints between verbs and nouns ("run" + "dishwasher" versus "run" + "marathon")
  - semantic parsing of a sentence into possible "interpretations"
  - interpreting verbs as states or actions (e.g., modeling the taxonomic organization of verbs and how they map to between sets of events, related by generality relationships)
  - interpreting nouns as constituents of states or actions (e.g., modeling the taxonomic organization of nouns and how they map to generality relationships between sets of items)
  - interpreting prepositions by representing items in a visual geometry / using spatial relationships
  - metaphoric mappings between concepts and spatial relationships w.r.t. some decision making process.
  - articulating an event that Ralph has completed with respect to a set of planning decisions, modulated by Ralph's model of the listener's knowledge
  - using hierarchical structure of linguistic phrases and aspectual connectives to model relationships between events and control structure of planning (do X "during", "after", "while" doing Y)
  - language parsing using a cognitively plausible model (e.g., Shift-Reduce parsing) 


### 6.  Communicating instructions

Ralph describes his actions or Sue's actions as an English verb phrase.

# Details about specific components of the simulator


## Physics

The location of an object over time is defined by is *position* in three dimensional space, `(x,y,z)`, and its *orientation*--its rotation around the three axes, `(h,p,r)`.  Unfortunately, 3D models often exist is arbitrary coordinate systems, with varying scales. So before adding a model to IsisWorld, one should run the positioning tool to normalize the model's scale, position and orientation.

Angular and linear forces can be modeled along with densities of objects by the Open Dynamics Engine. 
IsisWorld uses Piotr Podgórski's [ODE Middleware for Panda3D](http://www.panda3d.org/forums/viewtopic.php?t=7913), which permits modeling static, kinematic, dynamic and ray objects.

Note, Panda3D's  [ODE integration](http://www.panda3d.org/wiki/index.php/Using_ODE_with_Panda3D) has a memory leak as of 1.7.0 that has been fixed in the latest builds.

## State controller

The state of the simulator represented by a [Finite-State Machine](http://www.panda3d.org/wiki/index.php/Finite_State_Machines) that can be controlled either through the GUI or by issuing `meta_` commands through the XML-RPC client.




## Resources for Developers

Here is a list of resources for developers that are getting started working with IsisWorld.

  [Panda3d.org](http://panda3d.org) has a really good manual, though it doesn't have 100% coverage of all the features in the API.  Also [the Panda3D forum](http://Panda3d.org/phpbb2/) is very valuable resource.

To learn about Git, Dustin recommends [GitHub's videos](http://learn.github.com).



