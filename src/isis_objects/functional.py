class IsisFunctional():

    def __init__(self, states=None):
        if states == None:
            self.states = {}
        else:
            self.states = states

    def registerState(self,stateName,valueDomain):
        self.states[stateName] = valueDomain

    def call(self, agent, action, dobject = None):
        """ This is the dispatcher for the action methods """
        try:
            return getattr(self, "action__"+action)(agent, dobject)
        except AttributeError:
            return None

    ## register actions that are enabled by default in all objects
    def action__pick_up(self, agent, directobject):
        if self.getNetTag('heldBy') == '':
            # this the thing is not current held, OK to pick up
            self.disableCollisions()
            print "ATTACHING TO", directobject
            self.setPosHpr(0,0,0,0,0,0)
            self.reparentTo(directobject)
            print "OFFSET", self.offsetVec
            self.activeModel.setPosHpr(*self.pickupVec)
            #self.place()
            self.setTag('heldBy', agent.name)
            return 'success'
        else:
            return "Error: already held by someone"

    def action__drop(self, agent, directobject):
        if self.getNetTag('heldBy') == agent.name:
            self.enableCollisions()
            self.wrtReparentTo(directobject)
            self.activeModel.setPosHpr(*self.offsetVec)
            self.setHpr(self.getH(), 0, 0)
            self.setPos(self, (0, 1.3, 1.5))
            self.setTag('heldBy', '')
            return 'success'
        else:
            return "Error: not being held by given agent"


class NoPickup(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)
  
    def action__pick_up(self, x,y):
        return 'failed: cannot pick up this object'

class Dividable(IsisFunctional):
    def __init__(self,piece=None):
        IsisFunctional.__init__(self)
        if piece == None:
            print "Warning: no piece object defined for Dividable object", self.name
        self.piece = piece

    def action__divide(self, agent, object):
        if self.piece and object != None and isinstance(object, Sharp):
            if not agent.right_hand_holding_object:
                print agent.control__put_object_in_empty_right_hand(self.piece("piece", self.physicsManager).name)
                return True
            elif not agent.left_hand_holding_object:
                print agent.control__put_object_in_empty_left_hand(self.piece("piece", self.physicsManager).name)
                return True
        return False

class Sharp(IsisFunctional):
    def __init__(self):
        IsisFunctional.__init__(self)

    def action__cut(self, agent, object):
        print "ouch"
        return "success"