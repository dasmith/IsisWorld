'''
Created on Jan 19, 2010 

@author: glebk

xmlrpc server for interfacing with homesim
* NOTE DOESN'T HANDLE MULTIPLE CLIENTS YET

'''
import sys
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
# override Python's file operations with Panda's thread-safe file ops
from direct.stdpy import threading
from direct.stdpy.file import *
import SocketServer

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class XMLRPCServer(SocketServer.ThreadingMixIn,SimpleXMLRPCServer):
    def __init__(self):
        SimpleXMLRPCServer.__init__(self, ("", 8001), requestHandler=RequestHandler)
        self.register_introspection_functions()
        self.register_function(self.print_command)
        # allow the server to be turned off
        self.closed = False
    
    def start_serving(self, task):
        self.socket.setblocking(0)
        #while not self.closed:
        self.handle_request()
        
        # cooprative thread, allow Panda's main thread to run
        # consisder Yield causes signal.signal(signal.SIGINT, signal.default_int_handler)  error.
        # so force it instead
        #threading.Thread.forceYield()
        return task.cont

    def print_command(self, command):
        """ Test method to see if we can print to panda3d thread output """
        print command
        return 'printed command'


    def stop(self):
        self.closed = True
        return 'Done!'
