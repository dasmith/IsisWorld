'''
Chris Jones

Syntax for worldgen files:
	<object> at <x>,<y>,<z>		<-- Creates a new object of type <object> location (x, y, z)
	<object> in <object2>		<-- Creates a new object placed in object2
	<object> on <object2>		<-- Creates a new object on top of object2
'''

class ObjectLoader():
	def __init__(self, generators, target):
		self.gens = generators
		self.ids = {}
		self.target = target

	def loadObject(self, name):
		if name in self.gens:
			obj = self.gens[name].generate()
			self.ids[name] = id(obj)
			return obj
		return None

	def parseFile(self, file):
		file = open(file, "r")

		for s in file :
			tokens = s.lower().split(None, 3)
			dest = None
			if tokens[2] in self.ids:
				dest = self.target.find(tokens[2]+str(self.ids[tokens[2]]))
			o = self.loadObject(tokens[0])

			if tokens[1] == "at":
				x, y, z = tokens[2].split(",")
				o.setPos(float(x), float(y), float(z))
				o.reparentTo(self.target)
			elif dest:
				if tokens[1] == "on":
					dest.placeOn(o)
				elif tokens[21] == "in":
					dest.placeIn(o)