""" Misc. utility functions"""


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
