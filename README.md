
<pre>
                 ___                       ___           ___           ___           ___           ___       ___     
     ___        /\  \          ___        /\  \         /\__\         /\  \         /\  \         /\__\     /\  \    
    /\  \      /::\  \        /\  \      /::\  \       /:/ _/_       /::\  \       /::\  \       /:/  /    /::\  \   
    \:\  \    /:/\ \  \       \:\  \    /:/\ \  \     /:/ /\__\     /:/\:\  \     /:/\:\  \     /:/  /    /:/\:\  \  
    /::\__\  _\:\~\ \  \      /::\__\  _\:\~\ \  \   /:/ /:/ _/_   /:/  \:\  \   /::\~\:\  \   /:/  /    /:/  \:\__\ 
 __/:/\/__/ /\ \:\ \ \__\  __/:/\/__/ /\ \:\ \ \__\ /:/_/:/ /\__\ /:/__/ \:\__\ /:/\:\ \:\__\ /:/__/    /:/__/ \:|__|
/\/:/  /    \:\ \:\ \/__/ /\/:/  /    \:\ \:\ \/__/ \:\/:/ /:/  / \:\  \ /:/  / \/_|::\/:/  / \:\  \    \:\  \ /:/  /
\::/__/      \:\ \:\__\   \::/__/      \:\ \:\__\    \::/_/:/  /   \:\  /:/  /     |:|::/  /   \:\  \    \:\  /:/  / 
 \:\__\       \:\/:/  /    \:\__\       \:\/:/  /     \:\/:/  /     \:\/:/  /      |:|\/__/     \:\  \    \:\/:/  /  
  \/__/        \::/  /      \/__/        \::/  /       \::/  /       \::/  /       |:|  |        \:\__\    \::/__/   
                \/__/                     \/__/         \/__/         \/__/         \|__|         \/__/     ~~
                
</pre>

**IsisWorld** is a free and open-source microworld generator for grounding and testing multi-agent commonsense reasoning systems.  It is cross-platform, uses ODE rigid-body physics, is easily extensible (in Python using the [Panda3D](http://panda3d.org) game library) and can be controlled using any XML-RPC client.

   - **To use the simulator without modifying the source, [download the latest binaries](http://web.media.mit.edu/~dustin/isisworld).** (Note: even with the binaries, you can still change and create your own scenario files.)
   - **If you plan to make extensive changes to IsisWorld, [follow these instructions](http://web.media.mit.edu/~dustin/simulator_setup/#developing-the-simulator) about installing Panda3D, avoiding common problems and getting started.**

IsisWorld was developed for **evaluating integrative AI systems**.  A user can define a microworld by editing a *scenario file* and IsisWorld will *generate* a world---choosing particular sizes, scales and positions for the objects in the environment.  This is done in order to obstruct AI systems from overfitting the environment.

IsisWorld was intended to model everyday, *human-level* problems, amenable to reasoning about joint behavior, intention and communication.  The simulator granularity is too coarse for serving as a robotic simulator.  For more information about the simulator, including the indented audience and the motivation behind this approach to building intelligent agents, please refer to these resources: 

 * [An open source commonsense simulator for AI researchers](http://web.media.mit.edu/~dustin/simulator_metacog_aaai_2010.pdf).  Dustin Smith and Bo Morgan.  *Proceedings of AAAI-10. Workshop on Metacognition*. 
 * [IsisWorld Presentation](http://web.media.mit.edu/~dustin/isisworld.pdf) *Presented at the AAAI-10 Workshop on Metacognition*. 

# How do I use the simulator?

## Starting the simulator

If you have downloaded the binary, simply open the `isisworld` executable.  *The first time you load the binary, you will incur a long wait while Panda3D fetches the latest game libraries.  This will only happen once.*  IsisWorld will prompt you to "load a scenario".  If you look in the `scenarios` folder, you will find some default scenarios.  They are Python files containing a subclass of `IsisScenario` and describe how to generate the world and test for particular world states.

If you are running the simulator from source, you first need to have installed the [Panda3D v1.7+](http://panda3d.com) SDK and configured it so that its library files are locatable from your Python's loading path.  Then you can run the simulator:

    python main.py

There are several command-line options:

    -h              : displays a list of command line options
    -D              : loads first Scenario by default
    -p <PORTNUMBER> : launches the XML-RPC server on the specified port. Default 8001
    --small_window  : mimizes the window to 640x480
    --lazy_render   : render only at 4 frames per second to use minimal CPU, useful when physics is usually paused.

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
        while e.do('meta_physics_active'):
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
    'meta_physics_active'

Additionally, agents can execute actions.  For an up-to-date list of actions available to the agent, use the `meta_list_actions` command to return a list.


## How to add a new scenario

IsisWorld uses scenario files to define the state of the world and, optionally, a task specification to evaluate the agent's performance.  A scenario file contains  a description of what the generated world will look like along with *tasks* that check to see if a goal state of the world has been reached.   Isis Scenarios are Python files found in the `scenarios/` directory that implement a `Scenario` class.  Here is what the file `scenarios/make_toast` looks like:


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


# Details about specific components of the simulator


## Physics

The location of an object over time is defined by is *position* in three dimensional space, `(x,y,z)`, and its *orientation*--its rotation around the three axes, `(h,p,r)`.  Unfortunately, 3D models often exist is arbitrary coordinate systems, with varying scales. So before adding a model to IsisWorld, one should run the positioning tool to normalize the model's scale, position and orientation.

Angular and linear forces can be modeled along with densities of objects by the Open Dynamics Engine. 
IsisWorld uses Piotr Podgórski's [ODE Middleware for Panda3D](http://www.panda3d.org/forums/viewtopic.php?t=7913), which permits modeling static, kinematic, dynamic and ray objects.

Note, Panda3D's  [ODE integration](http://www.panda3d.org/wiki/index.php/Using_ODE_with_Panda3D) has a memory leak as of 1.7.0 that has been fixed in the latest builds.

## State controller

The state of the simulator represented by a [Finite-State Machine](http://www.panda3d.org/wiki/index.php/Finite_State_Machines) that can be controlled either through the GUI or by issuing `meta_` commands through the XML-RPC client.

The typical sequence of meta commands:

   1. `meta_load_scenario(scenario='newscenario.py')` loads a file called `newscenario.py` in the `scenarios/` folder.
   2. `meta_list_tasks` returns a list of tasks defined in the `IsisScenario` class of `newscenario.py` (any method whose name begins with `task_`)
   3. `meta_load_task(task='name_of_task')` runs the `environment` method of the scenario, and instantiates the 3D world.
   
Then, you can `meta_pause` or `meta_step` to start the physical (ODE) simulation and issue action commands to the agent.

To facilitate evaluation, tasks can define `train_` and `goal_` functions.  The training method is called when the simulator enters a the **training state**.  You can enter the training state by issuing the `meta_test` command through XML-RPC or clicking the `Test` on the simulator GUI.  

The **testing state** is entered by issuing `meta_test` or clicking the "Test" button on the GUI.  While in this state, the simulator constantly checks to see if any `IsisScenario.goal_*` methods are returning True, and if so, stops a timer and displays an alert window.

So, to use the training and testing features, your task sequence would include:

   4.  `meta_train`
   5.  `meta_test`

# How do I add new models to IsisWorld?

One of the main goals of IsisWorld is to allow end users to easily add new models to the simulator. Thee most tedious and time consuming part of building a scenario is making the objects' positions look realistic.  When loading a new model, the middle point (0,0,0) is arbitrarily defined and sometimes does not even intersect the 3D visual model!  We need a standard: each model should be realistically scaled (with respect to the 2 meter tall Robot), have its bottom center at 0,0,0, being standing upright, with its "Front" facing (1,1,1).    I have been accommodating these differences using two vectors that are added to the default positions of the objects

  - **offset_vector** = (x,y,z,h,p,r):  whenever an object is put in, or on, another object.
  - **pickup_vector** = (x,y,z,h,p,r): whenever the object is picked up, i.e., attached to one of the agent's hands.

Another problems is with the arbitrary scale of a model.  Often a model is way too large and needs to scaled to a tenth or hundred of the original size.  This is bad, because some of Panda's visual optimization techniques don't work with very scaled-down models.

What IsisWorld needs is a script that allows the user to view the model to tweak it.  I'm thinking something like [pview](http://www.panda3d.org/manual/index.php/Previewing_3D_Models_in_Pview), with an IsisAgent inside for scale and seeing what it looks like when an agent is holding an object, that we could use to compute the scaling parameter and the offset vectors using Panda3D's built-in `model.place()` GUI. Currently, the tedious process involves: loading the scene, having an agent pick it up, figuring out which dimension to rotate/scale it, and then editing the file.

The script could be as a wrapper to [egg-trans](http://www.panda3d.org/manual/index.php/List_of_Panda3D_Executables), then we could do away with the offset/pickup vectors altogether.

For example, this is how you scale the model by a, rotate it by h,p,r and translate it by x,y,z.

    egg-trans -o output.egg -TS a -TS h,p,r -TT x,y,z input.egg

Here are some relevant external resources pertaining to obtaining, editing and importing 3D models to `egg` format:

  -Google's [3D warehouse](http://sketchup.google.com/3dwarehouse/) is a huge resource that can be exported to **egg** files. Instructions: [#1](http://www.panda3d.org/phpbb2/viewtopic.php?t=9013).  (Works better with Sketchup Pro and using one of the alternative proprietary export options)
  - Blender models can be exported using Chicken.
  - [Alice](http://www.alice.org/index.php?page=gallery/index) I saw a list of these somewhere that were already in the egg file format. Some of these already have animation methods!
  - List of [game models](http://www.panda3d.org/phpbb2/viewtopic.php?t=6880)
  - [(not? immediately useful?) list of resources](http://code.google.com/p/panda3d-models/wiki/Resources)

%## Resources for Developers

%Here is a list of resources for developers that are getting started working with IsisWorld.

%[Panda3d.org](http://panda3d.org) has a really good manual, though it doesn't have 100% coverage of all the features in the API.  Also [the Panda3D forum](http://Panda3d.org/phpbb2/) is very valuable resource.

%To learn about Git, Dustin recommends [GitHub's videos](http://learn.github.com).



