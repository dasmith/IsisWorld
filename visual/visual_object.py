'''
Created on Jan 14, 2010

@author: glebk
'''

import re # for name changing

class Visual_Object(object):
    '''
    A Visual_Object defines a physical object having a position
    and dimensions or model file.  We pass visual objects to the
    simulator which then creates a visualization of them.
    '''

    def __init__(self, id, name, position, dim=None,  model='models/sphere'):
        '''
        Constructor
        '''
        self.id = id
        self.name = name
        self.position = position
        self.model = model
        if dim:
            self.dim = dim

    def duplicate_name(self):
        '''
        Change name in response to multiple obj of same name
        '''
        num_re = re.compile(r"[1-9]$")
        num_match = num_re.search(self.name)
        if num_match:
            num_match_value = int(num_match.group())
            self.name = self.name[:-1] + str(num_match_value + 1)
        else:
            self.name = self.name + '2'
        return self.name

        
