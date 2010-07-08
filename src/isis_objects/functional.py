class IsisFunctional():

    def __init__(self, states=None):
        if states == None:
            self.states = {}
        else:
            self.states = states

    def registerState(self,stateName,valueDomain):
        self.states[stateName] = valueDomain

    def call(self, agent, action, object = None):
        """ This is the dispatcher for the action methods """
        return getattr(self, "action__"+action)(agent, object)
        try:
            return getattr(self, "action__"+action)(agent, object)
        except AttributeError:
            return None
        #except:
        #    return None

    ## register actions that are enabled by default in all objects
    def action__pick_up(self, agent, action, object):
        if self.getNetTag('heldBy') == '':
            # this the thing is not current held, OK to pick up
            self.reparentTo(object)
            self.setPos(object, 0, 0, 0)
            self.setHpr(0, 0, 0)
            self.setTag('heldBy', agent.name)
            return 'success'
        else:
            raise "Error: already held by someone"

class Dividable(IsisFunctional):
    def __init__(self,piece=None):
        if piece == None:
            print "Warning: no piece object defined for Dividable object", self.name
            self.piece = self.models['default']
        else:
            self.piece = piece

    def action__divide(self, agent, object):
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






