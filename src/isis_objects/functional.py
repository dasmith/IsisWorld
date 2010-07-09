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
    def action__pick_up(self, agent, object):
        if self.getNetTag('heldBy') == '':
            # this the thing is not current held, OK to pick up
            self.disableCollisions()
            print "ATTACHING TO", object 
            self.setHpr(0, 0, 0)
            self.reparentTo(object)
            self.setPos(0, 0, 0)
            self.setTag('heldBy', agent.name)
            return 'success'
        else:
            return "Error: already held by someone"

    def take(self, parent):
        """ Allows Ralph to pick up a given object """
        if self.weight < 5000:
            self.reparentTo(parent)
            self.heldBy = parent

    def drop(self):
        """ Clears the heldBy variable """
        self.heldBy = None

class Dividable(IsisFunctional):
    def __init__(self,piece=None):
        IsisFunctional.__init__(self)
        if piece == None:
            print "Warning: no piece object defined for Dividable object", self.name
        self.piece = piece

    def action__divide(self, agent, object):
        if self.piece and object != None and isinstance(object, SharpObject):
            if not agent.right_hand_holding_object:
                agent.control__put_object_in_empty_right_hand(self.piece("bread", self.physicsManager))
                return true
            elif not agent.left_hand_holding_object:
                agent.control__put_object_in_empty_right_hand(self.piece.generate_instance(self.physicsManager))
                return true
        return false

class Sharp(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)

    def action__cut(self,other):
        print "ouch"






