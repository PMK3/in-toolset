
from petri.petri import PetriNet, Place, Transition, Arrow, ArrowType
from petri.industry import IndustryNet, EnterpriseNode, EnterpriseTransition, TransitionType
from common import Signal, Property
import json


class ProjectReader:
	def __init__(self, net):
		self.net = net
		
	def load(self, data):
		for info in data["enterprises"]:
			enterprise = self.loadEnterprise(info)
			self.net.enterprises.add(enterprise, info["id"])
		for info in data["messages"]:
			self.loadMessage(info)
			
	def loadEnterprise(self, info):
		node = EnterpriseNode(info["x"], info["y"])
		self.loadPetriNet(info["net"], node.net, node)
		self.readNode(node, info)
		return node

	def loadMessage(self, info):
		input = self.net.enterprises[info["inputEnterpriseId"]].net.transitions[info["inputTransitionId"]]
		output = self.net.enterprises[info["outputEnterpriseId"]].net.transitions[info["outputTransitionId"]]
		if self.net.canConnect(input, output):
			self.net.connect(input, output)
		
	def loadPetriNet(self, data, net, node=None):
		if node is not None:
			net.node = node

		for info in data["places"]:
			place = self.loadPlace(info)
			net.places.add(place, info["id"])

		for info in data["transitions"]:
			transition = self.loadTransition(info, node)
			net.transitions.add(transition, info["id"])
			
		for info in data["inputs"]:
			arrow = self.loadArrow(net, info, ArrowType.INPUT)
			net.inputs.add(arrow, info["id"])
			
		for info in data["outputs"]:
			arrow = self.loadArrow(net, info, ArrowType.OUTPUT)
			net.outputs.add(arrow, info["id"])
			
	def loadPlace(self, info):
		place = Place(info["x"], info["y"])
		place.tokens = info["tokens"]
		self.readNode(place, info)
		return place
		
	def loadTransition(self, info, node):
		if node is not None:
			trans = EnterpriseTransition(info["x"], info["y"], node)
			trans.type = info["type"]
			trans.arrowAngle = info["arrowAngle"]
			trans.industryAngle = info["industryAngle"]
			trans.messageType = info["messageType"]
		else :
			trans = Transition(info["x"], info["y"])

		self.readNode(trans, info)
		return trans
		
	def loadArrow(self, net, info, type):
		place = net.places[info["place"]]
		transition = net.transitions[info["transition"]]
		arrow = Arrow(type, place, transition)
		return arrow
		
	def readNode(self, node, info):
		node.label = info["label"]
		node.labelAngle = info["labelAngle"]
		node.labelDistance = info["labelDistance"]
		
		
class ProjectWriter:
	def __init__(self, net):
		self.net = net
		
	def save(self):
		enterprises = [self.saveEnterprise(e) for e in self.net.enterprises]
		messages = [self.saveMessage(m) for m in self.net.messages]
		return {
			"enterprises": enterprises,
			"messages": messages
		}
	
	def saveEnterprise(self, enterprise):
		data = self.saveNode(enterprise)
		data["net"] = self.savePetriNet(enterprise.net)
		return data
		
	def savePetriNet(self, net):
		places = [self.savePlace(p) for p in net.places]
		transitions = [self.saveTransition(t) for t in net.transitions]
		inputs = [self.saveArrow(a) for a in net.inputs]
		outputs = [self.saveArrow(a) for a in net.outputs]
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
		data = self.saveNode(transition)
		if isinstance(transition, EnterpriseTransition):
			data["type"] = transition.type
			data["messageType"] = transition.messageType
			data["arrowAngle"] = transition.arrowAngle
			data["industryAngle"] = transition.industryAngle
		return data
		
	def saveArrow(self, arrow):
		data = self.saveObject(arrow)
		data["place"] = arrow.place.id
		data["transition"] = arrow.transition.id
		return data

	def saveMessage(self, message):
		data = self.saveObject(message)
		data["inputTransitionId"] = message.input.id
		data["inputEnterpriseId"] = message.input.enterpriseNode.id
		data["outputTransitionId"] = message.output.id
		data["outputEnterpriseId"] = message.output.enterpriseNode.id
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
		
		self.industry = IndustryNet()
		self.industry.changed.connect(self.setUnsaved)

	def setFilename(self, filename): self.filename = filename
	def setUnsaved(self, unsaved=True): self.unsaved = unsaved

	def load(self, filename):
		with open(filename) as f:
			data = json.load(f)
			
		reader = ProjectReader(self.industry)
		reader.load(data)

		self.setFilename(filename)
		self.setUnsaved(False)

	def save(self, filename):
		writer = ProjectWriter(self.industry)
		
		data = writer.save()
		with open(filename, "w") as f:
			json.dump(data, f, indent="\t")
			
		self.setFilename(filename)
		self.setUnsaved(False)
