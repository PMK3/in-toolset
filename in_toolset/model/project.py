
from ..common import Signal, Property
from .base import *
from .ui import *
from .pnml import *
from PyQt5.QtCore import QFile
from PyQt5.QtCore import QIODevice
import json


class ProjectReader:
	"""Loads a project file (in our own json-based file format) corresponding to an inet into the program."""
	def load(self, data):
		self.loadPlaces(data)
		self.loadTransitions(data)
		self.loadEnterprises(data)

		industry = UIPetriNet()
		for place in self.places:
			industry.net.places.add(place)
		for trans in self.transitions:
			industry.net.transitions.add(trans)
		self.loadGraph(industry.graph, data["industry"], True)
		return industry

	def loadPlaces(self, data):
		self.places = []
		for info in data["places"]:
			place = Place()
			place.tokens = info
			self.places.append(place)

	def loadTransitions(self, data):
		self.transitions = []
		for info in data["transitions"]:
			transition = UITransition()
			transition.type = info["type"]
			transition.message = info["message"]
			self.transitions.append(transition)

	def loadEnterprises(self, data):
		self.enterprises = []
		for info in data["enterprises"]:
			enterprise = UIPetriNet()
			self.loadPetriNet(enterprise.net, info["net"])
			self.loadGraph(enterprise.graph, info["graph"], False)
			self.enterprises.append(enterprise)

	def loadPetriNet(self, net, data):
		for place in data["places"]:
			net.places.add(self.places[place])
		for transition in data["transitions"]:
			net.transitions.add(self.transitions[transition])

	def loadGraph(self, graph, data, industry):
		for info in data["nodes"]:
			obj = self.parseObjectRef(info)
			node = UINode(obj)
			self.loadPosition(node, info["pos"])
			self.loadLabel(node.label, info["label"])
			graph.nodes.add(node)

		for info in data["looseArrows"]:
			node = graph.nodes[info["node"]]
			transition = self.transitions[info["transition"]]

			arrow = UILooseArrow(node, transition)
			arrow.angle = info["angle"]
			self.loadLabel(arrow.label, info["label"])

			graph.looseArrows.add(arrow)

		for info in data["arrows"]:
			if industry:
				source = graph.looseArrows[info["source"]]
				target = graph.looseArrows[info["target"]]
				channel = self.places[info["channel"]]

				arrow = UIChannelArrow(source, target, channel)
			else:
				source = graph.nodes[info["source"]]
				target = graph.nodes[info["target"]]

				arrow = UIInternalArrow(source, target)

			arrow.curve = info["curve"]

			graph.arrows.add(arrow)

	def loadPosition(self, obj, data):
		obj.x = data[0]
		obj.y = data[1]

	def loadLabel(self, label, data):
		label.text = data["text"]
		label.angle = data["angle"]
		label.distance = data["distance"]

	def parseObjectRef(self, data):
		type = data["type"]
		id = data["id"]
		if type == "place": return self.places[id]
		if type == "transition": return self.transitions[id]
		if type == "enterprise": return self.enterprises[id]
		raise ValueError("Invalid object type: %s" %type)


class ProjectWriter:
	"""Writes a project to a project file (in our own json-based file format)."""
	def save(self, industry):
		data = {}
		data["places"] = self.savePlaces(industry)
		data["transitions"] = self.saveTransitions(industry)
		data["enterprises"] = self.saveEnterprises(industry)
		data["industry"] = self.saveGraph(industry.graph)
		return data

	def savePlaces(self, industry):
		places = []
		for place in industry.net.places:
			place.id = len(places)
			places.append(place.tokens)
		return places

	def saveTransitions(self, industry):
		transitions = []
		for trans in industry.net.transitions:
			trans.id = len(transitions)
			transitions.append({
				"type": trans.type,
				"message": trans.message
			})
		return transitions

	def saveEnterprises(self, industry):
		enterprises = []
		for node in industry.graph.nodes:
			node.obj.id = len(enterprises)
			enterprise = {
				"net": self.savePetriNet(node.obj.net),
				"graph": self.saveGraph(node.obj.graph)
			}
			enterprises.append(enterprise)
		return enterprises

	def savePetriNet(self, net):
		places = []
		for place in net.places:
			places.append(place.id)
		transitions = []
		for trans in net.transitions:
			transitions.append(trans.id)
		return {
			"places": places,
			"transitions": transitions
		}

	def saveGraph(self, graph):
		nodes = []
		for node in graph.nodes:
			node.id = len(nodes)
			info = self.saveObjectRef(node.obj)
			info["pos"] = self.savePosition(node)
			info["label"] = self.saveLabel(node.label)
			nodes.append(info)

		messages = []
		for arrow in graph.looseArrows.objects:
			if arrow.transition.active:
				arrow.id = len(messages)
				messages.append({
					"node": arrow.node.id,
					"transition": arrow.transition.id,
					"angle": arrow.angle,
					"label": self.saveLabel(arrow.label)
				})

		arrows = []
		for arrow in graph.arrows:
			info = {
				"source": arrow.source.id,
				"target": arrow.target.id,
				"curve": arrow.curve
			}
			if isinstance(arrow, UIChannelArrow):
				info["channel"] = arrow.channel.id
			arrows.append(info)

		return {
			"nodes": nodes,
			"arrows": arrows,
			"looseArrows": messages
		}

	def savePosition(self, obj):
		return [obj.x, obj.y]

	def saveLabel(self, label):
		return {
			"text": label.text,
			"angle": label.angle,
			"distance": label.distance
		}

	def saveObjectRef(self, obj):
		return {
			"type": self.getObjectType(obj),
			"id": obj.id
		}

	def getObjectType(self, obj):
		if isinstance(obj, Place): return "place"
		if isinstance(obj, Transition): return "transition"
		if isinstance(obj, UIPetriNet): return "enterprise"
		raise ValueError("This should never happen")


class Project:
	filename = Property("filenameChanged")
	unsaved = Property("unsavedChanged", False)

	def __init__(self):
		self.filenameChanged = Signal()
		self.unsavedChanged = Signal()

		self.industry = UIPetriNet()
		self.industry.changed.connect(self.setUnsaved)

		self.reader = ProjectReader()
		self.writer = ProjectWriter()

		self.exportname = ""

	def setFilename(self, filename): self.filename = filename
	def setExportname(self, exportname): self.exportname = exportname
	def setUnsaved(self, unsaved=True): self.unsaved = unsaved

	def load(self, filename):
		with open(filename) as f:
			data = json.load(f)

		self.industry = self.reader.load(data)
		self.industry.changed.connect(self.setUnsaved)

		self.setFilename(filename)
		self.setUnsaved(False)

	def save(self, filename):
		data = self.writer.save(self.industry)
		with open(filename, "w") as f:
			json.dump(data, f)

		self.setFilename(filename)
		self.setUnsaved(False)

	def export(self, exportname):
		writer = PNMLWriter(self.industry.net, self.industry.graph)
		file = QFile(exportname)
		if file.open(QIODevice.WriteOnly):
			stream = writer.save(file)
