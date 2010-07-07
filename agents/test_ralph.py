#!/usr/bin/env python


from som.arch import *
import som.frame_utils as frame_utils
import som.concept_learning as concept_learning

class TestRalph(CriticSelectorArchitecture):

    def __init__(self,*args,**kwargs):
        CriticSelectorArchitecture.__init__(self)



# initialize the cog arch
ralph = Test(debug=False,name='Ralph')
ralph.resource.mind.env.do('turn_right-start')
#ralph.run(0,seconds=0.3)
