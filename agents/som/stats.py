
import math

## misc statistical utilities
def mean(values):
    """Return the arithmetic average of the values"""
    return sum(values) / float(len(values))

def stddev(values):
    """The standard deviation of a set of values."""
    return math.sqrt(sum([(x - mean(values))**2 for x in values]) / (len(values)-1))
