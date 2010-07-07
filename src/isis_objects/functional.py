class IsisFunctional():

    def __init__(self, states=None):
        if states == None:
            self.states = {}
        else:
            self.states = states

    def registerState(self,stateName,valueDomain):
        self.states[stateName] = valueDomain


class Dividable(IsisFunctional):
    def __init__(self,piece=None):
        if piece == None:
            print "Warning: no piece object defined for Dividable object", self.name
            self.piece = self.models['default']
        else:
            self.piece = piece

    def action_divide(self, agent, object):
        if object != None and isinstance(object, SharpObject):
            if agent.right_hand_holding_object:
                agent.control__put_object_in_empty_right_hand(self.piece.generate_instance(self.physicsManager))
                return true
            elif agent.left_hand_holding_object:
                agent.control__put_object_in_empty_right_hand(self.piece.generate_instance(self.physicsManager))
                return true
        return false

class Sharp(IsisFunctional):
    def __init__(self):
        pass

    def cut(self,other):
        print "ouch"






