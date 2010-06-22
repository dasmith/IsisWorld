# -*- coding: UTF-8 -*-

# Copyright (c) 2009, Piotr Podgórski
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
#       in the documentation and/or other materials provided with the distribution.
#    3. Neither the name of the Author nor the names of other contributors may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from physics import *
from direct.interval.IntervalGlobal import *

"""
This is a class that can be used to make kinematic door.
Typpically if you need character controll in your game, you'll also need
some kind of door.
"""
class door():
    def __init__(self, worldManager, model):
        self.state = "close"
        self.speed = 0.5
        
        self.worldManager = worldManager
        
        self.doorNP = model
        
        """
        Here we store the initial hpr of the door so that they can close
        back to the original position.
        """
        self.hpr = self.doorNP.getHpr()
        
        self.doorGeomData = OdeTriMeshData(self.doorNP, True)
        self.doorGeom = OdeTriMeshGeom(self.worldManager.space, self.doorGeomData)
        self.doorGeom.setPosition(self.doorNP.getPos(render))
        self.doorGeom.setQuaternion(self.doorNP.getQuat(render))
        self.doorGeom.setCollideBits(FLOORMASK)
        
        self.doorData = odeGeomData()
        self.doorData.name = "door"
        self.doorData.surfaceFriction = 15.0
        self.doorData.selectionCallback = self.select
        
        self.worldManager.setGeomData(self.doorGeom, self.doorData, self, True)
        
    def select(self, character=None, direction=0):
        if self.state == "close":
            self.open(self.doorNP.getQuat(render).xform(direction).getY())
        elif self.state == "open":
            self.close()
        
    def close(self):
        """
        Here we use the Panda Sequence and Interval to close the door.
        Notice the transitional state *ing during the sequence.
        Without it it would be possible to start opening/closing
        the door during animation.
        """
        closeInterval = LerpHprInterval(self.doorNP, self.speed, self.hpr)
        Sequence(
            Func(self.changeState, "closing"),
            closeInterval,
            Func(self.changeState, "close"),
        ).start()
        
    def open(self, dir):
        """
        The direction is here to make sure the door opens from the character
        instead of to it. This might be a little unrealistic (typpically door
        open one way), but it tends to give better results.
        """
        if dir > 0:
            newH = -85.0
        else:
            newH = 85.0
        
        """
        Calculate the new heading for the door.
        """
        newH += self.doorNP.getH()
        
        """
        And run the sequence to close it.
        """
        Sequence(
            Func(self.changeState, "opening"),
            LerpHprInterval(self.doorNP, self.speed, Vec3(newH, 0, 0)),
            Func(self.changeState, "open"),
        ).start()
        
    def changeState(self, newState):
        self.state = newState
    
    def update(self, timeStep):
        """
        Here we update the position of the OdeGeom to follow the
        animated Panda Node. This method is what makes our object
        a kinematic one.
        """
        quat = self.doorNP.getQuat(render)
        pos = self.doorNP.getPos(render)
        
        self.doorGeom.setPosition(pos)
        self.doorGeom.setQuaternion(quat)
