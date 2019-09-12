
class Signal:
	def __init__(self):
		self.callbacks = []
		
	def connect(self, func):
		self.callbacks.append(func)
		
	def emit(self, *args):
		for func in self.callbacks:
			func(*args)
