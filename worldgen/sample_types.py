

class Object():
	def __init__(self, layout=None):
		if layout:
			self.layout = layout
		else:
			self.layout = DefaultLayout()

class 