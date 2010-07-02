#!/usr/bin/env python

'''
A simple reactive agent that looks for the toas

Opens connection to local xmlrpc server on port 8001 and runs a reactive agent

Authors: Bo Morgan, Dustin Smith

History:
    0: 2010-03-17   Initial Release
    1: 2010-03-18   Added more comments
    2: 2010-03-22   Moved backchaining to DifferenceEngine class (som/arch.py)

'''

from agents.som.arch import CriticSelectorArchitecture, DifferenceEngine, Critic, Selector

class TestRalph(CriticSelectorArchitecture):
    """ Reactive Ralph has critic selector pairs for

       Upon initialization, it creates a connection with the XML-RPC server
    """

    def __init__(self,*args,**kwargs):
        CriticSelectorArchitecture.__init__(self,*args,**kwargs)
        print "pause", self.env.do('meta_pause')
        print "turn left", self.env.do('turn_left-start', {'agent_id':2})
        print "get commands", self.env.do('meta_list_actions')
        self.env.do('sense')
        self.env.do('turn_left-stop')
ralph = TestRalph(debug=True) # set debug=False to hide many output messagesFKJ<LeftMouse>K<LeftMouse>
ralph.step()   # to step ralph once
# ralph.run(1) # to step ralph once
# ralph.run(2) # to run ralph 2x
# ralph.run()  # to run ralph indefinitely
