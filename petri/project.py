
from petri.petri import PetriNet, Place, Transition, Arrow, ArrowType
from common import Signal, Property
import json


class ProjectReader:
	def __init__(self, net):
		self.net = net
		
	def load(self, data):
		for info in data["places"]:
			self.loadPlace(info)
		for info in data["transitions"]:
			self.loadTransition(info)
		for info in data["inputs"]:
			self.loadArrow(info, ArrowType.INPUT)
		for info in data["outputs"]:
			self.loadArrow(info, ArrowType.OUTPUT)
			
	def loadPlace(self, info):
		place = Place(info["x"], info["y"])
		place.tokens = info["tokens"]
		self.readNode(place, info)
		
		self.net.places.add(place, info["id"])
		
	def loadTransition(self, info):
		trans = Transition(info["x"], info["y"])
		self.readNode(trans, info)
		
		self.net.transitions.add(trans, info["id"])
		
	def loadArrow(self, info, type):
		place = self.net.places[info["place"]]
		transition = self.net.transitions[info["transition"]]
		arrow = Arrow(type, place, transition)
		
		id = info["id"]
		if type == ArrowType.INPUT:
			self.net.inputs.add(arrow, id)
		else:
			self.net.outputs.add(arrow, id)
		
	def readNode(self, node, info):
		node.label = info["label"]
		node.labelAngle = info["labelAngle"]
		node.labelDistance = info["labelDistance"]
		
		
class ProjectWriter:
	def __init__(self, net):
		self.net = net
		
	def save(self):
		places = [self.savePlace(p) for p in self.net.places]
		transitions = [self.saveTransition(t) for t in self.net.transitions]
		inputs = [self.saveArrow(a) for a in self.net.inputs]
		outputs = [self.saveArrow(a) for a in self.net.outputs]
		return {
			"places": places,
			"transitions": transitions,
			"inputs": inputs,
			"outputs": outputs
		}
		
	def savePlace(self, place):
		data = self.saveNode(place)
		data["tokens"] = place.tokens
		return data
		
	def saveTransition(self, transition):
		return self.saveNode(transition)
		
	def saveArrow(self, arrow):
		data = self.saveObject(arrow)
		data["place"] = arrow.place.id
		data["transition"] = arrow.transition.id
		return data
		
	def saveNode(self, node):
		data = self.saveObject(node)
		data["x"] = node.x
		data["y"] = node.y
		data["label"] = node.label
		data["labelAngle"] = node.labelAngle
		data["labelDistance"] = node.labelDistance
		return data
		
	def saveObject(self, obj):
		return {"id": obj.id}


class Project:
	filename = Property("filenameChanged")
	unsaved = Property("unsavedChanged", False)
	
	def __init__(self):
		self.filenameChanged = Signal()
		self.unsavedChanged = Signal()

		self.net = PetriNet()
		self.net.changed.connect(self.setUnsaved)

	def setFilename(self, filename): self.filename = filename
	def setUnsaved(self, unsaved=True): self.unsaved = unsaved

	def load(self, filename):
		with open(filename) as f:
			data = json.load(f)
			
		reader = ProjectReader(self.net)
		reader.load(data)

		self.setFilename(filename)
		self.setUnsaved(False)

	def save(self, filename):
		writer = ProjectWriter(self.net)
		
		data = writer.save()
		with open(filename, "w") as f:
			json.dump(data, f, indent="\t")
			
		self.setFilename(filename)
		self.setUnsaved(False)
