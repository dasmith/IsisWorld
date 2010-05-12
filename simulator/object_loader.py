"""  Object Loader for IsisWorld Simulator """
from odeWorldManager import *
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat
from random import randint, random
import sys, re, time


class IsisObject(DirectObject):
    
    def  __init__(self, worldManager, activeModel, models, states=[], density=2000):
        self.state = "close"
        self.speed = 15

        self.worldManager = worldManager
        
        self.models = models
        
        self.NP = activeModel
        self.InitialHpr = self.NP.getHpr()
        
        # set up physical body
        boundingBox, offset = getOBB(self.NP)

        M = OdeMass()
        # water has density of 1000 (kg/m^3)
        # copper between 8920 and 8960 
        # 11340 is lead
        M.setBox(density, *boundingBox) # density should be density
        
        self.body = OdeBody(worldManager.world)
        self.body.setMass(M)
        self.body.setPosition(self.NP.getPos(render))
        self.body.setQuaternion(self.NP.getQuat(render))
        # Create a BoxGeom
        self.geom = OdeBoxGeom(self.worldManager.space,*boundingBox)
        self.geom.setCollideBits(BitMask32(0x00000002))
        self.geom.setCategoryBits(BitMask32(0x00000001))
        #groundGeom.setCollideBits(BitMask32(0x00000021))
        #groundGeom.setCategoryBits(BitMask32(0x00000012))
        self.geom.setBody(self.body)
    
        self.data = odeGeomData()
        self.data.name = self.NP.getName()
        self.data.surfaceFriction = 15.0
        self.data.selectionCallback = self.select

        self.worldManager.setGeomData(self.geom, self.data, self, True)
        #if self.data.name == "knife": self.NP.place()
        
        
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
        self.NP.setPosQuat(render, self.body.getPosition(), Quat(self.body.getQuaternion()))



class IsisObjectGenerator():
   # yaml_tag = u'!IsisObjectGenerator'
    def __init__(self, name, models, posHpr=(0,0,0,0,0,0), states = [], scale=1, density=1):
        """ This defines a generator object from which instances are derived."""
        self.name = name
        self.posHpr = posHpr # default position and orientation
        self.states = states 
        self.models = models 
        self.scale = scale
        self.density = density
   
    def generate_instance(self, worldManager, renderParent, options={}):
        """ Generates a new object and adds it to the world"""
        # TODO, check to see if name exists.
        active_model = loader.loadModel(self.models['default']) 
        active_model.setName(self.name)
        active_model.reparentTo(renderParent) 
        active_model.setScale(self.scale)
        active_model.setPosHpr(renderParent,*self.posHpr)
        active_model.flattenStrong()
        
        new_obj = IsisObject(worldManager, active_model, self.models, self.states, self.density)
        return new_obj

    def __repr__(self):
        return "%s(name=%r, posHpr=%r, states=%r, models=%r, scale=%r, density=%r)" % (self.__class__.__name__, self.name, self.posHpr, self.states, self.models, self.scale, self.density)


def load_objects_file():
    return map(lambda x: x.strip(), open('kitchen.isis','r').readlines())
    

def load_objects_in_world(worldManager, renderParent, otherItems):
    # add each object to the world
    world_generator_instructions = load_objects_file()
    generators = load_object_generators()
    world_objects = {}
    
    for instruction in world_generator_instructions:
        item = instruction.split("\t")[0]
        if len(instruction.split("\t")) > 1:
            itemRenderParent = renderParent
            for option in instruction.split("\t")[1:]:
                key,val = option.split(" ")
                if key == "on":
                    itemRenderParent = otherItems[val]
            if generators.has_key(item):
                mobj = generators[item].generate_instance(worldManager,renderParent)
                world_objects[item] = mobj
                print "Creating object %s" % (item) 
            else:
                print "No default model for object %s" % (item)
    return world_objects    

"""    Material	Density (kg/m^3)
    Balsa wood	120
    Brick	2000
    Copper	8900
    Cork	250
    Diamond	3300
    Glass	2500
    Gold	19300
    Iron	7900
    Lead	11300
    Styrofoam	100
"""
def load_object_generators():
    generators = {'knife': IsisObjectGenerator('knife', models={'default':'models3/knife'}, posHpr=(-1.0, 3.1, 0, 0, 0, 0), scale=0.01,density=10000),
    'toaster': IsisObjectGenerator('toaster',models={'default': 'models/kitchen_models/toaster','with_bread': 'models/kitchen_models/toaster_with_bread'}, posHpr=(4.5,3.1,0,260,0,0), scale=0.7, density=5000),
    'bread': IsisObjectGenerator('slice_of_bread',models={'default': 'models/kitchen_models/slice_of_bread'},scale=0.5,posHpr=(3,1,3.1,0,0,0), density=1000),
    'loaf': IsisObjectGenerator('loaf',models={'default': 'models/kitchen_models/loaf_of_bread'},scale=0.3,posHpr=(4,1,0,0,0,0), density=1000) }
    return generators


def load_generators_from_yaml():
    import yaml
    try:
        objects = yaml.load_all(open('commonsense/object_generators.yaml','r'))
    except:
        print "Cannot open 'objects.yml' file."
    return objects

def dump_generators_to_yaml():
    import yaml
    of = open('commonsense/object_generators.yaml','w')
    objects = load_object_generators()
    yaml.dump_all(objects,of, explicit_start=True)

if __name__ == "__main__":
    # define the original objects
    dump_generators_to_yaml()
    
    
        
# Methods to Place Objects in World 
