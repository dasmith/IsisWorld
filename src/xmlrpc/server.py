'''
Created on Jan 19, 2010 

@author: glebk

xmlrpc server for interfacing with homesim
* NOTE DOESN\'T HANDLE MULTIPLE CLIENTS YET

'''
# System Imports
import sys

### Server Related Impots ###
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

class XMLRPCServer(object):

    def print_command(self, command):
        """ Test method to see if we can print to panda3d thread output """
        print command
        return 'printed command'

#    def shutdown(self):
#        """ TODO Doesn't really work but will need a means of shutting it down """
#        self.kill = 1
#        return 'Done!'

    def __init__(self):
        self.server = SimpleXMLRPCServer(("", 8001), requestHandler=RequestHandler)
        self.server.register_introspection_functions()
        self.server.register_function(self.print_command)
