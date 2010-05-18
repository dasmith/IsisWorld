
from pandac.PandaModules import OdeWorld,  OdeUtil, OdeSurfaceParameters, OdeJointGroup, OdeTriMeshData,OdeTriMeshGeom, OdeHashSpace, OdeBody, OdeMass, OdeBoxGeom, OdeCappedCylinderGeom, OdeRayGeom
from pandac.PandaModules import BitMask32, Vec3, Vec4, Quat, OdeContact,OdeContactJoint, OdeSphereGeom, OdePlaneGeom, GeomVertexReader
from pandac.PandaModules import GeomVertexFormat, GeomVertexData,Geom
from pandac.PandaModules import *
import random
from direct.showbase import PythonUtil as PU
from direct.showbase.InputStateGlobal import inputState

class ODEobject:
    ''' the base class of ODE boxes, spheres, capsules, and TriMeshes used here
    '''
    def storeProps(self, pythonObject, density, surfaceFriction, noColl_ID=None):

        """
        Any object can be handled as an Area Trigger,
        but for real Area Trigger functionality
        you need the odeTrigger class.

        This isTrigger setting just tells the collision handler
        whether to make an actual collision between this object
        and others or just execute it's callback.
        """
        self.isTrigger = False

        """
        The method to be called when a collision with the object
        that uses this Data occurs.
        """
        self.collisionCallback = None

        """
        This is used when the player attempts to use an object
        Of course objects are usable (clickable) only when
        this is not None.
        """
        self.selectionCallback = None

        """
        This is for general usage
        """
        self.pythonObject = pythonObject
        self.name = ""

        """
        And here we have the standard ODE stuff for collisions
        """
        self.surfaceFriction = surfaceFriction
        self.surfaceBounce = 0.01
        self.surfaceBounceVel = 0.0
        self.surfaceSoftERP = 0.0
        self.surfaceSoftCFM = 0.00001
        self.surfaceSlip = 0.0
        self.density=density
        # randomize geom's collision ID, if not supplied
        if noColl_ID==None:
           if pythonObject:
              noColl_ID=id(pythonObject)
           else:
              noColl_ID=random.random()*random.random()*1000
        self.noColl=noColl_ID

    def destroy(self):
        if hasattr(self,'body'):
           del self.body
        self.geom.getSpace().remove(self.geom)
        del self.geom
        if hasattr(self,'visualizer'):
           self.visualizer.removeNode()
        if self.pythonObject:
           self.pythonObject.removeNode()

    def getOBB(self,collObj):
        ''' get the Oriented Bounding Box '''
        # save object's parent and transformation
        parent=collObj.getParent()
        trans=collObj.getTransform()
        # ODE need everything in world's coordinate space,
        # so bring the object directly under render, but keep the transformation
        collObj.wrtReparentTo(render)
        # get the tight bounds before any rotation
        collObj.setHpr(0,0,0)
        bounds=collObj.getTightBounds()
        # bring object to it's parent and restore it's transformation
        collObj.reparentTo(parent)
        collObj.setTransform(trans)
        # (max - min) bounds
        box=bounds[1]-bounds[0]
        return [box[0],box[1],box[2]]


class ODEbox(ODEobject):
    ''' An easy setup for creating OdeBoxGeom (based on the tight bounding box),
        and it's body.

        If you have a geometry you'd like to use to define GeomBox size precisely,
        pass it as "collObj", or otherwise
        the "pythonObject" will be used to define GeomBox size.

        "noColl_ID" is an arbitrary number, use it when you need to build
        a larger collision structure from several geoms, which might overlap each other.
        Geoms with the same "noColl_ID" will NOT be tested for collision.
        In such case, don't pass your "pythonObject" to every geoms, or else
        your "pythonObject" transformation will be updated based on your every geoms.
        Pass it only when creating the main geom.
    '''
    def __init__(self, world, space, pythonObject=None, collObj=None,
                       density=0, surfaceFriction=0, noColl_ID=None):
        if pythonObject==None:
           obj=collObj
        else:
           obj=pythonObject
           if collObj==None:
              collObj=pythonObject

        boundingBox=self.getOBB(collObj)

        self.geom = OdeBoxGeom(space, *boundingBox)
        if density:  # create body if the object is dynamic, otherwise don't
           self.body = OdeBody(world)
           M = OdeMass()
           M.setBox(density, *boundingBox)
           self.body.setMass(M)
           self.geom.setBody(self.body)
        # synchronize ODE geom's transformation according to the real object's
        self.geom.setPosition(obj.getPos(render))
        self.geom.setQuaternion(obj.getQuat(render))
        # store object's properties
        self.storeProps(pythonObject, density, surfaceFriction, noColl_ID)


class ODEsphere(ODEobject):
    ''' An easy setup for creating ode.GeomSphere (based on the tight bounding box),
        and it's body.

        If you have a geometry you'd like to use to define GeomSphere size precisely,
        pass it as "collObj", or otherwise
        the "pythonObject" will be used to define GeomSphere size.

        "noColl_ID" is an arbitrary number, use it when you need to build
        a larger collision structure from several geoms, which might overlap each other.
        Geoms with the same "noColl_ID" will NOT be tested for collision.
        In such case, don't pass your "pythonObject" to every geoms, or else
        your "pythonObject" transformation will be updated based on your every geoms.
        Pass it only when creating the main geom.
    '''
    def __init__(self, world, space, pythonObject=None, collObj=None,
                       density=0, surfaceFriction=0, noColl_ID=None):
        if pythonObject==None:
           obj=collObj
        else:
           obj=pythonObject
           if collObj==None:
              collObj=pythonObject

        boundingBox=self.getOBB(collObj)
        radius=.5*max(*boundingBox)

        self.geom = OdeSphereGeom(space, radius)
        if density:  # create body if the object is dynamic, otherwise don't
           self.body = OdeBody(world)
           M = OdeMass()
           M.setSphere(density, radius)
           self.body.setMass(M)
           self.geom.setBody(self.body)
        # synchronize ODE geom's transformation according to the real object's
        self.geom.setPosition(obj.getPos(render))
        self.geom.setQuaternion(obj.getQuat(render))
        # store object's properties
        self.storeProps(pythonObject, density, surfaceFriction, noColl_ID)


class ODEcapsule(ODEobject):
    ''' An easy setup for creating ode.GeomCapsule (based on the tight bounding box),
        and it's body.

        If you have a geometry you'd like to use to define GeomCapsule size precisely,
        pass it as "collObj", or otherwise
        the "pythonObject" will be used to define GeomCapsule size.

        "noColl_ID" is an arbitrary number, use it when you need to build
        a larger collision structure from several geoms, which might overlap each other.
        Geoms with the same "noColl_ID" will NOT be tested for collision.
        In such case, don't pass your "pythonObject" to every geoms, or else
        your "pythonObject" transformation will be updated based on your every geoms.
        Pass it only when creating the main geom.
    '''
    def __init__(self, world, space, pythonObject=None, collObj=None,
                       density=0, surfaceFriction=0, noColl_ID=None):
        if pythonObject==None:
           obj=collObj
        else:
           obj=pythonObject
           if collObj==None:
              collObj=pythonObject

        boundingBox=self.getOBB(collObj)
        # capsule's radius is half of the smallest bound
        radius=.5*min(*boundingBox)
        # capsule's length is the largest bound and without the half sphere caps
        length=max(*boundingBox)-2.*radius
        # find which direction is the capsule's long axis (x=1, y=2, z=3)
        for b in range(len(boundingBox)):
            if boundingBox[b]==max(*boundingBox):
               longAxis=b+1
               break

        self.geom = OdeCappedCylinderGeom(space, radius, length)
        if density:  # create body if the object is dynamic, otherwise don't
           self.body = OdeBody(world)
           M = OdeMass()
           M.setCapsule(density, direction=longAxis, radius=radius, length=length)
           self.body.setMass(M)
           self.geom.setBody(self.body)
        # synchronize ODE geom's transformation according to the real object's
        self.geom.setPosition(obj.getPos(render))
        self.geom.setQuaternion(obj.getQuat(render))
        # store object's properties
        self.storeProps(pythonObject, density, surfaceFriction, noColl_ID)


class ODEtrimesh(ODEobject):
    ''' An easy setup for creating ode.GeomTriMesh and it's body.

        Pass any nodepath as "collObj", all geometries' polygons under that node will be sent to ODE,
        including the current transformation (position, rotation, scale), except shear.
        If not given, your "pythonObject" will be used.

        You can also set the object's mass density and surfaceFriction coefficient (mu),
        set density=0 to set the object as a static object, or
        setting it larger than 0 will automatically set the object as a dynamic one.
    '''
    def __init__(self, world, space, pythonObject, collObj=None, density=0, surfaceFriction=0, showCollObj=0, noColl_ID=None):
        if collObj==None:
           collObj=pythonObject
        # find any geomnode under the given node
        geomList=collObj.findAllMatches('**/+GeomNode').asList()
        if not geomList:
           geomList.append(collObj)

        # get the node's scale to preserve it
        meshScale=collObj.getScale(render)
        collNumVtx=0
        collnumface=0
        # dictionary to keep the overall vertex data length before appending the new data
        vDataStart={}
        # list for the vertices
        collVertices=[]
        # list for the vertices index
        collFaces=[]

        # append all vertex data into a complete list
        for collGeom in geomList:
            for gIdx in range(collGeom.node().getNumGeoms()):
                currentGeom=collGeom.node().getGeom(gIdx)
                collVtxData=currentGeom.getVertexData()
                numVtx=collVtxData.getNumRows()
                # append the current vertex data, IF it hasn't been added to the list,
                # otherwise, don't add it again, to avoid duplicated vertex data,
                # which may be shared by several geoms
                if not vDataStart.has_key(collVtxData):
                   # store the number of the collected vertices so far,
                   # to mark the index start for the next vertex data
                   vDataStart[collVtxData]=collNumVtx
                   # create vertex reader
                   collvtxreader=GeomVertexReader(collVtxData)
                   # set the start position for reading the vertices,
                   # begin reading at column 0, which is the vertex position
                   collvtxreader.setColumn(0)
                   # begin reading at vertex 0
                   collvtxreader.setRow(0)
                   for i in range(numVtx):
                       # respect each geomNode's transformation which may be exist
                       vtx=collObj.getRelativePoint(collGeom,collvtxreader.getData3f())
                       # synchronize TriMesh to the current scale of the collision mesh
                       vtx1=vtx[0]*meshScale[0]
                       vtx2=vtx[1]*meshScale[1]
                       vtx3=vtx[2]*meshScale[2]
                       collVertices.append((vtx1,vtx2,vtx3))
                   # add the current collected vertices count
                   collNumVtx+=numVtx

        # storing the vertices index
        for collGeom in geomList:
            for gIdx in range(collGeom.node().getNumGeoms()):
                geom=collGeom.node().getGeom(gIdx)
                collVtxData=geom.getVertexData()
                vDataBegin=vDataStart[collVtxData]
                for prim in range(geom.getNumPrimitives()):
                    # store the vertices index for each triangle
                    collFaceData=geom.getPrimitive(prim).decompose()
                    # get the triangle counts
                    numface=collFaceData.getNumFaces()
                    # get the start index of current primitive at geom's vertex data
                    s = collFaceData.getPrimitiveStart(prim)
                    for i in range(numface):
                        # refer to the vertex data length list created earlier
                        vtx1=vDataBegin+collFaceData.getVertex(s+i*3)
                        vtx2=vDataBegin+collFaceData.getVertex(s+i*3+1)
                        vtx3=vDataBegin+collFaceData.getVertex(s+i*3+2)
                        collFaces.append((vtx1,vtx2,vtx3))
                    collnumface+=numface

        meshdata=OdeTriMeshData(collObj)
        # create TriMesh data
        ##meshdata.build(collVertices,collFaces)
        # and pass it to ODE
        self.geom = OdeTriMeshGeom(space,meshdata)

        # create body if the object is dynamic, otherwise don't
        if density:
           M2 = OdeMass()
           M2.setBox(density, 1,1,1)
           self.body = OdeBody(world)
           self.body.setMass(M2)
           self.geom.setBody(self.body)
        # store object's properties
        self.storeProps(pythonObject, density, surfaceFriction, noColl_ID)

        print '###############################'
        print collObj
        collObj.analyze()
        print '--- sent to ODE ---'
        print 'Vertices : ',collNumVtx
        print 'Faces    : ',collnumface
        print '###############################\n'

        # originally only to debug the transfer method
        self.visualize(collnumface)

        # synchronize TriMesh to the current transformation (position & rotation) of the collision mesh
        self.geom.setPosition(collObj.getPos(render))
        self.geom.setQuaternion(collObj.getQuat(render))

        # hide the collision geometry, if it's not the visible object
        #if not showCollObj and collObj!=pythonObject:
        #   collObj.hide()

    def visualize(self,collnumface):
        ''' this method creates the actual geometry succesfully sent to ODE,
            originally only to debug the transfer method '''

        return  #(step.1) create GeomVertexData and add vertex information
        format=GeomVertexFormat.getV3()
        vdata=GeomVertexData('vertices', format, Geom.UHStatic)
        vertexWriter=GeomVertexWriter(vdata, 'vertex')
        tris=GeomTriangles(Geom.UHStatic)

        for i in range(collnumface):
          vtx1,vtx2,vtx3=self.geom.getTriangle(i)
          vertexWriter.addData3f(*vtx1)
          vertexWriter.addData3f(*vtx2)
          vertexWriter.addData3f(*vtx3)
          #(step.2) make primitives and assign vertices to them
          tris.addConsecutiveVertices(i*3,3)
          #indicates that we have finished adding vertices for the triangle
          tris.closePrimitive()

        #(step.3) make a Geom object to hold the primitives
        collmeshGeom=Geom(vdata)
        collmeshGeom.addPrimitive(tris)
        #(step.4) now put geom in a GeomNode
        collmeshGN=GeomNode('')
        collmeshGN.addGeom(collmeshGeom)

        self.visualizer = self.pythonObject.attachNewNode(collmeshGN)
        self.visualizer.setRenderModeWireframe(1)
        self.visualizer.setColor(1,1,1,1)
        scale=self.pythonObject.getScale()
        self.visualizer.setScale(1./scale[0],1./scale[1],1./scale[2])
        self.visualizer.setLightOff()
        # put the axis at object's origin (represents it's center of gravity)
        axis = loader.loadModelCopy('zup-axis')
        axis.reparentTo(self.visualizer)
        axis.setScale(.25)


class ODEsim:
    ''' this class consists of methods which are associated with
        ODE simulation setting & loop '''

    def initODE(self):
        self.ode_WORLD = OdeWorld()
        self.ode_WORLD.setGravity((0, 0, -9.81))
        #self.ode_WORLD.setCFM(0)
#        self.ode_WORLD.setContactMaxCorrectingVel(1)
#        self.ode_WORLD.setERP(0.8)
        self.ode_WORLD.setContactSurfaceLayer(.0001)
        self.ode_SPACE = OdeSimpleSpace()
        self.floor = OdePlaneGeom(self.ode_SPACE, Vec4(0, 0, 1, 0))
        self.ode_CONTACTgroup = OdeJointGroup()
        self.ODEdt = 1.0 / 80.0

    def scalp (self, vec, scal):
        vec[0] *= scal
        vec[1] *= scal
        vec[2] *= scal

    def near_callback(self, args, geom1, geom2):
        '''Callback function for the collide() method.

        This function checks if the given geoms do collide and
        creates contact joints if they do.
        '''

        # don't check for collision IF both geoms build a larger collision geom,
        # because they probably overlap each other
#        noColl1=101010
#        noColl2=-noColl1
#        if hasattr(geom1, 'noColl'):
#           noColl1=geom1.noColl
#        if hasattr(geom2, 'noColl'):
#           noColl2=geom2.noColl
#        if noColl1==noColl2:
#           return

        # Check if the objects do collide
        # averaging the surfaceFriction coefficient of the two colliding objects
        surfaceParams = OdeSurfaceParameters()
        surfaceFriction1=surfaceFriction2=0
        if hasattr(geom1, 'surfaceFriction'):
            surfaceParams.setMu(geom1.surfaceFriction)
        if hasattr(geom2, 'surfaceFriction'):
            surfaceParams.setMu2(geom1.surfaceFriction)

        entries = []
        entry = OdeUtil.collide(geom1, geom2,2)
        if entry.getNumContacts():
           entries .append(entry)
            



#        print 'AVG :',geom1, geom2, averageFrictionCoef

        # looking for TriMesh-anything collision
        geom1_is_TriMesh=type(geom1).__name__=='GeomTriMesh'
        geom2_is_TriMesh=type(geom2).__name__=='GeomTriMesh'
        bothTriMesh=geom1_is_TriMesh and geom2_is_TriMesh
        if bothTriMesh:
           g1Vel=g2Vel=Vec3(0,0,0)
           g1body=geom1.getBody()
           if g1body:
              g1Vel=Vec3(*g1body.getLinearVel())
           g2body=geom2.getBody()
           if g2body:
              g2Vel=Vec3(*g2body.getLinearVel())

           diff=40.0/(g1Vel-g2Vel).length()
           diff=min(20.0,diff)
           bouncePerContact=diff/len(entries)
#           print diff,bouncePerContact

        if ( geom1_is_TriMesh or geom2_is_TriMesh ) and self.contactVis:
           LSpoint=LineSegs()
           LSpoint.setColor(1,1,0)
           LSpoint.setThickness(8)
           LSnormal=LineSegs()
           LSnormal.setColor(1,.5,.2)
           LSnormal.setThickness(2)
           TriMeshCollision=1
        else:
           TriMeshCollision=0

#          surfaceParams.setBounce(geom1Data.surfaceBounce)
#          surfaceParams.setBounceVel(geom1Data.surfaceBounceVel)
#          surfaceParams.setSlip1(geom1Data.surfaceSlip)
#          surfaceParams.setSlip2(geom2Data.surfaceSlip)

        # Create contact joints
        self.ode_WORLD, self.ode_CONTACTgroup = args

        numContacts = entry.getNumContacts()
        if numContacts > 4:
            numContacts = 4
        for i in range(numContacts):
            cgeom = entry.getContactGeom(i)
            contactPoint = entry.getContactPoint(i)
            # if any TriMesh collision, collect the contact points
            if TriMeshCollision:
               pos, normal, depth, g1, g2 = entry.getContactGeomParams()
               # create a single point, call moveTo only
               pos=Point3(pos[0],pos[1],pos[2])
               LSpoint.moveTo(pos)
               # create a line
               LSnormal.moveTo(pos)
               LSnormal.drawTo(pos+Point3(normal[0],normal[1],normal[2]))

            # add more bounce if both objects are TriMesh
            if bothTriMesh:
                surfaceParams.setBounce(bouncePerCountact)
            else:
                surfaceParams.setBounce(0.2)


            contact = OdeContact()
            contact.setGeom(cgeom)
            contact.setFdir1(cgeom.getNormal())
            contact.setSurface(surfaceParams)
            j = OdeContactJoint(self.ode_WORLD, self.ode_CONTACTgroup, contact)
            j.attach(geom1.getBody(), geom2.getBody())

        # render TriMesh contacts
        if TriMeshCollision:
           contactVisualizer=render.attachNewNode('')
           contactVisualizer.attachNewNode(LSpoint.create())
           contactVisualizer.attachNewNode(LSnormal.create())
           contactVisualizer.setLightOff()
           # remove the visualized TriMesh contacts, after the given time
           taskMgr.doMethodLater(.01,self.removeContactVis,'removeContact',[contactVisualizer])

    def removeContactVis(self,vis):
        vis.removeNode()

    def simulate(self):
        # synchronize the position and rotation of the visible object to it's body
        for o in self.simObjects:
            if o.density and o.pythonObject!=None:
               body = o.body
               o.pythonObject.setPos(render,*body.getPosition())
               o.pythonObject.setQuat(render,Quat(*body.getQuaternion()))

        self.ode_SPACE.collide((self.ode_WORLD,self.ode_CONTACTgroup), self.near_callback)
        self.ode_WORLD.quickStep(self.ODEdt)
        ''' you can switch to standard world step, for more accuracy,
        but on most cases, it causes simulation instability '''
        #self.ode_WORLD.step(self.ODEdt)
        self.ode_CONTACTgroup.empty()
