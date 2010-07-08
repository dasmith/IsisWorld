
from pandac.PandaModules import Vec3
from visual import *
from spatial import *
from functional import *
from isisobject import IsisObject


class table(IsisObject,IsisVisual,Container,IsisFunctional):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="table/table",scale=0.006)
        Container.__init__(self,density=4000)


class knife(IsisObject, IsisVisual, IsisSpatial, Sharp):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="knife", scale=0.01)
        IsisSpatial.__init__(self, density=25)


class toaster(IsisObject, IsisVisual, Container, IsisFunctional):
    
    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="toaster", scale=0.7)
        Container.__init__(self, density=100)
        IsisFunctional.__init__(self)

        # register functional states
        self.registerState("containsToast", [0,1,2])

class bread(IsisObject, IsisVisual, Container, IsisFunctional):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="slice_of_bread", scale=0.5)
        Container.__init__(self, density=100)

class loaf(IsisObject, IsisVisual, IsisSpatial, Dividable):

    def __init__(self,name,physics):
        IsisObject.__init__(self,name=name,physics=physics)
        IsisVisual.__init__(self,model="loaf_of_bread", scale=0.3)
        IsisSpatial.__init__(self, density=1000)
