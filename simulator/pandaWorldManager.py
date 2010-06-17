
from pandac.PandaModules import *
# initialize collision mask constants
FLOORMASK = BitMask32.bit(0)        
WALLMASK = BitMask32.bit(1)
PICKMASK = BitMask32.bit(2)
AGENTMASK = BitMask32.bit(3)


class PhysicsCharacterController(object):
    
    def __init__(self, worldManager):
        # make sure parent node is off
        import random
        self.rootNode.setCollideMask(BitMask32.allOff())
        x= random.randint(0,10)
        y= random.randint(0,10)
        z= random.randint(0,10)
        self.actor.setPos(x,y,z)
        self.avatarRadius = 0.8        
        offsetNodeOne = [x,0+y,0.5+z,0.5]
        offsetNodeTwo = [x,0+y,1.6+z,0.5]
        # collision tubes have not been written as good FROM collidemasks
        # to make the person tall, but not wide we use three collisionspheres
        centerHeight = 1
        self.avatarViscosity = 0
        self.cNode = CollisionNode('collisionNode')
        self.cNode.addSolid(CollisionSphere(0.0, 0.0, centerHeight, self.avatarRadius))
        self.cNode.addSolid(CollisionSphere(0.0, 0.0, centerHeight + 2*self.avatarRadius, self.avatarRadius))
        self.cNode.setFromCollideMask(BitMask32.allOn())
        self.cNode.setIntoCollideMask(BitMask32.allOff()|AGENTMASK)
        self.cNode.setTag('agent','agent')
        self.cNodePath = self.actor.attachNewNode(self.cNode)
        self.cNodePath.show()
        self.priorParent, self.actorNodePath, self.acForce = worldManager.addActorPhysics(self)

def getorientedboundingbox(collobj):
    ''' get the oriented bounding box '''
    # save object's parent and transformation
    parent=collobj.getparent()
    trans=collobj.gettransform()
    # ode need everything in world's coordinate space,
    # so bring the object directly under render, but keep the transformation
    collobj.wrtreparentto(render)
    # get the tight bounds before any rotation
    collobj.sethpr(0,0,0)
    bounds=collobj.gettightbounds()
    # bring object to it's parent and restore it's transformation
    collobj.reparentto(parent)
    collobj.settransform(trans)
    # (max - min) bounds
    box=bounds[1]-bounds[0]
    return [box[0],box[1],box[2]]


def getCapsuleSize(collobj,radius=1):
    bounds=collobj.getTightBounds()
    # (max - min) bounds
    return [bounds[0][0],bounds[0][1],bounds[0][2],bounds[1][0],bounds[1][1],bounds[1][2],radius]

class PhysicsWorldManager():
    
    def __init__(self):
        """Setup the collision pushers, handler, and traverser"""
        # cTrav is in charage to drive collisions
        base.cTrav = CollisionTraverser('Collision Traverser')
        # panda's physics system is attached to particle system
        base.enableParticles()
        # allows detection of fast moving objects
        base.cTrav.setRespectPrevTransform(True)
        base.cPush = PhysicsCollisionHandler()
        base.cPush.setStaticFrictionCoef(1)
        base.cPush.setDynamicFrictionCoef(1.0)
    
        #base.cEvent = CollisionHandlerEvent()
        # instantiate an angular integrator, which is required
        # in order to add angular velocity forces

        base.physicsMgr.attachLinearIntegrator(LinearEulerIntegrator())
        base.physicsMgr.attachAngularIntegrator(AngularEulerIntegrator())
        # init gravity force
        self.gravityFN = ForceNode('gravity-force')
        self.gravityFNP = base.render.attachNewNode(self.gravityFN)
        # drag down in Z axis -9.81 units/second
        self.gravityForce = LinearVectorForce(0,0,-9.81)
        self.gravityFN.addForce(self.gravityForce)
        # attach gravity to global physics manager, which
        # is defined automatically by base.enableParticles()
        base.physicsMgr.addLinearForce(self.gravityForce)
        # look for agent-on-agent collisions
        #base.cEvent.addInPattern("a2a%(""agent"")fh%(""agent"")ih")
        #base.cEvent.addInPattern("%(agent)ft-into-%(agent)it")
        #base.accept("a2a",self.handleAgentOnAgentCollision)
        
        base.cPush.setInPattern("enter%in")
        base.cPush.setOutPattern("enter%in")

        # see this website for a description of the patterns
        # https://www.panda3d.org/wiki/index.php/Collision_Handlers

    def handleAgentOnAgentCollision(self,entry):
        print "Collision! between two agents"
        print entry

    def handleAllCollisions(self,entry):
        """ Entries have information
https://www.panda3d.org/wiki/index.php/Collision_Entries

        """
        print entry

    def addActorPhysics(self,actor):
        # ActorNode tracks physical interactions and applies
        # them to a model.  It keeps track of the elapsed times
        # in framerates
        import random
        actorNode = ActorNode("%s-physicsActorNode" % actor.name)
        actorNode.getPhysicsObject().setOriented(1)
        actorNode.getPhysicsObject().setMass(200)
        actorNode.getPhysical(0).setViscosity(0.1)
        actorNodePath = NodePath(actorNode)#PandaNode("%s-physicsNode" % actor.name))
        
        actor.actor.reparentTo(actorNodePath)
        actor.actor.assign(actorNodePath)
        actorNodePath.reparentTo(actor.rootNode)
        #actorNodePath.reparentTo(actor.rootNode)
        #actorNodePath.assign(actor.rootNode)

        # TODO: find out the meaning of this
        fn = ForceNode("priorParent")
        fnp = NodePath(fn)
        fnp.reparentTo(render)
        priorParent = LinearVectorForce(0.0, 0.0, 0)
        fn.addForce(priorParent)
        base.physicsMgr.addLinearForce(priorParent)
        #actor.priorParentNp = fnp
        #actor.priorParent = priorParent

        fn = ForceNode("viscosity")
        fnp = NodePath(fn)
        fnp.reparentTo(render)
        actor.avatarViscosity = LinearFrictionForce(0.0, 1.0, 0)
        fn.addForce(actor.avatarViscosity)
        base.physicsMgr.addLinearForce(actor.avatarViscosity)
        base.physicsMgr.attachLinearIntegrator(LinearEulerIntegrator())
        base.physicsMgr.attachPhysicalNode(actorNodePath.node())

        actuatorForce = LinearVectorForce(0.0, 0.0, 0.0)
        fn = ForceNode("actorControls")
        fnp = NodePath(fn)
        fnp.reparentTo(render)
        fn.addForce(actuatorForce)
        base.physicsMgr.addLinearForce(actuatorForce)
       
        # attach ralph to world
        #base.physicsMgr.attachPhysicalNode(charAN)
        # attach collision node with actor node to it


        base.cPush.addCollider(actor.cNodePath, actor.actor)
        # add collider to global traverser
        base.cTrav.addCollider(actor.cNodePath, base.cPush)
        #base.cTrav.addCollider(cNode, base.cEvent)
        #base.cTrav.addCollider(cNode, base.cEvent)

        return priorParent,actorNodePath,actuatorForce


    def addSphereInWorld(self, obj, show=False):
        # Get the size of the object for the collision sphere.
        bounds = obj.getChild(0).getBounds()
        center = bounds.getCenter()
        radius = bounds.getRadius()

        # Create a collision sphere and name it something understandable.
        collSphereStr = 'CollisionHull' + str(self.collCount) + "_" + obj.getName()
        self.collCount += 1
        cNode = CollisionNode(collSphereStr)
        cNode.addSolid(CollisionSphere(center, radius))

        cNodepath = obj.attachNewNode(cNode)
        if show:
            cNodepath.show()

        # Return a tuple with the collision node and its corrsponding string so
        # that the bitmask can be set.
        return (cNodepath, collSphereStr)

    def addObjectInWorld(nodePath,shape):
        if self.disable: return
        collider = nodePath.attachNewNode(CollisionNode(nodePath.name+"-collider"))
        boundingBox=getOrientedBoundingBox(collObj)
        if shape=='sphere':
            radius=.5*max(*boundingBox)
            posVec = nodePath.getPos() + radus
            geom = CollisionSphere(posVec)
            return geom

    def setupGround(self,groundNP):
        # Ground collision: represented as an infinite plane
        # any object below the plane, no matter how far, is
        # considered to be intersecting the plane.
        #
        # Constructed with Panda3D plane object, one way to
        # do this is with a point and a normal
        #cp = CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0)))
        #planeNP = base.render.attachNewNode(CollisionNode('groundcnode'))
        #planeNP.node().addSolid(cp)
        #planeNP.show()
        groundNP.node().setIntoCollideMask(FLOORMASK)

    def doPhysics(self,dt):
        base.physicsMgr.doPhysics(dt)

    def startPhysics(self):
        # everything is done in the __init__ method
        # for Panda's physics
        pass
