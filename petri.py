
from signal import Signal


class Place:
	def __init__(self, name, x, y):
		self.name = name
		self.tokens = 0
		self.input = []
		self.output = []
		self.x = x
		self.y = y

class Transition:
	def __init__(self, name, x, y):
		self.name = name
		self.input = []
		self.output = []
		self.x = x
		self.y = y

class PetriNet:
	def __init__(self):
		self.nextPlaceId = 0
		self.nextTransitionId = 0
		self.places = {}
		self.transitions = {}

	def addPlace(self, name, x, y):
		id = self.nextPlaceId
		self.places[id] = Place(name, x, y)
		self.nextPlaceId += 1
		return id

	def addTransition(self, name, x, y):
		id = self.nextPlaceId
		elf.transitions[id] = Transition(name, x, y)
		self.nextTransitionId += 1
		return id

	def removePlace(self, id):
		del self.places[id]

	def removeTransition(self, id):
		del self.transitions[id]

	def addArrowPlaceToTransition(self, placeId, transitionId):
		self.places[placeId].output += [transitionId]
		self.transitions[transitionId].input += [placeId]

	def addArrowTransitionToPlace(self, transitionId, placeId):
		self.places[placeId].output += [transitionId]
		self.transitions[transitionId].input += [placeId]


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
