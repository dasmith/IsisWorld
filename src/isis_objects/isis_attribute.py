#!/usr/bin/env python
"""
ATTRIBUTE SPECIFICATIONS:

The state of an object should be *entirely* sepcified by its attributes and values.  Values
are represented as two different lists: the current_value and the possible_value (its domain).

Here are the types of attributes and a description and conventions for how to use them.

  1.  Binary Attributes
    - begin the names of these attributes, 'is_X'
    - the most common state should the default value, which is False
    - no "in between" True/False values
    
    - Properties:
      1. name : name of the attribute
      2. visible: [default = True] whether or not the agent sees this property by on sense by default
      3. on_change_func: [default = None] callback function
      
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
      4. exhaustive? [default = False]: means that the possible range
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


"""

class IsisAttribute(object):
    """
    The state of an object should be *entirely* sepcified by its attributes and values.  Values
    are represented as two different lists: the current_value and the possible_value (its domain).

    Here are the types of attributes and a description and conventions for how to use them.
    """
    def __init__(self, name, visible, on_change_fun):
        
        self.name = name
        self.visible = visible
        self._callback_function = on_change_fun
        # range of actual and possible values
        self._possible_values = None
        self._possible_values_classes = [] # type checking
        self._actual_value = None
        # properties
        self._is_monotonic = False
        self._is_single_valued = True
        self._is_unique = True

        self._func_cmp = lambda x,y: x < y

    def set_value(self, new_value):
        """ The logic behind enforcing the changing of attributes and values. """
        if self._possible_values != None:
            if not new_value in self._possible_values:
                raise Exception("IsisAttribute Error: Value %d not in domain of attribute %s " % (new_value, self.name))
        elif len(self._possible_values_classes) != 0:
            if not new_value.__class__.__name__ in self._possible_values_classes:
                 raise Exception("IsisAttribute Error: Value %d not in domain type '%s' for attribute %s " \
                 % (new_value, ', '.join(self._possible_values_classes), self.name))
        if self._is_monotonic and (self._actual_value != None and self._func_cmp(new_value, self._actual_value)):
            raise Exception("IsisAttribute Set Error: Monotonic property of attribute %s violated: %s > %s "\
             % (self.name, self._actual_value, new_value))
        if self._callback_function != None:
            self._callback_function(self._actual_value, new_value)
        if self._is_single_valued:
            # overwrite existing value
            self._actual_value = new_value
        else:
            if self._actual_value == None:
                if self._is_unique:
                    self._actual_value = set([new_value])
                else:
                    self._actual_value = [new_value]
            else:
                if self._is_unique:
                    self._actual_value.add(new_value)
                else:
                    self._actual_value.append(new_value)
    
    def set_callback(self, callback_function):
        self._callback_function = callback_function

    def add_value(self, new_value):
        """ Adds a value to the list of actual values.  Only works to the
        values that _is_single_valued = True """
        if self._is_single_valued:
            print "Cannot add a value to single-valued attribute"
        else:
            self.set_value(new_value)
    
    def pop_value(self):
        """ Removes and returns a value from a list of actual values.  Only works to the
        values that _is_single_valued = True """
        if self._is_single_valued:
            print "Cannot pop a value from a single-valued attribute"
        elif self._actual_value != None:
            v = self._actual_value.pop()
            if len(self._actual_value) == 0:
                self._actual_value = None
            return v
    
    def get_value(self):
        """ Returns the value for the particular attritube """
        if isinstance(self._actual_value,set):
            return list(self._actual_value)
        else:
            return self._actual_value

class BinaryAttribute(IsisAttribute):
    """
    1.  Binary Attributes
      - begin the names of these attributes, 'is_X'
      - the most common state should the default value, which is False
      - no "in between" True/False values

      - Properties:
        1. name : name of the attribute
        2. visible : whether or not the attribute is visible
        3. on_change_func : optionall call back function

      - Examples: 
         * FunctionalElectronic::is_on = {True,False}
         * FunctionalOpenable::is_open = {True,False}
    """
    def __init__(self, name, visible=False, on_change_func=None):
        IsisAttribute.__init__(self, name, visible, on_change_func)
        if name[0:3] != "is_":
            print "Warning: binary IsisAttribute '%s' violates naming convention, it should start with 'is_'" % (name)
        self._possible_values = [True, False]
        self._actual_value = True

class NominalAttribute(IsisAttribute):
    """
    2.  Nominal Attributes
      - represents an unordered set of values.
      - a generalization of Binary Attributes

      - Properties
        1. name : name of the attribute
        2. max_number [default = None]: the maximum number of values
        3. is_unique? [default = True]: allow duplicates?
        4. is_single_valued? [default = True]: otherwise, treats value as a set or list (depending on is_unique?)
        5. exhaustive? [default = False]: means that the possible range
           of values is already in the set, and that new assignments
           can only come from existing members of the set.

      - Examples:
        * IsisFunctional::owners = {[names of IsisAgents that own the object]}
           - max_number=None, unique?=True, 
    """
    def __init__(self, name, domain=None, visible=False, max_number=None, is_unique=True, is_single_valued=True, on_change_func=None):
        IsisAttribute.__init__(self, name, visible, on_change_func)
        self._possible_values = domain
        self._is_unique = is_unique
        self._is_single_valued = is_single_valued
        if not (is_unique or is_single_valued):
            print "Warning: In attribute %s unique is False, to make a difference: is_single_valued must = True." % self.name
            
        # actual value is first element of domain
        #if domain != None:
        #    self._actual_value = domain[0]


class OrderedAttribute(IsisAttribute):
    """
    3. Ordered Attributes
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
    """
    def __init__(self, name, domain=None, domain_types=None, visible=False, is_monotonic=False, on_change_func=None):
        IsisAttribute.__init__(self, name, visible, on_change_func)
        if domain != None:
            self._possible_values = domain
        if domain_types != None:
            for dt in domain_type:
                if not isinstance(dt,str):
                    raise "Domain type specifications must be strings! %d is not. " % (dt)
            self._possible_values_classes = domain_types
        self._is_monotonic = is_monotonic
        

if __name__ == '__main__':
    
    # test binary attributes
    def func(f,t):
        print "Changing %s to %s" % (f, t)

    x = BinaryAttribute(name='binary')
    print x.get_value()
    assert x.get_value() == True
    x.set_value(False)
    assert x.get_value() == False
    print x.get_value()

    # test ordered attributes
    x = OrderedAttribute(name='monotonic', is_monotonic=True)
    assert x.get_value() == None
    x.set_value(10)
    assert x.get_value() == 10
    x.set_value(15)
    try:
        x.set_value(12) # should fail
    except Exception, e:
        print e
    else:
        raise "Monotonic-constraint not caught"
    
    # test nominal attributes
    n = NominalAttribute(name='contains', is_unique=True, is_single_valued=False)
    n.add_value('butter')
    n.add_value('jam')
    n.add_value('jam')
    print n.get_value()
    assert n.get_value() == set(['butter','jam'])
    o = NominalAttribute(name='owner', is_unique=False, is_single_valued=False)
    o.add_value('Joe')
    o.add_value('Joe')
    print o.get_value()
    assert o.get_value() == ['Joe','Joe']
