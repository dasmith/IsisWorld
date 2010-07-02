import direct.directbase.DirectStart 

import math
from pandac.PandaModules import Point3, Vec3 
from pandac.PandaModules import GeomVertexFormat, GeomVertexData, GeomVertexWriter 
from pandac.PandaModules import Geom, GeomNode, GeomPoints, NodePath, GeomLinestrips 

""" 
(FenrirWolf's wireGeom http://www.panda3d.org/phpbb2/viewtopic.php?t=6619 for visualisation) 


Note that wireprims are wire-like representations of geom, in the same manner as Ogre's debug mode.  I find this the most useful way to represent 
ODE geom structures visually, as you can clearly see the orientation versus a more generic wireframe mesh. 

These wireprims are rendered as linestrips.  Therefore, only vertices are required and texturing is not supported.  You can use standard render attribute changes such 
as setColor in order to change the line's color.  By default it is green. 

This class merely returns a NodePath to a GeomNode that is a representation of what is requested.  You can use this outside of ODE geom visualizations, obviously. 

Supported are sphere, box, cylinder, capsule (aka capped cylinder), ray, and plane 

to use: 

sphereNodepath = wireGeom().generate ('sphere', radius=1.0) 
boxNodepath = wireGeom().generate ('box', extents=(1, 1, 1)) 
cylinderNodepath = wireGeom().generate ('cylinder', radius=1.0, length=3.0) 
rayNodepath = wireGeom().generate ('ray', length=3.0) 
planeNodepath = wireGeom().generate ('plane') 

""" 
class wireGeom: 
  
  def __init__ (self):    
    # GeomNode to hold our individual geoms 
    self.gnode = GeomNode ('wirePrim') 
    
    # How many times to subdivide our spheres/cylinders resulting vertices.  Keep low 
    # because this is supposed to be an approximate representation 
    self.subdiv = 12 

  def line (self, start, end):  
    
    # since we're doing line segments, just vertices in our geom 
    format = GeomVertexFormat.getV3() 
    
    # build our data structure and get a handle to the vertex column 
    vdata = GeomVertexData ('', format, Geom.UHStatic) 
    vertices = GeomVertexWriter (vdata, 'vertex') 
        
    # build a linestrip vertex buffer 
    lines = GeomLinestrips (Geom.UHStatic) 
    
    vertices.addData3f (start[0], start[1], start[2]) 
    vertices.addData3f (end[0], end[1], end[2]) 
    
    lines.addVertices (0, 1) 
      
    lines.closePrimitive() 
    
    geom = Geom (vdata) 
    geom.addPrimitive (lines) 
    # Add our primitive to the geomnode 
    self.gnode.addGeom (geom) 

  def circle (self, radius, axis, offset):  
    
    # since we're doing line segments, just vertices in our geom 
    format = GeomVertexFormat.getV3() 
    
    # build our data structure and get a handle to the vertex column 
    vdata = GeomVertexData ('', format, Geom.UHStatic) 
    vertices = GeomVertexWriter (vdata, 'vertex') 
        
    # build a linestrip vertex buffer 
    lines = GeomLinestrips (Geom.UHStatic) 
    
    for i in range (0, self.subdiv): 
      angle = i / float(self.subdiv) * 2.0 * math.pi 
      ca = math.cos (angle) 
      sa = math.sin (angle) 
      if axis == "x": 
        vertices.addData3f (0, radius * ca, radius * sa + offset) 
      if axis == "y": 
        vertices.addData3f (radius * ca, 0, radius * sa + offset) 
      if axis == "z": 
        vertices.addData3f (radius * ca, radius * sa, offset) 
    
    for i in range (1, self.subdiv): 
      lines.addVertices(i - 1, i) 
    lines.addVertices (self.subdiv - 1, 0) 
      
    lines.closePrimitive() 
    
    geom = Geom (vdata) 
    geom.addPrimitive (lines) 
    # Add our primitive to the geomnode 
    self.gnode.addGeom (geom) 

  def capsule (self, radius, length, axis): 
    
    # since we're doing line segments, just vertices in our geom 
    format = GeomVertexFormat.getV3() 
    
    # build our data structure and get a handle to the vertex column 
    vdata = GeomVertexData ('', format, Geom.UHStatic) 
    vertices = GeomVertexWriter (vdata, 'vertex') 
        
    # build a linestrip vertex buffer 
    lines = GeomLinestrips (Geom.UHStatic) 
    
    # draw upper dome 
    for i in range (0, self.subdiv / 2 + 1): 
      angle = i / float(self.subdiv) * 2.0 * math.pi 
      ca = math.cos (angle) 
      sa = math.sin (angle) 
      if axis == "x": 
        vertices.addData3f (0, radius * ca, radius * sa + (length / 2)) 
      if axis == "y": 
        vertices.addData3f (radius * ca, 0, radius * sa + (length / 2)) 

    # draw lower dome 
    for i in range (0, self.subdiv / 2 + 1): 
      angle = -math.pi + i / float(self.subdiv) * 2.0 * math.pi 
      ca = math.cos (angle) 
      sa = math.sin (angle) 
      if axis == "x": 
        vertices.addData3f (0, radius * ca, radius * sa - (length / 2)) 
      if axis == "y": 
        vertices.addData3f (radius * ca, 0, radius * sa - (length / 2)) 
    
    for i in range (1, self.subdiv + 1): 
      lines.addVertices(i - 1, i) 
    lines.addVertices (self.subdiv + 1, 0) 
      
    lines.closePrimitive() 
    
    geom = Geom (vdata) 
    geom.addPrimitive (lines) 
    # Add our primitive to the geomnode 
    self.gnode.addGeom (geom) 

  def rect (self, width, height, axis): 
    
    # since we're doing line segments, just vertices in our geom 
    format = GeomVertexFormat.getV3() 
    
    # build our data structure and get a handle to the vertex column 
    vdata = GeomVertexData ('', format, Geom.UHStatic) 
    vertices = GeomVertexWriter (vdata, 'vertex') 
        
    # build a linestrip vertex buffer 
    lines = GeomLinestrips (Geom.UHStatic) 
    
    # draw a box 
    if axis == "x": 
      vertices.addData3f (0, -width, -height) 
      vertices.addData3f (0, width, -height) 
      vertices.addData3f (0, width, height) 
      vertices.addData3f (0, -width, height) 
    if axis == "y": 
      vertices.addData3f (-width, 0, -height) 
      vertices.addData3f (width, 0, -height) 
      vertices.addData3f (width, 0, height) 
      vertices.addData3f (-width, 0, height) 
    if axis == "z": 
      vertices.addData3f (-width, -height, 0) 
      vertices.addData3f (width, -height, 0) 
      vertices.addData3f (width, height, 0) 
      vertices.addData3f (-width, height, 0) 

    for i in range (1, 3): 
      lines.addVertices(i - 1, i) 
    lines.addVertices (3, 0) 
      
    lines.closePrimitive() 
    
    geom = Geom (vdata) 
    geom.addPrimitive (lines) 
    # Add our primitive to the geomnode 
    self.gnode.addGeom (geom) 

  def generate (self, type, radius=1.0, length=1.0, extents=Point3(1, 1, 1)): 
            
    if type == 'sphere': 
      # generate a simple sphere 
      self.circle (radius, "x", 0) 
      self.circle (radius, "y", 0) 
      self.circle (radius, "z", 0) 

    if type == 'capsule': 
      # generate a simple capsule 
      self.capsule (radius, length, "x") 
      self.capsule (radius, length, "y") 
      self.circle (radius, "z", -length / 2) 
      self.circle (radius, "z", length / 2) 

    if type == 'box': 
      # generate a simple box 
      self.rect (extents[1], extents[2], "x") 
      self.rect (extents[0], extents[2], "y") 
      self.rect (extents[0], extents[1], "z") 

    if type == 'cylinder': 
      # generate a simple cylinder 
      self.line ((0, -radius, -length / 2), (0, -radius, length / 2)) 
      self.line ((0, radius, -length / 2), (0, radius, length / 2)) 
      self.line ((-radius, 0, -length / 2), (-radius, 0, length / 2)) 
      self.line ((radius, 0, -length / 2), (radius, 0, length / 2)) 
      self.circle (radius, "z", -length / 2) 
      self.circle (radius, "z", length / 2) 
    
    if type == 'ray': 
      # generate a ray 
      self.circle (length / 10, "x", 0) 
      self.circle (length / 10, "z", 0) 
      self.line ((0, 0, 0), (0, 0, length)) 
      self.line ((0, 0, length), (0, -length / 10, length * 0.9)) 
      self.line ((0, 0, length), (0, length / 10, length * 0.9)) 

    if type == 'plane': 
      # generate a plane 
      length = 3.0 
      self.rect (1.0, 1.0, "z") 
      self.line ((0, 0, 0), (0, 0, length)) 
      self.line ((0, 0, length), (0, -length / 10, length * 0.9)) 
      self.line ((0, 0, length), (0, length / 10, length * 0.9)) 
    
    # rename ourselves to wirePrimBox, etc. 
    name = self.gnode.getName() 
    self.gnode.setName(name + type.capitalize()) 
    
    NP = NodePath (self.gnode)  # Finally, make a nodepath to our geom 
    NP.setColor(0.0, 1.0, 0.0)   # Set default color 
    
    return NP
