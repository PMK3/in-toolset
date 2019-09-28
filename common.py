
class Signal:
	def __init__(self):
		self.callbacks = []
		
	def connect(self, func):
		self.callbacks.append(func)
		
	def disconnect(self, func):
		self.callbacks.remove(func)
		
	def emit(self, *args):
		for func in self.callbacks:
			func(*args)
			
	__call__ = emit

			
class Property:
	def __init__(self, signame, default=None):
		self.signame = signame
		self.default = default
		self.name = None
		
	def read(self, inst): return inst.__dict__.get(self.name, self.default)
	def write(self, inst, value):
		inst.__dict__[self.name] = value
		inst.__dict__[self.signame].emit()
		
	def __set__(self, instance, value):
		old = self.read(instance)
		if value != old:
			self.write(instance, value)
			
	def __get__(self, instance, owner):
		return self.read(instance)
		
	def __set_name__(self, owner, name):
		self.name = name