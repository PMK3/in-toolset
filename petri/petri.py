
from petri.base import Object, Node, ObjectList
from common import Signal, Property
import random


class Place(Node):
	tokens = Property("tokensChanged", 0)
	
	def __init__(self, x, y):
		super().__init__(x, y)
		self.tokensChanged = Signal()
		self.tokensChanged.connect(self.changed)
		
	def setTokens(self, tokens): self.tokens = tokens
	
	def take(self): self.tokens -= 1
	def give(self): self.tokens += 1


class Transition(Node):
	enabled = Property("enabledChanged", True)
	source = Property("sourceChanged", True)
	sink = Property("sinkChanged", True)
	
	def __init__(self, x, y):
		super().__init__(x, y)
		self.enabledChanged = Signal()
		self.sourceChanged = Signal()
		self.sinkChanged = Signal()
		
		self.inputs = []
		self.outputs = []
		
	def checkEnabled(self):
		for input in self.inputs:
			if input.tokens == 0:
				return False
		return True
		
	def updateEnabled(self):
		self.enabled = self.checkEnabled()
		
	def updateProperties(self):
		self.updateEnabled()
		self.source = len(self.inputs) == 0
		self.sink = len(self.outputs) == 0
		
	def addInput(self, input):
		self.inputs.append(input)
		self.updateProperties()
		input.tokensChanged.connect(self.updateEnabled)
		
	def removeInput(self, input):
		input.tokensChanged.disconnect(self.updateEnabled)
		self.inputs.remove(input)
		self.updateProperties()
		
	def addOutput(self, output):
		self.outputs.append(output)
		self.updateProperties()
	
	def removeOutput(self, output):
		self.outputs.remove(output)
		self.updateProperties()
		
	def trigger(self):
		for input in self.inputs:
			input.take()
		for output in self.outputs:
			output.give()


class ArrowType:
	INPUT = 0
	OUTPUT = 1

class Arrow(Object):
	def __init__(self, type, place, transition):
		super().__init__()
		self.type = type
		self.place = place
		self.transition = transition
			
		self.place.deleted.connect(self.delete)
		self.transition.deleted.connect(self.delete)
		
		self.restored.connect(self.register)
		self.deleted.connect(self.unregister)
		
		self.register()
		
	def register(self):
		if self.type == ArrowType.INPUT:
			self.transition.addInput(self.place)
		else:
			self.transition.addOutput(self.place)
			
	def unregister(self):
		if self.type == ArrowType.INPUT:
			self.transition.removeInput(self.place)
		else:
			self.transition.removeOutput(self.place)


class PetriNet:
	deadlock = Property("deadlockChanged", True)
	
	def __init__(self):
		self.changed = Signal()
		self.deadlockChanged = Signal()

		self.places = ObjectList()
		self.transitions = ObjectList()
		self.inputs = ObjectList()
		self.outputs = ObjectList()
		
		self.places.changed.connect(self.changed)
		self.transitions.changed.connect(self.changed)
		self.inputs.changed.connect(self.changed)
		self.outputs.changed.connect(self.changed)
		
		self.transitions.added.connect(self.registerTransition)
		
	def checkDeadlock(self):
		self.deadlock = not any(t.enabled for t in self.transitions)
		
	def registerTransition(self, transition):
		transition.enabledChanged.connect(self.checkDeadlock)
		transition.statusChanged.connect(self.checkDeadlock)
		self.checkDeadlock()
		
	def merge(self, net):
		self.places.merge(net.places)
		self.transitions.merge(net.transitions)
		self.inputs.merge(net.inputs)
		self.outputs.merge(net.outputs)
		
	def triggerRandom(self):
		transitions = [t for t in self.transitions if t.enabled]
		random.choice(transitions).trigger()
