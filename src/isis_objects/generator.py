from isisobject import IsisObject
from pandac.PandaModules import Vec3
# Object generators used to instantiate various objects

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
