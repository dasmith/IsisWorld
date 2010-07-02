

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
        """ This method isn't used right now.  All IsisActions look for the corresponding
        Ralph.control__[command_name]() method and execute it."""
        pass
        #eval(commandFunct)


class ActionController():
    """ This initializes a set of IsisActions and is responsible for dispatching these actions.

    Actions are currently defined in the IsisWorld.setupControls() method.   Version numbers
    are intended to help clients remember which set of actions they are interacting with.
    """

    def __init__(self,versionNumber):
        self.actionMap = {} 
        self.keyboardMap= {}
        self.helpStrings = []
        self.versionNumber = versionNumber

    def hasAction(self,action):
        """ Tells whether the ActionController has this action defined"""
        return action in self.actionMap.values() or action in self.actionMap.keys()

    def makeAgentDo(self,agent,command,args={}):
        """ Given a command and an agent pointer, tell the agent to do that command"""
        result = eval("agent.%s(%s)" % (command,','.join(map(lambda a: '%s=args[%s]' % (a,a), args.keys()))))
        # None objects are not serializable by XML-RPC
        print "Making agent do", result
        if result == None:
            return "success"
        else:
            return result

    def addAction(self,action):
        """ Adds an action to the actionMap, containing commands that can be controlled through XMLRPC"""
        if action.keyboardBinding:
            self.helpStrings.append("Press [%s] to %s" % (action.keyboardBinding, action.commandName.replace("_"," ")))
        # initialize actions
        if action.intervalAction:
            # define start and stop commands
            self.actionMap["%s-start" % action.commandName]="control__%s__start" % action.commandName
            self.actionMap["%s-stop" % action.commandName]="control__%s__stop" % action.commandName
            if action.keyboardBinding:
                self.keyboardMap["%s" % action.keyboardBinding]="control__%s__start" % action.commandName
                self.keyboardMap["%s-up" % action.keyboardBinding]="control__%s__stop" % action.commandName
        else:
            self.actionMap["%s" % action.commandName]="control__%s" % action.commandName
            if action.keyboardBinding:
                self.keyboardMap["%s" % action.keyboardBinding]="control__%s" % action.commandName
