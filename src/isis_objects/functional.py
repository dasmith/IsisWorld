from direct.task import Task, TaskManagerGlobal

"""
IsisFunctional is the base class for a hierarchy of commonsense object semantics.  

Its primary functionality is to represent the actions that the object can receive, 
the IsisEvents it can initiate, and the type and values of the attributes that are
affected by those actions and events.

I. Attribute specifications:

The state of an object should be *entirely* sepcified by its attributes and values.  Values
are represented as two different lists: the current_value and the possible_value (its domain).

Here are the types of attributes and a description and conventions for how to use them.

  1.  Binary Attributes
    - begin the names of these attributes, 'is_X'
    - the most common state should the default value, which is False
    - no "in between" True/False values
    
    - Properties:
      1. name : name of the attribute
      
    - Examples: 
       * FunctionalElectronic::is_on = {True,False}
       * FunctionalOpenable::is_open = {True,False}
       

  2.  Nominal Attributes
    - represents an unordered set of values.
    - a generalization of Binary Attributes
    
    - Properties
      1. name : name of the attribute
      2. max_number [default = None]: the maximum number of values
      3. unique? [default = True]: allow duplicates?
      4. default value [default = 1st element in list]
      5. exhaustive? [default = False]: means that the possible range
         of values is already in the set, and that new assignments
         can only come from existing members of the set.

    - Examples:
      * IsisFunctional::owners = {[names of IsisAgents that own the object]}
         - max_number=None, unique?=True, 
      
  3.  Ordered Attributes
    - represents an ordered list of values
    - attributes can potentially be infinite, and are not generated before hand.
    
    - Properties:
      1. name :
      2. values [default = number line] 
      3. cmp [default = attribute.__lt__(self,other)]: orders the values
      4. monotonic? [default = False]: when true, if the value changes, asserts that the
        new value is *greater than* the original.
    
    - Examples:
      * IsisDiscrete::cooked  [0,1,2,3,4]


II. Event specifications

Events are instantiated after a call back to the action.
The preconditions for an event should be checked in the action function, **before** instantiating the event.
Events have two main parts:
  
  1. Event Body:  what happens at each sub-step of the event
  2. Event Culmination:  what happens at the termination of the event (besides the event being removed from
    the event list)
  
Some events can do nothing in the body except see if it's time to terminate the event, thereby calling event_terminate() 
directly.

- Events that check for a certain condition to be met can check to do this in the event body.

"""

class IsisAttribute(object):
    """
    The state of an object should be *entirely* sepcified by its attributes and values.  Values
    are represented as two different lists: the current_value and the possible_value (its domain).

    Here are the types of attributes and a description and conventions for how to use them.
    """
    def __init__(self, name):
        
        self.name = name
        self._possible_values = None
        self._actual_value = None
        self._is_monitonic = False
        self._is_unique = True
        self._func_cmp = lambda x,y: x < y
        self._exhaustive = lambda : self._possible_values != None
    
    def setValue(self, new_value):
        """ The logic behind enforcing the changing of attributes and values. """
        if self._exhaustive:
            if not new_value in self._possible_values:
                raise Exception("IsisAttribute Error: Value %d not in domain of attribute %s " % (new_value, self.name))
        if self._monitonic and (self._actual_value != None and self._func_cmp(new_value, self._actual_value)):
            raise Exception("IsisAttribute Set Error: Montonic property of attribute %s violated: %s > %s "\
             % (self.name, self._actual_value, new_value))
        self._actual_value = new_value

class BinaryAttribute(IsisAttribute):
    """
    1.  Binary Attributes
      - begin the names of these attributes, 'is_X'
      - the most common state should the default value, which is False
      - no "in between" True/False values

      - Properties:
        1. name : name of the attribute

      - Examples: 
         * FunctionalElectronic::is_on = {True,False}
         * FunctionalOpenable::is_open = {True,False}
    """
    def __init__(self, name):
        IsisAttribute.init(self, name)
        if name[0:3] != "is_":
            print "Warning: binary IsisAttribute %s in violation of naming convention, should start with 'is_'"
        self._possible_values = [True, False]
        self._actual_value = True
        self._is_unique = True

class OrderedAttribute(IsisAttribute):
    

class IsisFunctional():

    def __init__(self):
        #self.setTag('pickable','true')
        if not hasattr(self,'states'):
            self.states = {}
    
    def list_actions(self):
        """ Lists all of the action__X methods a particular IsisObject will respond to."""
        return map(lambda x: x[9:], filter(lambda x: x[0:8] == "action__",dir(self)))

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



class FunctionalDoor(IsisFunctional):
    """ Implements the 'action__open' method, allowing a part of the model to be "opened"
    or "closed" by:
    
        1. visually change its spatial orientation of the openable part
        2. registering the binary state, as 'openState' = closed/opened.
    """
    
    def __init__(self):
        IsisFunctional.__init__(self)
        if not hasattr(self,'door'):
            print "Warning: no piece object defined for FunctionalDoor object", self.name
    
    def action__open(self, agent, directobj):
        print "Select method called"
        if self.retrieveState("openState") == "closed":
            Sequence(
                Func(self.registerState, "openState", "opening"),
                LerpPosHprInterval(self.door, 0.5, Vec3(.45, 2.4, .72), Vec3(-90, 0, 0)),
                Func(self.registerState, "openState", "opened")
            ).start()
        elif self.retrieveState("openState") == "opened":
            Sequence(
                Func(self.registerState, "openState", "closing"),
                LerpPosHprInterval(self.door, 0.5, Vec3(-.56, .6, .72), Vec3(0, 0, 0)),
                Func(self.registerState, "openState", "closed")
            ).start()



class Dividable(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)
        if not hasattr(self,'piece'):
            print "Warning: no piece object defined for Dividable object", self.name

    def action__divide(self, agent, direct_object):
        if direct_object != None and hasattr(direct_object, "action__cut"):
            if agent.right_hand_holding_object == None:
                # instantiate a new IsisObject
                obj = self.piece()
                return agent.pick_object_up_with(obj, agent.right_hand_holding_object, agent.player_right_hand)
            elif agent.left_hand_holding_object == None:
                obj = self.piece()
                return agent.pick_object_up_with(obj, agent.left_hand_holding_object, agent.player_left_hand)
            else:
                print "Error - no free hand"
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
