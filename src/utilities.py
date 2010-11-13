""" Misc. utility functions"""

import struct
import xmlrpclib

def getOrientedBoundedBox(collObj):
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
    offset=collObj.getBounds().getCenter()-collObj.getPos()
    # bring object to it's parent and restore it's transformation
    collObj.reparentTo(parent)
    collObj.setTransform(trans)
    # (max - min) bounds
    box=bounds[1]-bounds[0]
#        print bounds[0], bounds[1]
    return [box[0],box[1],box[2]], [offset[0],offset[1],offset[2]]
    
def getObjFromNP(np,tag="isisobj"):
    """ Helper function to get the Python object from a NodePath involved with 
    a collision entry, using a tag """
    if np.hasPythonTag(tag):
        return np.getPythonTag(tag)
    else:
        p = np.getParent()
        if p.hasPythonTag(tag):
            return p.getPythonTag(tag)
        else:
            return np

def frange(x,y,inc):
    """ floating point xrange """
    while x <= y:
        if x < 0:
            yield -(abs(x)**2)
        else:
            yield x**2
        x += inc

def pnm_image__as__xmlrpc_image(source_pnm_image, max_x=320, max_y=240):
    source_x_size = source_pnm_image.getXSize()
    source_y_size = source_pnm_image.getYSize()
    x_size = source_x_size
    y_size = source_y_size
    if x_size > max_x:
        y_size = y_size * max_x / x_size
        x_size = max_x
    if y_size > max_y:
        x_size = x_size * max_y / y_size
        y_size = max_y
    rgb_string_image = ''
    for y in range(y_size):
        source_y = y * source_y_size / y_size
        for x in range(x_size):
            source_x = x * source_x_size / x_size
            red   = 255 * source_pnm_image.getRed(  source_x, source_y)
            green = 255 * source_pnm_image.getGreen(source_x, source_y)
            blue  = 255 * source_pnm_image.getBlue( source_x, source_y)
            rgb_string = struct.pack('BBB', red, green, blue)
            rgb_string_image += rgb_string
    return {'dict_type':'xmlrpc_image', 'width':x_size, 'height':y_size, 'rgb_data':xmlrpclib.Binary(rgb_string_image)}


def rgb_ram_image__as__xmlrpc_image(source_rgb_ram_image, max_x=None, max_y=None, x_offset=0, y_offset=0):
    print 'rgb_ram_image__as__xmlrpc_image.  x_offset =', x_offset, ' y_offset =', y_offset
    source_x_size   = source_rgb_ram_image['width']
    source_y_size   = source_rgb_ram_image['height']
    source_rgb_data = source_rgb_ram_image['rgb_data']
    reduction_factor = 1
    x_size           = source_x_size
    y_size           = source_y_size
    while ((max_x is not None) and (x_size > max_x)) or ((max_y is not None) and (y_size > max_y)):
        reduction_factor += 1
        x_size = source_x_size / reduction_factor
        y_size = source_y_size / reduction_factor
    rgb_string_image = ''
    for y in range(y_size):
        source_y = (source_y_size - 1) - ((y * (source_y_size - (reduction_factor - 1)) / y_size) + y_offset)
        for x in range(x_size):
            source_x = (x * (source_x_size - (reduction_factor - 1)) / x_size) + x_offset
            pixel_index = ((source_y * source_x_size) + source_x) * 3
            red   = source_rgb_data[pixel_index + 0]
            green = source_rgb_data[pixel_index + 1]
            blue  = source_rgb_data[pixel_index + 2]
            rgb_string = struct.pack('BBB', red, green, blue)
            rgb_string_image += rgb_string
    return {'dict_type':'xmlrpc_image', 'width':x_size, 'height':y_size, 'rgb_data':xmlrpclib.Binary(rgb_string_image), 'reduction_factor':reduction_factor}
    
