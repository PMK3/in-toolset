
from enum import Enum, auto
from signal import Signal
from objectlist import Object, ObjectList, Node
import math
import json


class Place(Node):
	def __init__(self, net, x=0, y=0, tokens=0):
		super().__init__(net, x, y)
		self.tokensChanged = Signal()
		self._tokens = tokens
		self.setTokens(tokens)

	def setTokens(self, amount):
		if amount != self.getTokens():
			self._tokens = amount
			self.tokensChanged.emit()

	def getTokens(self):
		return self._tokens

	tokens = property(getTokens, setTokens)


class TransitionType(Enum):
	INTERNAL = auto()
	INPUT = auto()
	OUTPUT = auto()


class Transition(Node):
	def __init__(self, net, x=0, y=0, type=TransitionType.INTERNAL):
		super().__init__(net, x, y)
		self.type = type

	def canTrigger(self):
		for input in self.net.inputs:
			if input.transition == self and input.place.tokens < 1:
				return False
		return True

	def trigger(self):
		if not self.canTrigger():
			raise ValueError("No tokens available")

		for input in self.net.inputs:
			if input.transition == self:
				input.place.tokens -= 1

		for output in self.net.outputs:
			if output.transition == self:
				output.place.tokens += 1


class Arrow(Object):
	def __init__(self, net, place=None, transition=None):
		super().__init__(net)
		self.place = place
		self.transition = transition
		if self.place and self.transition:
			self.connect()

	def connect(self):
		self.place.deleted.connect(self.delete)
		self.transition.deleted.connect(self.delete)

	def load(self, data):
		super().load(data)
		self.place = self.net.places[data["place"]]
		self.transition = self.net.transitions[data["transition"]]
		self.connect()

	def save(self):
		data = super().save()
		data["place"] = self.place.id
		data["transition"] = self.transition.id
		return data

	def similar(self, obj):
		return obj.active and obj.place == self.place and obj.transition == self.transition

class PetriNet(Object):
	def __init__(self, parent=None):
		super().__init__(parent)

		self.places = ObjectList(self, Place)
		self.transitions = ObjectList(self, Transition)
		self.inputs = ObjectList(self, Arrow)
		self.outputs = ObjectList(self, Arrow)

	def setInitialMarking(self):
		placeIsSource = {}
		for place in self.places:
			place.tokens = 1
		for output in self.outputs:
			output.place.tokens = 0

	def load(self, data):
		super().load(data)
		self.places.load(data["places"])
		self.transitions.load(data["transitions"])
		self.inputs.load(data["inputs"])
		self.outputs.load(data["outputs"])
		self.setInitialMarking()

	def save(self):
		data = super().save()
		data["places"] = self.places.save()
		data["transitions"] = self.transitions.save()
		data["inputs"] = self.inputs.save()
		data["outputs"] = self.outputs.save()
		return data

	def triggerRandomTransition(self):
		triggerable = [transition for transition in self.transitions if transition.canTrigger()]
		if not triggerable.empty():
			random.choice(triggerables).trigger()
		else:
			raise ValueError("No Triggerable Transition Available")


class Project:
	def __init__(self):
		self.filenameChanged = Signal()
		self.unsavedChanged = Signal()

		self.net = PetriNet()
		self.net.changed.connect(self.setUnsaved)
		self.filename = None
		self.unsaved = False

	def setFilename(self, filename):
		if self.filename != filename:
			self.filename = filename
			self.filenameChanged.emit()

	def setUnsaved(self, unsaved=True):
		if self.unsaved != unsaved:
			self.unsaved = unsaved
			self.unsavedChanged.emit()

	def load(self, filename):
		with open(filename) as f:
			data = json.load(f)
		self.net.load(data)

		self.setFilename(filename)
		self.setUnsaved(False)

	def save(self, filename):
		data = self.net.save()
		with open(filename, "w") as f:
			json.dump(data, f, indent="\t")

		self.setFilename(filename)
		self.setUnsaved(False)
