
from signal import Signal


class Place:
	def __init__(self, x, y):
		self.tokens = 0
		self.input = []
		self.output = []
		self.x = x
		self.y = y

class Transition:
	def __init__(self, x, y):
		self.input = []
		self.output = []
		self.x = x
		self.y = y

class PetriNet:
	def __init__(self):
		self.places = []
		self.transitions = []

	def addPlace(self, x, y):
		self.places.append(Place(x, y))

	def addTransition(self, x, y):
		self.transitions.append(Transition(x, y))

	def addArrowPlaceToTransition(self, placeId, transitionId):
		self.places[placeId].output += [transitionId]
		self.transitions[transitionId].input +=[placeId]

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
