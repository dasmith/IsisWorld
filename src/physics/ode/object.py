import utils
from pandac.PandaModules import NodePath, Vec3, Quat, BitMask32
from pandac.PandaModules import OdeBody, OdeMass, OdeSphereGeom, OdeBoxGeom, OdePlaneGeom, OdeCylinderGeom, OdeCappedCylinderGeom, OdeTriMeshGeom, OdeTriMeshData
from pandac.PandaModules import CollisionNode, CollisionSphere
from ODEWireGeom import *


class PhysicsObjectController():
    
    def __init__(self,world,density,geomType="box", dynamic=True):
        print "Initializing ODE Base for an %s object" % (geomType)
        self.model.flattenLight()
        # set up the appropriate ODE Geometry 
        self.isEnabled = False
        offset = Vec3(0.0)
        self.geom = None 
        if geomType == 'mesh':
            # You don't want to use this all of the time because
            # of the high computational cost
            self.geom = OdeTriMeshGeom(world.space, OdeTriMeshData(self.model,True))
        elif geomType == 'sphere':
            # calculate radius
            boundingBox, offset = utils.getOrientedBoundingBox(self.model)
            radius =  boundingBox[0]/2.0
            self.geom =  OdeSphereGeom(world.space, radius)
        elif geomType == 'box':
            boundingBox, offset = utils.getOrientedBoundingBox(self.model)
            self.offsetVec = Vec3(*offset)
            self.geom = OdeBoxGeom(world.space, *boundingBox)
            boxNP = wireGeom().generate('box', extents=boundingBox)
            boxNP.reparentTo(render) 
        elif geomType == 'cylinder':
            # calculate radius and height
            boundingBox, offset = utils.getOrientedBoundingBox(self.model)
            radius =  boundingBox[0]/2.0
            low, high = self.model.getTightBounds()
            height = high[0]-low[0]
            self.geom = OdeCylinderGeom(world.space, radius, height)
        else:
            raise Exception("Undefined geomType = %s" % (geomType))
       
        self.geom.setCollideBits(BitMask32.bit(1))
        self.geom.setCategoryBits(BitMask32.bit(1))
        
        # TODO: surface entires should be more user friendly (break into system of geomTypes)
        world.space.setSurfaceType(self.geom, 2)
        
        self.density = 10000
        if dynamic:
            # if the density is defined, make this a dynamic object by defining its Body
            self.body = OdeBody(world.world)
            mass = OdeMass()
            if geomType == 'mesh':
                low, high = self.model.getTightBounds()
                mass.setBoxTotal(self.density, high[0]-low[0], high[1]-low[1], high[2]-low[2])
            elif geomType == 'sphere':
                mass.setSphereTotal(self.density, radius)
            elif geomType == 'box':
                mass.setBoxTotal(self.density, *boundingBox)
            elif geomType == 'cylinder':
                mass.setCapsuleTotal(self.density, 3, radius, height)
            else:
                raise Exception("Undefined geomType = %s" % (geomType)) 
            self.body.setPosition(self.model.getPos(render))
            self.body.setQuaternion(self.model.getQuat(render))
            self.mass = mass.getMagnitude() 
            self.body.setMass(mass)
            self.geom.setBody(self.body)
            self.body.setTorque(0,0,0)
            self.setAngularVelocity(0.0)
            self.setLinearVelocity(0.0)
            self.body.setForce(0.0)
            # acknowledge offset
            #if offset != Vec3(0):
            #    self.geom.setOffsetPosition(*offset)
            # initialize position of geometry
            if hasattr(self.body, 'setData'):
                print "setting data for body of %s" % (geomType)
                self.body.setData(self.model)
        # register item in world
        world.addObject(self)

    def isDynamic(self):
        return hasattr(self,'body')

    def destroy(self):
        if hasattr(self,'body'):
            self.body.destroy()
        self.geom.getSpace().remove(self.geom)
        self.geom.destroy()
        # TODO: deleteModel()?

    def setPosition(self, pos):
        self.geom.setPosition(pos+self.offsetVec)
        self.model.setPos(pos+self.offsetVec)

    def getPosition(self):
        return self.geom.getPosition()

    def setRotation(self, hpr):
        # only for dynamic entities
        self.model.setHpr(hpr)
        self.geom.setQuaternion(self.node.getQuat(render))
   
    def handleCollision(self, entry, geom1, geom2):
        self.isEnabled = True
        #print "enabling", self.name

    def getRotation(self):
        return self.node.getHpr()

    def setLinearVelocity(self, vel):
        self.body.setLinearVelocity(vel)

    def getLinearVelocity(self):
        return self.body.getLinearVel()

    def setAngularVelocity(self, vel):
        self.body.setAngularVel(vel)

    def getAngularVelocity(self):
        return self.body.getAngularVel()

    def addTorque(self, torque):
        self.body.addTorque(torque.getX(), torque.getY(), torque.getZ())

    def getTorque(self):
        return self.body.getTorque()

    def addForceAtPosition(self, direction, pos):
        self.body.addForceAtPos(direction.getX(), direction.getY(), direction.getZ(), pos.getX(), pos.getY(), pos.getZ())

    def update(self, timeStep=1):
        """ This method is called at each physics step by the Physics Controller
        whenever the object is added as a Kinematic, rather than Dynamic, object"""
        if self.isEnabled and self.getNetTag('heldBy') == '':
            # only enable the object to have physics when the object is not held
            #print self.getNetTag('heldBy')
            #print "Updating %s" % self.name
            #print self.body.getPosition(), self.geom.getPosition(), self.model.getPos()
            #self.model.setPosQuat(render, self.body.getPosition(), Quat(self.body.getQuaternion()))
            self.model.setPosQuat(render, self.geom.getPosition(), Quat(self.geom.getQuaternion()))
