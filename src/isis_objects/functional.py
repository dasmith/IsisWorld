from direct.task import Task, TaskManagerGlobal

class IsisFunctional():

    def __init__(self, states=None):
        if states == None:
            self.states = {}
        else:
            self.states = states
        self.layout = None;

    def registerState(self,stateName,valueDomain):
        self.states[stateName] = valueDomain

    def retrieveState(self,stateName):
        if self.states.has_key(stateName):
            return self.states[stateName]

    def setLayout(self, l):
        self.layout = l

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
            if self.layout:
                self.layout.remove(self)
                self.layout = None
            self.disableCollisions()
            self.setPosHpr(0,0,0,0,0,0)
            self.reparentTo(directobject)
            self.activeModel.setPosHpr(*self.pickupVec)
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
        if self.piece and object != None and hasattr(object, "action__cut"):
            if not agent.right_hand_holding_object:
                obj = self.piece("piece", self.physicsManager)
                obj.call(agent, "pick_up", agent.player_right_hand)
                agent.right_hand_holding_object = obj
                return "Success"
            elif not agent.left_hand_holding_object:
                obj = self.piece("piece", self.physicsManager)
                obj.call(agent, "pick_up", agent.player_left_hand)
                agent.left_hand_holding_object = obj
                return "Success"
        return False


class Cookable(IsisFunctional):
    def __init__(self, cooked, raw="default"):
        IsisFunctional.__init__(self)
        self.cookedModel = cooked
        self.registerState("cooked", False)
        self.changeModel(raw)

    def action__cook(self, agent, object):
        self.changeModel(self.cookedModel)
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
        self.registerState("powerOn", False)
    def action__turn_on(self, agent, object):
        self.registerState("powerOn", True)
    def action__turn_off(self, agent, object):
        self.registerState("powerOn", False)


class Cooker(OnOffDevice):
    def __init__(self, cook_in=True, cook_on=True):
        OnOffDevice.__init__(self)
        self.cook_in = cook_in
        self.cook_on = cook_on

    def action__turn_on(self, agent, object):
        OnOffDevice.action__turn_on(self, agent, object)
        taskMgr.doMethodLater(5, self.__timerDone, "Cooker Timer", extraArgs = [])

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