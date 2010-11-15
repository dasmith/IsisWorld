from direct.task import Task, TaskManagerGlobal

class IsisFunctional():

    def __init__(self):
        #self.setTag('pickable','true')
        if not hasattr(self,'states'):
            self.states = {}
    
    def list_actions(self):
        """ Lists all of the action__X methods a particular IsisObject will respond to."""
        return filter(lambda x: x[0:8] == "action__",dir(self))

    def registerState(self,stateName,valueDomain):
        if not hasattr(self,'states'):
            self.states = {}
        self.states[stateName] = valueDomain

    def retrieveState(self,stateName):
        if self.states.has_key(stateName):
            return self.states[stateName]

    def call(self, agent, action, dobject = None):
        """ This is the dispatcher for the action methods """
        print "CALLING %s ON %s WITH %s" % (action,self.name,dobject)
        if hasattr(self, "action__"+action):
            return getattr(self, "action__"+action)(agent, dobject)
        else:
            print "Error, %s does not respond to action__%s" % (self.name, action)

class Spreadable(IsisFunctional):
    # This superclass should be inherited by objects that can be "spread" over other objects
    # For example, butter can be "spread" onto a knife, plate, or piece of bread
    def __init__(self):
        IsisFunctional.__init__(self)
        # TODO If there are attributes, use hasattr to make sure self has them!
        
    def action__spread(self, agent, object):
        # agent is the 'person' who is interacting with self and object
        # object is the other object that this is spreading on, such as a knife or piece of bread
        # TODO write code to spread self onto object
        print "in action__spread"
        if object != None and hasattr(object, 'action__surface'):
            object.action__surface(agent, self) # the surface will then put this object on itself
            # TODO confirm that this is the right pattern to follow, or if it needs changing
            return "success"
        return None

class SurfaceForSpreadable(IsisFunctional):
    # This superclass should be inherited by objects on which Spreadable objects can be spread
    # e.g. knife, bread, toast
    def __init__(self):
        IsisFunctional.__init__(self)
        # It's possible that it might be better design to initialize this objecth here
        # instead of leaving it up to the subclass?
        # The following is what other classes in this module did
        #if not hasattr(self, 'spreadableOnSelf'):
         #   print "Warning: no spreadableOnSelf object defined for SurfaceForSpreadable object", self.name
        self.spreadableOnSelf = None     
        
    def action__surface(self, agent, object):
        # agent is the 'person' and object should be the Spreadable thing going on this surface
        print "in action__surface"
        if object != None and hasattr(object, 'action__spread'):
            if self.spreadableOnSelf == None:
                self.spreadableOnSelf = object
                return "success"
            else:
                # There is already something spread on this object
                # TODO decide what to implement in this case
                print "tried to spread ", object, " onto surface ", self.name, \
                      " but it already has ", self.spreadableOnSelf
        return None

class TransfersSpreadable(SurfaceForSpreadable):
    # This class represents a SurfaceForSpreadable that can transfer its spreadable
    # object to another SurfaceForSpreadable
    def __init__(self):
        SurfaceForSpreadable.__init__(self)
    
    def action__transfer(self, agent, object):
        # agent is the 'person' and object is the target that will receive self's Spreadable
        # object must be a SurfaceForSpreadable
        print "in action__transfer"
        if object != None and hasattr(object, 'action__surface'):
            if self.spreadableOnSelf == None:
                print "tried to transfer a Spreadable from ", self.name, " to ", object, \
                      " but ", self.name, " has no Spreadable on it"
            else:
                object.action__surface(agent, self.spreadableOnSelf)
                self.spreadableOnSelf = None # Not on this surface anymore
                return "success"
        return None

class Dividable(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)
        if not hasattr(self,'piece'):
            print "Warning: no piece object defined for Dividable object", self.name

    def action__divide(self, agent, object):
        if object != None and hasattr(object, "action__cut"):
            if agent.right_hand_holding_object == None:
                # instantiate a new IsisObject
                obj = self.piece()
                return agent.pick_object_up_with(obj, agent.right_hand_holding_object, agent.player_right_hand)
            elif agent.left_hand_holding_object == None:
                obj = self.piece()
                return agent.pick_object_up_with(obj, agent.left_hand_holding_object, agent.player_left_hand)
        return None


class Cookable(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)
        self.registerState("cooked", False)

        if not hasattr(self,'cookableRawModel'):
            self.cookableRawModel = "default"
        if not hasattr(self,'cookableCookedModel'):
            print "Warning: %s has no Cookable.cookableCookedModel model defined, using default." % self.name
            self.cookableCookedModel = "default"
        self.changeModel(self.cookableRawModel)

    def action__cook(self, agent, object):
        """ This defines an action that changes the state and the corresponding model."""
        self.changeModel(self.cookableCookedModel)
        self.registerState("cooked", True)


class Sharp(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)

    def action__cut(self, agent, object):
        print "ouch"
        return "success"


class OnOffDevice(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)
        self.registerState("power", False)
    def action__turn_on(self, agent, object):
        self.registerState("power", True)
    def action__turn_off(self, agent, object):
        self.registerState("power", False)


class Cooker(OnOffDevice):
    def __init__(self):
        OnOffDevice.__init__(self)
        if not hasattr(self,'cook_in'):
            self.cook_in = False
        if not hasattr(self,'cook_on'):
            self.cook_on = False

    def action__turn_on(self, agent, object):
        OnOffDevice.action__turn_on(self, agent, object)
        taskMgr.doMethodLater(5, self.__timerDone, "Cooker Timer", extraArgs = [])
        return "success"

    def __timerDone(self):
        self.cook(None, None)
        self.action__turn_off(None, None)

    def cook(self, agent, object):
        print "Cooking..."
        if self.cook_on:
            for obj in self.on_layout.getItems():
                print obj.name
                obj.call(agent, "cook", object)
        if self.cook_in:
            for obj in self.in_layout.getItems():
                print obj.name
                obj.call(agent, "cook", object)
        print "done."
