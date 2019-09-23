
from enum import Enum, auto
from signal import Signal
import math
import json


class Object:
	def __init__(self, net):
		self.changed = Signal()
		self.deleted = Signal()
		self.labelChanged = Signal()

		self.net = net
		self.active = True
		self.id = None
		self.label = ""

	def delete(self):
		if self.active:
			self.active = False
			self.deleted.emit()
			self.changed.emit()

	def load(self, data):
		self.id = data["id"]

	def save(self):
		return {
			"id": self.id
		}

	def similar(self, obj):
		return False


class Node(Object):
	def __init__(self, net, x=0, y=0):
		super().__init__(net)
		self.positionChanged = Signal()
		self.labelChanged = Signal()

		self.x = x
		self.y = y

		self.label = ""
		self.labelAngle = math.pi / 2
		self.labelDistance = 35

	def move(self, x, y):
		self.x = x
		self.y = y
		self.positionChanged.emit()
		self.changed.emit()

	def setLabel(self, label):
		self.label = label
		self.labelChanged.emit()
		self.changed.emit()

	def setLabelAngle(self, angle):
		self.labelAngle = angle
		self.labelChanged.emit()
		self.changed.emit()

	def setLabelDistance(self, dist):
		self.labelDistance = dist
		self.labelChanged.emit()
		self.changed.emit()

	def load(self, data):
		super().load(data)
		self.x = data["x"]
		self.y = data["y"]
		self.label = data["label"]
		self.labelAngle = data["labelAngle"]
		self.labelDistance = data["labelDistance"]

	def save(self):
		data = super().save()
		data["x"] = self.x
		data["y"] = self.y
		data["label"] = self.label
		data["labelAngle"] = self.labelAngle
		data["labelDistance"] = self.labelDistance
		return data


class Place(Node):
	def __init__(self, net, x=0, y=0, tokens=0):
		super().__init__(net, x, y)
		self.tokens = tokens

class TransitionType(Enum):
	INTERNAL = auto()
	INPUT = auto()
	OUTPUT = auto()

class Transition(Node):
	def __init__(self, net, x=0, y=0, type=TransitionType.INTERNAL):
		super().__init__(net, x, y)
		self.type = type

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


class ObjectList:
	def __init__(self, net, cls):
		self.changed = Signal()
		self.added = Signal()

		self.changed.connect(net.changed.emit)

		self.net = net
		self.cls = cls
		self.objects = {}
		self.nextId = 0

	def __getitem__(self, item):
		return self.objects[item]

	def __iter__(self):
		return self.objects.__iter__()

	def add(self, obj):
		if obj.id in self.objects:
			return

		if any(obj.similar(x) for x in self.objects.values()):
			return

		if obj.id is None:
			obj.id = self.nextId
			self.nextId += 1

		obj.changed.connect(self.changed.emit)

		self.objects[obj.id] = obj
		self.added.emit(obj)
		self.changed.emit()

	def load(self, infos):
		for info in infos:
			obj = self.cls(self.net)
			obj.load(info)
			self.add(obj)
		self.nextId = max(self.objects, default=0) + 1

	def save(self):
		list = []
		for obj in self.objects.values():
			if obj.active:
				list.append(obj.save())
		return list


class PetriNet:
	def __init__(self):
		self.changed = Signal()

		self.places = ObjectList(self, Place)
		self.transitions = ObjectList(self, Transition)
		self.inputs = ObjectList(self, Arrow)
		self.outputs = ObjectList(self, Arrow)

	def setInitialMarking(self):
		for place in self.places.objects.values():
			source = True
			for arrow in self.outputs.objects.values():
				if arrow.place == place:
					source = False
					place.tokens = 0
					break
			if source:
				place.tokens = 1
				print("Source")
			else:
				place.tokens = 0
				print("No Source")

	def load(self, data):
		self.places.load(data["places"])
		self.transitions.load(data["transitions"])
		self.inputs.load(data["inputs"])
		self.outputs.load(data["outputs"])

	def save(self):
		return {
			"places": self.places.save(),
			"transitions": self.transitions.save(),
			"inputs": self.inputs.save(),
			"outputs": self.outputs.save()
		}
		return data


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
