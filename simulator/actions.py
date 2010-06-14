
class IsisAction():
    """ This class defines the actions that are available to the agent in IsisWorld """
    def __init__(self, commandName, commandFunct=None, intervalAction=False, keyboardBinding=None):
        # commandName is what XML-PRC must call to execute the action
        self.commandName = commandName
        # if the command has a keymapping, define it here
        self.keyboardBinding = keyboardBinding
        # if the command is an interval action, meaning once it is
        # started, it continues until it is stopped, set this to true
        # if this is true, it:
        #  1) makes a pair of functions: commandName-start, commandName-stop
        #     to engage and disengage the action
        #  2) when there is a keyboardBinding, it adds the '_up' statement
        #     to stop the command when the key is released
        self.intervalAction=intervalAction
        # define the command function
        if commandFunct == None:
            commandFunct = "print 'The function %s is undefined'" % self.commandName
        else:
            commandFunct = commandFunct

    def execute(self,agent):
        eval(commandFunct)


class ActionController():
    """ This initializes a set of IsisActions and is responsible for
    dispatching these actions"""

    def __init__(self,versionNumber):
        self.actionMap = {} 
        self.keyboardMap= {} 
        self.versionNumber = versionNumber

    def hasAction(self,action):
        """ Tells whether the ActionController has this action defined"""
        return action in self.actionMap.keys()

    def hasKeyboard(self,action):
        """ Tells whether the ActionController has this action defined"""
        return action in self.keyboardMap.keys()

    def haveAgentDo(self,command,agent):
        print "trying to", command, "on", agent
        """ Given a command and an agent pointer, tell the agent
        to do that command"""
        eval("agent.%s" % command)

    def addAction(self,action):
        if action.intervalAction:
            # define start and stop commands
            self.actionMap["%s-start" % action.commandName]="control__%s__start()" % action.commandName
            self.actionMap["%s-stop" % action.commandName]="control__%s__start()" % action.commandName
            if action.keyboardBinding:
                self.keyboardMap["%s" % action.keyboardBinding]="control__%s__start()" % action.commandName
                self.keyboardMap["%s_up" % action.keyboardBinding]="control__%s__stop()" % action.commandName
        else:
            self.actionMap["%s" % action.commandName]="control__%s()" % action.commandName
            if action.keyboardBinding:
                self.keyboardMap["%s" % action.keyboardBinding]="control__%s()" % action.commandName
