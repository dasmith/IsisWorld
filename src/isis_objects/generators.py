
from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject

world_objects = {}

def addToWorld(object):
    world_objects[object.name] = object

class table(IsisObject,IsisVisual,Container,Surface,IsisFunctional):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="table/table",scale=0.006)
        self.create()

        Container.__init__(self,density=4000)
        Container.setup(self)
        Surface.__init__(self, density=4000)
        Surface.setup(self)

        IsisFunctional.__init__(self)

        addToWorld(self)


class knife(IsisObject, IsisVisual, IsisSpatial, Sharp):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="knife", scale=0.01)
        self.create()

        IsisSpatial.__init__(self, density=25)
        IsisSpatial.setup(self)

        Sharp.__init__(self)

        addToWorld(self)


class toaster(IsisObject, IsisVisual, Container, IsisFunctional):
    
    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics,offsetVec=(1,0.4,0))
        IsisVisual.__init__(self,model="toaster", scale=0.7)
        self.create()

        Container.__init__(self, density=100)
        Container.setup(self)

        IsisFunctional.__init__(self)
        # register functional states
        self.registerState("containsToast", [0,1,2])

        addToWorld(self)

class bread(IsisObject, IsisVisual, Container, IsisFunctional):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="slice_of_bread", scale=0.5)
        self.create()

        Container.__init__(self, density=100)
        Container.setup(self)

        IsisFunctional.__init__(self)

        addToWorld(self)

class loaf(IsisObject, IsisVisual, IsisSpatial, Dividable):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="loaf_of_bread", scale=0.3)
        self.create()

        IsisSpatial.__init__(self, density=1000)
        IsisSpatial.setup(self)

        Dividable.__init__(self, bread)

        addToWorld(self)