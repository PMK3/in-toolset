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
		self.places[placeId].output = transitionId
		self.transitions[transitionId].input = placeId

	def addArrowTransitionToPlace(self, transitionId, placeId):
		self.places[placeId].output = transitionId
		self.transitions[transitionId].input = placeId
