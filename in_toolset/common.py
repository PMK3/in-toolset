
class Signal:
	def __init__(self):
		self.callbacks = []
		
	def connect(self, func, *param):
		self.callbacks.append((func, param))
		
	def disconnect(self, func, *param):
		self.callbacks.remove((func, param))
		
	def emit(self, *args):
		for func, param in self.callbacks:
			func(*args, *param)
			
	__call__ = emit
	
	
class SignalListener:
	def __init__(self):
		self.listeners = []
		
	def connect(self, signal, callback):
		self.listeners.append((signal, callback))
		signal.connect(callback)
		
	def disconnect(self):
		for signal, callback in self.listeners:
			signal.disconnect(callback)
		self.listeners = []

			
class Property:
	def __init__(self, signame, default=None):
		self.signame = signame
		self.default = default
		
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