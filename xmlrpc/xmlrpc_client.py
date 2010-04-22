'''
Opens connection to local xmlrpc server

Created Jan 23, 2010
By Gleb Kuznetsov (glebk@mit.edu)

INSTRUCTIONS:
For now the server provides a single function 'do'
which takes a single parameter text_command which is
a string of parameters with a single blank space
as the delimeter.

COMMAND LIST
* Adding an object to the world:
    s.do('object add object_name obj_x obj_y obj_z model=None')
ex: s.do('object add box 5 5 0')
returns:  name handle (i.e. 'box' or 'box1' if 'box already existed)

* Removing an object from the world:
    s.do('object remove object_name')
ex: s.do('object remove box') where box is object's name handle

* Move the agent to a target
    s.do('action move target target_name')
ex: s.do('action move target toast')

* Move the agent to a position
    s.do('action move position x y z')
ex: s.do('action move position 10 0 0')
'''

import xmlrpclib

s = xmlrpclib.ServerProxy('http://localhost:8001')





