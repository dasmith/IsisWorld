import xmlrpclib, sys, time
import random
from collections import defaultdict
from utils import dprint
import concept_learning
##### "CONNECT" FUNCTION #####

# In this implementation, most individual resources and functions only know about others
# if they're passed a reference to them in a "connections" dictionary. There is no need
# to define resources/functions internally to the agent so that they can have a "self"
# handle, neither does every function need to access all of "resource.mind" anymore.

# However, it would be silly to pass connection items around all the time. Most of the
# time these connections don't need to be refreshed manually, because both Resources
# and perception dictionaries are mutable, so simply holding onto a reference is sufficient
# to get all necessary updates.

# Therefore, the "connect" function should usually be used to hardwire connections in place.

# When "connect" is used to link a condition function with a source of perceptions, you get
# a zero-argument goal_test_function suitable for use in a DifferenceEngine.
# Likewise, when "connect" is used to link an action function with an environment, you get
# a reduce_difference_function of two arguments, resource and diff.

def connect(function_with_connections_kwarg, connections): # TODO: name connected functions more usefully
    def connected_function(*args):
        return function_with_connections_kwarg(*args, connections=connections)
    return connected_function

##### ABSTRACT MENTAL RESOURCES #####

class AbstractDifferenceEngine(object):
    def __init__(self, goal_test_function_unconnected, reduce_difference_function_unconnected, backchains_unconnected):
        self.gtf_unc = goal_test_function_unconnected
        self.rdf_unc = reduce_difference_function_unconnected
        self.bc_unc = backchains_unconnected

    def instantiate(self, mind, connections=[]): 
        try:
            goal_test_function = connect(self.gtf_unc, connections=connections)
            reduce_difference_function = connect(self.rdf_unc, connections=connections)
            backchains = [connect(bc, connections=connections) for bc in self.bc_unc]
        except(KeyError):
            print "DifferenceEngine did not receive necessary connection for instantiation."
            raise
        
        return DifferenceEngine(mind, goal_test_function, reduce_difference_function, backchains, connections=connections)


##### MENTAL RESOURCES #####

class MentalResource(object):
    def __init__(self,mind,connections=[]):

        self.is_on = False # whether resource is on
        self.connections = connections

        mind.all_resources.append(self)
        # No self.mind pointer is kept around anymore - only connections,
        # which COULD contain a "mind" connection if that's really what
        # was intended.

class Critic(MentalResource):

    def __init__(self, mind, condition_function, resources_to_turn_on=[], connections=[]):
        MentalResource.__init__(self,mind,connections=[])
        # sub-class of MentalResource, inherits:
        #  - self.is_on means this reource is engaged during the cycle
        #  - self.mind points to the instance of the cognitive architecture

        self.is_active = False # is_active means the preconditions are met
        self.name = condition_function.__name__

        # rule to determine whether or not the conditions are met 
        self.condition_function = condition_function

        self.resources_to_turn_on = resources_to_turn_on

    def execute(self):
        """ returns true if all preconditions are met""" 
        if self.condition_function(): # (doesn't need to be called with "self" anymore)
            # if condition is met, turn on certain selectors
            if not self.is_active:
                for res in self.resources_to_turn_on: 
                    res.is_on = True
                    res.is_active = True
                #self.mind.new_goals += self.resources_to_turn_on
            self.is_active = self.is_on # short circuit is_active
        else:
            self.is_active = False 
        return self.is_active  

class Selector(MentalResource):
    """ """

    def __init__(self, mind, active_function, backchains=[], connections = []):
        # sub-class of MentalResource, inherits:
        #  - self.is_on means this reource is engaged during the cycle
        #  - self.mind points to the instance of the cognitive architecture
        # active_function takes actions
        MentalResource.__init__(self,mind,connections=[])
        # function to execute whenever is_on==True 
        self.active_function = active_function
        # is_active stores response of active_function (for meta-reasoning)
        self.is_active = False
        # remember name of function, for debugging
        self.name = active_function.__name__
        # ways to go when things get stuck
        # i.e. what to do when is_on and not is_active
        self.backchains = backchains

    def execute(self):
        """ execute() is called at each cog cycle if self.is_on == True
        always calls active_function, which has the responsibility of turning itself off """ 
        self.is_active = self.active_function(self)
        if self.is_on and not self.is_active:
            #if self.mind.debug:  dprint(self.name)
            # cannot run active_function: turn on backchains
            for de in self.backchains:
                de.is_on          = True
                #print "++ Turning on - ", de.name
            #self.mind.new_goals +=self.backchains
            self.is_active = True


class DifferenceEngine(Selector):
    """Difference Engines are kinds of selectors. 
        
        diff = goal_test_fuction(self) - returns 0 if there is no difference (e.g. goal has been met)
          and returns a difference (diff) otherwise, which can be used to modulate the behavior of
          of the selector
        reduce_difference_function(diff)
        backchains - a list of resources to turn_on iff is_on==True and is_active==False
     """

    def __init__(self, mind, goal_test_function, reduce_difference_function, backchains=[], connections=[]):
        self.is_active = False

        def take_action_to_reduce_difference(myself):
            # see if any difference exists
            diff = goal_test_function()
            if diff == True:
                if mind.debug: print "-- %s, turning off %s " % (diff, myself.name)
                # run difference function once more to shut it's subgoals off if it wants.
                #reduce_difference_function(myself,diff)
                # turn Selector off
                myself.is_on = False
                if not self.is_active:
                    return False # don't run action unless it's already on
            return reduce_difference_function(diff)

        Selector.__init__(self,mind,take_action_to_reduce_difference,backchains,connections=connections)
        fnames = "%s_%s" % (goal_test_function.__name__, reduce_difference_function.__name__)
        self.name = "diffeng__%s" % fnames.replace("__","_")


class LearningDifferenceEngine(DifferenceEngine):
    def __init__(self, mind, goal_test_function, action_function, backchains=[]):
        self.is_active = False
        self.last_frame = []
        self.concept_learner = concept_learning.VersionSpaceLearner()
        self.__name__ = "learning_de_%s" % (action_function.__name__)
        def learned_reduce_difference_function(myself, diff):
            if diff == True:
                # goal has been met
                if self.last_frame != []:
                    print "********* Adding positive example", self.last_frame
                    self.concept_learner.add_positive_example(self.last_frame)
                    myself.is_on == False
                self.concept_learner.print_hypotheses()
                return True
            elif diff == False:
                if self.last_frame != []:
                    print "********* Adding negative example", self.last_frame
                    self.concept_learner.add_negative_example(self.last_frame)
                action_function(myself)
                self.last_frame = myself.mind.perceptions
                self.concept_learner.print_hypotheses()
                return False
        DifferenceEngine.__init__(self,mind,goal_test_function,learned_reduce_difference_function,backchains)

class SensorySystem(): # currently a very thin object. enables connections just to this subsystem
    def __init__(self):
        perceptions = {}

class CriticSelectorArchitecture():

    def __init__(self,debug=True,name="Ralph",*args,**kwargs):
        # store the name of the agent to control
        self.name = name
        #try:
        if True:
            # connect to environment via XML-RPC
            self.env = xmlrpclib.ServerProxy('http://localhost:8001')
            start = time.clock()
            self.env.do('meta_step',{'seconds':0.2,'agent':self.name})
            self.delay = time.clock()-start
            print "Delay: ", self.delay
        else:#except:
            print "Error: Cannot connect to the simulator." 
            sys.exit()
        self.debug = debug  # outputs error messages
        # sensory representation of the immediate world state (updated each step())
        self.sensorysystem = SensorySystem()
        self.all_resources = []
        self.reactive_resources = []
        self.deliberative_resources = []
        self.reflective_resources = []

        self.turned_on = []
        self.turned_off = []
        self.pre_expectation_frame = {} # keep track of last state to add
        # actions primitives: together allow selectors to be defined over temporal intervals. 
        # multiple actions can be executed simulatenously
        self.actions = {'turn_left-start':[],\
                        'turn_left-stop':[],\
                        'turn_right-start':[],\
                        'turn_right-stop':[],\
                        'move_forward-start':[],\
                        'move_backward-start':[],\
                        'move_forward-stop':[],\
                        'move_backward-stop':[],\
                        'look_right-start':[],\
                        'look_right-stop':[],\
                        'look_left-start':[],\
                        'look_left-stop':[],\
                        'look_up-start':[],\
                        'look_up-stop':[],\
                        'look_down-start':[],\
                        'look_down-stop':[],\
                        'pick_up_with_right_hand':['object'],\
                        'pick_up_with_left_hand':['object'],\
                        'say':['message'],\
                        'drop_from_right_hand':[],\
                        'drop_from_left_hand':[]}
        # how many cycles has the agent run? 
        self.age = 0


    def add_reactive_resource(self, resource):
        self.reactive_resources.append(resource)
        return resource

    def add_deliberative_resource(self, resource):
        self.deliberative_resources.append(resource)
        return resource

    def add_reflective_resource(self, resource):
        self.reflective_resources.append(resource)
        return resource

    def execute_reactive_resources(self):
        for resource in self.reactive_resources:
            if resource.is_on:
                resource.execute()

    def execute_deliberative_resources(self):
        for resource in self.deliberative_resources:
            if resource.is_on:
                resource.execute()

    def execute_reflective_resources(self):
        for resource in self.reflective_resources:
            if resource.is_on:
                resource.execute()

    def execute_all_resources(self):
        for resource in self.all_resources:
            if resource.is_on:
                resource.execute()

    def sense(self):
        """ This method asks the environment to return a frame-structure of perceptual
        data, and is called each step.  It prints the sensory frame to the terminal. """
        self.sensorysystem.perceptions = self.env.do('sense', {'agent':self.name})
        print "result of sense", self.env.do('sense', {'agent':self.name})
        if self.debug:
            print "Perceiving: "
            for modality, data in self.sensorysystem.perceptions.items():
                print "\t%s : %s" % (modality, data)

    def step(self,seconds=0.1):
        """ Step function 1) senses, 2) executes all layered resources (which tell "body"
        which actions to engage, then 3) executes simulator for X seconds (defined by 
        'seconds' variable."""

        self.age += 1
        # tell the terminal how old you are
        print "Step %i" % (self.age)
        
        state_1 = [x for x in self.all_resources if x.is_on]
        self.sense() # sense the world which returns perceptions, 
        #print "ALL resources", self.all_resources
        for r in self.all_resources:
            if r.is_on: print "+", r.name

        self.execute_all_resources()
        #self.execute_reactive_resources()
        #self.execute_deliberative_resources()
        #self.execute_reflective_resources()
        state_2 = [x for x in self.all_resources if x.is_on]
        self.turned_on = set(state_2)-set(state_1)
        self.turned_off = set(state_1)-set(state_2)
        for resource in self.turned_on:
            dprint(x.name,"ON: ")
        for resource in self.turned_off:
            dprint(x.name,"OFF: ")
            
        self.env.do('step_simulation',{'seconds':seconds, 'agent':self.name}) # simulator is paused by default, run for X seconds
        time.sleep(seconds+(self.delay*2)) # make sure agent waits as long as simulator
        return True

    def run(self,times=0,seconds=0.1):
        """ This method calls step 'times' times, or  indefinitely if times=0 """
        ct = 1
        self.step(seconds) # first step
        while times != ct:
            try:
                self.step(seconds) # rest of steps
                ct += 1
            except KeyboardInterrupt:
                print "Killing agent" # kill agent without causing a ton of debugging messages to flood terminal
    


