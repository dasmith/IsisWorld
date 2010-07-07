from isisobject import IsisObject, Dividable, SharpObject
from pandac.PandaModules import Vec3
# Object generators used to instantiate various objects

class ContainerGenerator():

    def __init__(self):
        self.containerItems = []

    def enterContainer(self,fromObj,toObject):
        assert toObject == self, "Error: cannot put into self"
        if fromObj not in self.containerItems:
            self.containerItems.append(fromObj)

    def leaveContainer(self,fromObj,toObject):
        assert toObject == self, "Error: cannot remove from another container"
        if fromObj in self.containerItems:
            self.containerItems.remove(toObject)

    def isEmpty(self):
        return len(self.containerItems) == 0



class IsisObjectGenerator():
    def __init__(self, name, model, scale = 1, density = 200, offsets = Vec3(0, 0, 0)):
        """ This defines a generator object from which instances are derived."""
        self.name = name
        self.model = model
        self.scale = scale
        self.density = density
        #TODO: Automatically center models once they are loaded
        self.offsets = offsets
   
    def generate_instance(self, physicsManager=None, pos =Vec3(0, 0, 0), parent = None):
        """ Generates a new object and adds it to the world"""
        model = loader.loadModel(self.model)
        model.setScale(self.scale)
        # flatten strong causes problem with physics
        #model.flattenLight()

        # add item to Isisworld
        obj = IsisObject(self.name, model, self.density, physicsManager, initialPos=pos, offsetVec=self.offsets)
        if parent:
            obj.reparentTo(parent)
        #obj.update()

        return obj

class DividableGenerator(IsisObjectGenerator):
    def __init__(self, name, model, piece, scale = 1, density = 200, offsets = Vec3(0, 0, 0)):
        """ Defines dividable objects which return pieces of themselves """
        IsisObjectGenerator.__init__(self, name, model, scale, density, offsets)
        self.piece = piece

    def generate_instance(self, physicsManager=None, pos = Vec3(0, 0, 0), parent = None):
        """ Generate a new object and adds it to the world"""
        model = loader.loadModel(self.model)
        model.setScale(self.scale)

        obj = Dividable(self.name, model, self.density, self.piece, physicsManager, pos, self.offsets)
        if parent:
            obj.repartenTo(parent)

        return obj

class SharpGenerator(IsisObjectGenerator):
    def __init__(self, name, model, scale = 1, density = 200, offsets = Vec3(0, 0, 0)):
        IsisObjectGenerator.__init__(self, name, model, scale, density, offsets)
   
    def generate_instance(self, physicsManager=None, pos =Vec3(0, 0, 0), parent = None):
        """ Generates a new object and adds it to the world"""
        model = loader.loadModel(self.model)
        model.setScale(self.scale)

        obj = SharpObject(self.name, model, self.density, physicsManager, initialPos=pos, offsetVec=self.offsets)
        if parent:
            obj.reparentTo(parent)

        return obj
