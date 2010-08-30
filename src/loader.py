"""  Parses and instantiates objects/agents by executing the environment() method of IsisScenarios """

import sys
from random import *
from direct.interval.IntervalGlobal import *
from pandac.PandaModules import Vec3

def load_objects_future(scenario, renderParent, physics):
    # load functions and modules into the namespace
    # these functions are globals used by the scenario object
    # to easily and pythonically set up the environment

    # Parents the object to the world node, must be done to the object or a parent
    # of the object for the object to be visible
    generators = __import__("src.isis_objects.generators")
    generators = generators.isis_objects.generators
    # FIXME: hacky definition to filter the generators from the other Panda3d functions in the namespace
    filterfun = lambda x: x[0] in ['fridge','toaster','bread','loaf','kitchen','knife','table','Ralph']
    generators = dict(filter(filterfun, generators.__dict__.items()))
    for klass, constructor in generators.items():
        constructor.setPhysics(physics)
    
    # define functions used in the execution namspace
    def put_in_world(obj):
        obj.reparentTo(renderParent)

    # Places the object in to the given container
    def put_in(obj, container):
        if container.call(None, "put_in", obj) != "success":
            obj.reparentTo(renderParent)
            x, y, z = container.activeModel.getPos(renderParent)
            obj.setPos(x, y, z+3)

    # Places the object on to the given surface
    def put_on(obj, surface):
        if surface.call(None, "put_on", obj) != "success":
            obj.reparentTo(renderParent)
            x, y, z = surface.activeModel.getPos(renderParent)
            obj.setPos(x, y, z+3)

    def store(vars):
        """ Stores the local variables defined in the environment
        so that they can later be used by later references in the task, 
        such as the functions that check to see if a goal is met."""
        scenario.envDict = vars
        # TODO: have store called automatically after Scenario.environment(), perhaps by re 'compiling' 
        # the environment byte-code to include the "store(locals())" expression as the last line.

    locals().update(generators)
    locals().update({'put_in_world':put_in_world,'put_in':put_in,'put_on':put_on, 'store':store})
    print 'LOCALS', locals()
    exec scenario.environment.__code__ in locals()
    print 'POST LOCALS', locals()
