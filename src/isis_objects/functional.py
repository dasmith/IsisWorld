"""
IsisFunctional is the base class for a hierarchy of commonsense object semantics.  

Its primary functionality is to represent the actions that the object can receive, 
the IsisEvents it can initiate, and the type and values of the attributes that are
affected by those actions and events.

I. Attribute specifications:

The state of an object should be *entirely* sepcified by its attributes and values.  Values
are represented as two different lists: the current_value and the possible_value (its domain).

 - For more details, see the specification in isis_attribute.py

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
from direct.task import Task, TaskManagerGlobal

from isis_attribute import *

class IsisFunctional():
    """ Every object must inherit from this base-class."""
    
    def __init__(self):
        self.attributes = {}
    
    def get_all_action_names(self):
        """ Lists all of the action__X methods a particular IsisObject will respond to."""
        return map(lambda x: x[8:], filter(lambda x: x[0:8] == "action__",dir(self)))

    def get_all_attributes_and_values(self, visible_only=True):
        """ Returns all of the attributes and their values, filters to 
        only the visible attributes if this is defined. """
        return dict(map(lambda (x,y): (x,y.get_value()), filter(lambda (x,y): not visible_only or y.visible, self.attributes.items())))
    
    def has_attribute(self, attribute_name):
        """ Returns whether has attribute name """
        return self.attributes.has_key(attribute_name)
    
    def get_attribute(self, attribute_name):
        """ Returns the attribute. """
        return self.attributes[attribute_name]
    
    def get_attribute_value(self, attribute_name):
        if self.attributes.has_key(attribute_name):
            return self.attributes[attribute_name].get_value()
        else:
            print "Warning: %s does not have attribute %s " % (self.name, attribute_name)
            
    def pop_attribute(self, attribute_name):
        """ If the attribute contains multiple values,
        this removes and returns one element from the list/set. """
        return self.attributes[attribute_name].pop_value()

    
    def set_attribute(self, attribute_name, value):
        """ Attempts to set an attribute to a given value """        
        if self.attributes.has_key(attribute_name):
            return self.attributes[attribute_name].set_value(value)
        else:
            print "Warning: %s does not have attribute %s " % (self.name, attribute_name)
            return False

    def add_attribute(self, attribute, value=None):
        """ Creates a new attribute, which must be of type IsisAttribute, storing it in the
        self.attributes dictionary indexed by its name, and optionally sets its value. """
        if not isinstance(attribute, IsisAttribute):
            raise "Error: attribute %s of %s is not IsisAttribute" % (self.name, attribute)
        else:
            a_name = attribute.name
            # store attributes in dictionary
            self.attributes[a_name] = attribute
            if not value == None:
                self.attributes[a_name].set_value(value)
    

    
    def call(self, agent, action, indirect_object = None):
        """ This is the dispatcher for the action methods """
        print "CALLING %s ON %s WITH %s" % (action,self.name, indirect_object)
        if hasattr(self, "action__"+action):
            return getattr(self, "action__"+action)(agent, indirect_object)
        else:
            print "Error, %s does not respond to action__%s" % (self.name, action)


class FunctionalCountable(IsisFunctional):
    """ This is the base-class for all count-nouns.
    """
    def __init__(self):
        IsisFunctional.__init__(self)
        self.add_attribute(NominalAttribute(name='owners', is_unique=True, is_single_valued=False))
        self.add_attribute(NominalAttribute(name='covered_in', is_unique=True, is_single_valued=False))

        def __action_cook_callback(start_val, end_val):
            """ Changes the appearance of the cooked item to match the cooked state.
            If it is cooked more than 3 times, then it dispapears?"""
            print "Cooked callback called for ", self.name
            if not hasattr(self,'cookableRawModel'):
                self.cookableRawModel = "default"
            if not hasattr(self,'cookableCookedModel'):
                print "Warning: %s has no Cookable.cookableCookedModel model defined, using default." % self.name
                self.cookableCookedModel = "default"
            #self.changeModel(self.cookableRawModel)

        self.add_attribute(OrderedAttribute(name='cooked', domain=[0,1,2,3], visible=True, is_monotonic=True, on_change_func=__action_cook_callback), value=0)
    
    def action__smear(self, agent, direct_object):
        """ Transfers the 'covered_in' attributes from direct_object
        to the current object.
        
        FUTURE: should this be generalized into a 'event-of-transfer'?
        """
        transferred_substances = []
        if direct_object.has_attribute('covered_in'):
            cia = direct_object.get_attribute('covered_in')
            value = cia.pop_value()
            while value != None:
                self.add_attribute_value('covered_in', value)
                value = cia.pop_value()

    def action__cook(self, agent, object):
        """ This defines an action that changes the state and the corresponding model."""
        self.changeModel(self.cookableCookedModel)
        # TODO: if there is no model, just make it darker
        self.set_attribute('cooked', (self.get_attribute_value('cooked')+1))


class FunctionalMass(IsisFunctional):
    """ FunctionalMass is used for defining objects where their parts are also pieces of the self-same
    object, like water, butter, jelly.
    """
    def __init__(self):
        IsisFunctional.__init__(self)
        #self.add_attribute(NominalAttribute(name='owners', is_unique=True, is_single_valued=False))


class FunctionalDoor(IsisFunctional):
    """ Implements the 'action__open' method, allowing a part of the model to be "opened"
    or "closed" by:
    
        1. visually change its spatial orientation of the openable part
        2. registering the binary state, as 'openState' = closed/opened.
    """
    
    def __init__(self):
        IsisFunctional.__init__(self)
        self.add_attribute(BinaryAttribute(name='is_open',visible=True), value=False)
    
    def afterSetup(self):
        if not hasattr(self,'door'):
            print "Warning: no door object defined for FunctionalDoor object", self.name



class FunctionalDividableCountable(FunctionalCountable):
    def __init__(self):
        FunctionalCountable.__init__(self)
        if not hasattr(self,'_functional__dividable_piece'):
            print "Warning: no piece object defined for Dividable object", self.name

    def action__divide(self, agent, direct_object):
        if direct_object != None and hasattr(direct_object, "action__cut"):
            if agent.right_hand_holding_object == None:
                # instantiate a new IsisObject
                obj = self._functional__dividable_piece()
                return agent.pick_object_up_with(obj, agent.right_hand_holding_object, agent.player_right_hand)
            elif agent.left_hand_holding_object == None:
                obj = self._functional__dividable_piece()
                return agent.pick_object_up_with(obj, agent.left_hand_holding_object, agent.player_left_hand)
            else:
                print "Error - no free hand"
        return None

class FunctionalDividableMass(FunctionalCountable):
    def __init__(self):
        FunctionalCountable.__init__(self)
        if not hasattr(self,'piece'):
            print "Warning: no piece object defined for Dividable object", self.name

    def action__scoop(self, agent, direct_object):
        if direct_object != None and direct_object.has_attribute('covered_in'):
            direct_object.add_attribute_value(self.name)
        else:
            print "Error, you cannot scoop something without a covered_in attribute like" % self.direct_object
            return None


class FunctionalSharp(FunctionalCountable):
    def __init__(self):
        FunctionalCountable.__init__(self)

    def action__cut(self, agent, object):
        print "action_cut called"
        return "success"


class FunctionalElectronic(FunctionalCountable):
    def __init__(self):
        FunctionalCountable.__init__(self)
        self.add_attribute(BinaryAttribute(name='is_on',visible=True), value=False)

    def action__turn_on(self, agent, object):
        self.set_attribute('is_on', True)

    def action__turn_off(self, agent, object):
        self.set_attribute('is_on', False)

class FunctionalCooker(FunctionalElectronic):
    """ This device must be a container and an on-off device.
    
    When turned on, it increments the cooked value for each item inside of the container.
    
    """
    def __init__(self):
        FunctionalElectronic.__init__(self)
        if not hasattr(self,'cook_in'):
            self.cook_in = False
        if not hasattr(self,'cook_on'):
            self.cook_on = False
        
        return True
        
        def launch_turn_cooker_on_isis_event():
            # check preconditions for
            # x = IsisEvent()
            print "Could not turn on cooker because...."
                
        self.add_attribute_callback('is_on', launch_turn_cooker_on_isis_event)
    
        #taskMgr.doMethodLater(5, self.__timerDone, "Cooker Timer", extraArgs = [])

    def action__cook(self, agent, direct_object):
        print "Cooking...", direct_object, " in ", self.name
        if self.cook_on:
            for obj in self.on_layout.getItems():
                print obj.name
                obj.call(agent, "cook", direct_object)
        if self.cook_in:
            for obj in self.in_layout.getItems():
                print obj.name
                obj.call(agent, "cook", direct_object)
        print "done."
