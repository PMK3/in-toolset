
from signal import Signal
import json


class Place:
	def __init__(self, x=0, y=0, label=""):
		self.x = x
		self.y = y
		self.label = label
		self.tokens = 0
		self.input = []
		self.output = []
		
	def load(self, data):
		self.x = data["x"]
		self.y = data["y"]
		self.label = data["label"]
	
	def save(self):
		return {
			"x": self.x,
			"y": self.y,
			"label": self.label
		}

	def __repr__(self):
		return "(label: " + str(self.label) \
			+ ", tokens: " + str(self.tokens) \
			+ ", input: " + str(self.input) \
			+ ", output: " + str(self.output) \
			+ ")"


class Transition:
	def __init__(self, name, x, y):
		self.name = name
		self.input = []
		self.output = []
		self.x = x
		self.y = y

	def __repr__(self):
		return "(name: " + str(self.name) \
			+ ", input: " + str(self.input) \
			+ ", output: " + str(self.output) \
			+ ")"


class PetriNet:
	def __init__(self):
		self.placeAdded = Signal()
		
		self.nextPlaceId = 0
		self.nextTransitionId = 0
		self.places = {}
		self.transitions = {}

	def __repr__(self):
		return "(places: " + str(self.places) \
			+ ", transitions: " + str(self.transitions) \
			+ ")"
			
	def load(self, data):
		for place in data["places"]:
			obj = Place()
			obj.load(place)
			self.addPlace(obj)
		
	def save(self):
		places = []
		for place in self.places.values():
			places.append(place.save())
		
		data = {
			"places": places
		}
		return data

	def addPlace(self, place):
		id = self.nextPlaceId
		self.places[id] = place
		self.nextPlaceId += 1
		self.placeAdded.emit(place)
		return id

	def addTransition(self, name, x, y):
		id = self.nextTransitionId
		self.transitions[id] = Transition(name, x, y)
		self.nextTransitionId += 1
		return id

	def removePlace(self, id):
		del self.places[id]

	def removeTransition(self, id):
		del self.transitions[id]

	def addArrowPlaceToTransition(self, placeId, transitionId):
		output = self.places[placeId].output
		input = self.transitions[transitionId].input
		if transitionId not in output:
			output.append(transitionId)
		if placeId not in input:
			input.append(placeId)

	def addArrowTransitionToPlace(self, transitionId, placeId):
		output = self.transitions[transitionId].output
		input = self.places[placeId].input
		if placeId not in output:
			output.append(placeId)
		if transitionId not in input:
			input.append(transitionId)

	def removeArrowPlaceToTransition(self, placeId, transitionId):
		output = self.places[placeId].output
		input = self.transitions[transitionId].input
		if transitionId in output:
			output.remove(transitionId)
		if placeId in input:
			input.remove(placeId)

	def removeArrowTransitionToPlace(self, placeId, transitionId):
		output = self.transitions[transitionId].output
		input = self.places[placeId].input
		if placeId in output:
			output.remove(placeId)
		if transitionId in input:
			input.remove(transitionId)


class Project:
	def __init__(self):
		self.filenameChanged = Signal()
		self.unsavedChanged = Signal()

		self.net = PetriNet()
		self.filename = None
		self.unsaved = False

	def setFilename(self, filename):
		if self.filename != filename:
			self.filename = filename
			self.filenameChanged.emit()

	def setUnsaved(self, unsaved):
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
			json.dump(data, f)
		
		self.setFilename(filename)
		self.setUnsaved(False)
