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