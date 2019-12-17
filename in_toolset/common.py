"""This module allows for signalling with callbacks and interconnectable signals.
To do this, the :py:class:`~in_toolset.common.Signal` and :py:class:`~in_toolset.common.SignalListener` classes are used.
Furthermore, it provides the class :py:class:`~in_toolset.common.Property` which allows the creation of object properties with associated signals to signify changes."""

class Signal:
	"""A Signal basically consists of a list of callbacks and associated params that will be called when :py:meth:`~in_toolset.common.Signal.emit` is called."""
	def __init__(self):
		self.callbacks = []
		
	def connect(self, func, *param):
		"""Connect a callback, to be called when when :py:meth:`~in_toolset.common.Signal.emit` is called."""
		self.callbacks.append((func, param))
		
	def disconnect(self, func, *param):
		"""Disconnect or remove a callback so that it will no longer be called when :py:meth:`~in_toolset.common.Signal.emit` is called."""
		self.callbacks.remove((func, param))
		
	def emit(self, *args):
		"""Call all connected callbacks with `args` and their associated `param`"""
		for func, param in self.callbacks:
			func(*args, *param)
			
	__call__ = emit
	
	
class SignalListener:
	"""The SignalListener class groups callbacks and the signals to which they were added to allow for easier deletion/disconnection."""

	def __init__(self):
		self.listeners = []
		
	def connect(self, signal, callback):
		"""Connect `callback` to `signal` and store it in `this`"""
		self.listeners.append((signal, callback))
		signal.connect(callback)
		
	def disconnect(self):
		"""Disconnect all callbacks stored in `this`"""
		for signal, callback in self.listeners:
			signal.disconnect(callback)
		self.listeners = []

			
class Property:
	"""A basic property system that can be used to add properties with getters, setters, and signals to a class.."""
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
