
from signal import Signal
import json


class Object:
	def __init__(self, net):
		self.net = net
		self.changed = Signal()
		self.deleted = Signal()
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
		self.label = data["label"]

	def save(self):
		return {
			"id": self.id,
			"label": self.label
		}


class Node(Object):
	def __init__(self, net, x=0, y=0):
		super().__init__(net)
		self.positionChanged = Signal()

		self.x = x
		self.y = y

	def move(self, x, y):
		self.x = x
		self.y = y
		self.positionChanged.emit(x, y)
		self.changed.emit()

	def load(self, data):
		super().load(data)
		self.x = data["x"]
		self.y = data["y"]

	def save(self):
		data = super().save()
		data["x"] = self.x
		data["y"] = self.y
		return data
	

class Place(Node):
	def __init__(self, net, x=0, y=0):
		super().__init__(net, x, y)
		self.tokens = 0


class Transition(Node):
	pass


class Arrow(Object):
	def __init__(self, net, place=None, transition=None):
		super().__init__(net)
		self.place = place
		self.place.deleted.connect(self.delete)
		self.transition = transition
		self.transition.deleted.connect(self.delete)

	def load(self, data):
		super().load(data)
		self.place = self.net.places[data["place"]]
		self.transition = self.net.transitions[data["transition"]]

	def save(self):
		data = super().save()
		data["place"] = self.place.id
		data["transition"] = self.transition.id
		return data
		
		
class ObjectList:
	def __init__(self, net, cls):
		self.changed = Signal()
		self.added = Signal()
		
		self.net = net
		self.cls = cls
		self.objects = {}
		self.nextId = 0
		
	def __getitem__(self, item):
		return self.objects[item]
		
	def add(self, obj):
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
		
		self.places.changed.connect(self.changed.emit)
		self.transitions.changed.connect(self.changed.emit)
		self.inputs.changed.connect(self.changed.emit)
		self.outputs.changed.connect(self.changed.emit)
		
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
