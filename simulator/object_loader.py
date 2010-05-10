"""  Object Loader for IsisWorld Simulator """
from odeWorldManager import *
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat
from random import randint, random
import sys, re, time

try:
    import yaml
except:
    print "YAML not installed"
    sys.exit()


class IsisObject(DirectObject):
    
    def  __init__(self, worldManager, activeModel, models, states=[], mass=1):
        self.state = "close"
        self.speed = 15

        self.worldManager = worldManager
        
        self.models = models
        
        self.NP = activeModel
        boundingBox, offset = getOBB(self.NP)
        self.InitialHpr = self.NP.getHpr()
        boxBody = OdeBody(worldManager.world)
        M = OdeMass()
        M.setBox(mass, *boundingBox) # mass should be density
        boxBody.setMass(M)
        boxBody.setPosition(self.NP.getPos(render))
        boxBody.setQuaternion(self.NP.getQuat(render))
        # Create a BoxGeom
        self.geom = OdeBoxGeom(self.worldManager.space,*boundingBox)
        self.geom.setCollideBits(BitMask32(0x00000002))
        self.geom.setCategoryBits(BitMask32(0x00000001))
        self.geom.setBody(boxBody)
    
        self.data = odeGeomData()
        self.data.name = self.NP.getName()
        self.data.surfaceFriction = 15.0
        self.data.selectionCallback = self.select

        self.worldManager.setGeomData(self.geom, self.data, self, False)
        #if self.data.name == "knife": self.NP.place()
        
    def setPosQuat(self,x,a,b):
        return self.NP.setPosQuat(a,b)
        
    def select(self, character, direction):
        if self.state == "close":
            self.open(self.NP.getQuat(render).xform(direction).getY())
        elif self.state == "open":
            self.close()

    def close(self):
        """
        Here we use the Panda Sequence and Interval to close the door.
        Notice the transitional state *ing during the sequence.
        Without it it would be possible to start opening/closing
        the door during animation.
        """
        #closeInterval = LerpHprInterval(self.doorNP, self.speed, self.hpr)
        #Sequence(
        #        Func(self.changeState, "closing"),
        #        closeInterval,
        #        Func(self.changeState, "close"),
        #).start()

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
        #newH += self.doorNP.getH()

        """
        And run the sequence to close it.
        """
        #Sequence(
        #        Func(self.changeState, "opening"),
        #        LerpHprInterval(self.doorNP, self.speed, Vec3(newH, 0, 0)),
        #        Func(self.changeState, "open"),
        #).start()

    def changeState(self, newState):
        self.state = newState

    def update(self, timeStep):
        """
        Here we update the position of the OdeGeom to follow the
        animated Panda Node. This method is what makes our object
        a kinematic one.
        """
        #print "Called update for", self.data.name
        quat = self.NP.getQuat(render)
        pos = self.NP.getPos(render)

        self.geom.setPosition(pos)
        self.geom.setQuaternion(quat)



class IsisObjectGenerator(yaml.YAMLObject):
    yaml_tag = u'!IsisObjectGenerator'
    def __init__(self, name, models, posHpr=(0,0,0,0,0,0), states = [], scale=1, mass=1):
        """ This defines a generator object from which instances are derived."""
        self.name = name
        self.posHpr = posHpr # default position and orientation
        self.states = states 
        self.models = models 
        self.scale = scale
        self.mass = mass
   
    def generate_instance(self, worldManager, renderParent, options={}):
        """ Generates a new object and adds it to the world"""
        # TODO, check to see if name exists.
        active_model = loader.loadModel(self.models['default']) 
        active_model.setName(self.name)
        active_model.reparentTo(renderParent) 
        active_model.setScale(self.scale)
        active_model.setPosHpr(*self.posHpr)
        
        new_obj = IsisObject(worldManager, active_model, self.models, self.states, self.mass)
        return new_obj

    def __repr__(self):
        return "%s(name=%r, posHpr=%r, states=%r, models=%r, scale=%r, mass=%r)" % (self.__class__.__name__, self.name, self.posHpr, self.states, self.models, self.scale, self.mass)


def load_objects_file():
    try:
        objects = yaml.load_all(open('objects.yaml','r'))
    except:
        print "Cannot open 'objects.yml' file."
    return objects
    #return (IsisObject(*o) for o in objects)

def load_objects_in_world(worldManager, renderParent):
    # add each object to the world
    iobjects = load_objects_file()
    world_objects = []
    
    for iobj in sorted(iobjects,key=lambda x: x.mass, reverse=True):
        # TODO: ensure name is unique
        if iobj.models.has_key('default'):
            mobj = iobj.generate_instance(worldManager, renderParent)
            world_objects.append(mobj)
            print "Creating object %s" % (iobj.name) 
        else:
            print "No default model for object %s" % (iobj.name)
    return world_objects    
    
def generate_object_file():
    knife = IsisObjectGenerator('knife', models={'default':'models/kitchen_models/knife'}, posHpr=(-1.0, 3.1, 3, 0, 0, 0), scale=0.01,mass=1)
    toaster = IsisObjectGenerator('toaster',models={'default': 'models/kitchen_models/toaster','with_bread': 'models/kitchen_models/toaster_with_bread'}, posHpr=(4.5,1,3,260,0,0), scale=0.7, mass=3)
    bread = IsisObjectGenerator('slice_of_bread',models={'default': 'models/kitchen_models/slice_of_bread'},scale=0.7,posHpr=(3,1,0,0,0,0), mass=0.8)
    counter = IsisObjectGenerator('counter',models={'default': 'models/kitchen_models/counter'}, posHpr=(2, 1.8, -2.5, 180, 0, 0), scale=0.6, mass=200000)
    objects = [counter,knife,toaster,bread]
    # create and save YAML file
    of = open('objects.yaml','w')
    yaml.dump_all(objects,of, explicit_start=True)
    
    #new_object = Visual_Object(0, 'toaster_with_bread', posHpr, model='models/kitchen_models/toaster_with_bread')
    #new_object = Visual_Object(0, 'loaf_of_bread', posHpr, model='models/kitchen_models/loaf_of_bread')
   


if __name__ == "__main__":
    # define the original objects
    generate_object_file()
    objects = load_objects_file()
    
    
        
# Methods to Place Objects in World 
