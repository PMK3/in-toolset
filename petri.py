
from signal import Signal


class Place:
	def __init__(self, name, x, y):
		self.name = name
		self.tokens = 0
		self.input = []
		self.output = []
		self.x = x
		self.y = y

	def __str__(self):
		return "(name: " + str(self.name) \
			+ ", tokens: " + str(self.tokens) \
			+ ", input: " + str(self.input) \
			+ ", output: " + str(self.output) \
			+ ")"

	__repr__ = __str__

class Transition:
	def __init__(self, name, x, y):
		self.name = name
		self.input = []
		self.output = []
		self.x = x
		self.y = y

	def __str__(self):
		return "(name: " + str(self.name) \
			+ ", input: " + str(self.input) \
			+ ", output: " + str(self.output) \
			+ ")"

	__repr__ = __str__


class PetriNet:
	def __init__(self):
		self.nextPlaceId = 0
		self.nextTransitionId = 0
		self.places = {}
		self.transitions = {}

	def __str__(self):
		return "(places: " + str(self.places) \
			+ ", transitions: " + str(self.transitions) \
			+ ")"

	__repr__ = __str__

	def addPlace(self, name, x, y):
		id = self.nextPlaceId
		self.places[id] = Place(name, x, y)
		self.nextPlaceId += 1
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
		self.setFilename(filename)
		self.setUnsaved(False)
		#TODO: Load petri net from file

	def save(self, filename):
		self.setFilename(filename)
		self.setUnsaved(False)
		#TODO: Write petri net to file
