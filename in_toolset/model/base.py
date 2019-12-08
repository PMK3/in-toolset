
from in_toolset.common import Signal, Property
import random


class Object:
	active = Property("statusChanged", True)

	def __init__(self):
		self.changed = Signal()
		self.deleted = Signal()
		self.restored = Signal()

		self.statusChanged = Signal()
		self.statusChanged.connect(self.changed)
		self.statusChanged.connect(self.notifyState)

		self.id = None

	def notifyState(self):
		if self.active:
			self.restored.emit()
		else:
			self.deleted.emit()

	def delete(self):
		self.active = False

	def restore(self):
		self.active = True


class ObjectList:
	def __init__(self):
		self.changed = Signal()
		self.added = Signal()
		self.removed = Signal()

		self.objects = []

	def __repr__(self):
		return repr(self.objects)

	def __len__(self):
		return sum(obj.active for obj in self.objects)

	def __getitem__(self, index):
		return self.objects[index]

	def __iter__(self):
		return (obj for obj in self.objects if obj.active)

	def index(self, index):
		return self.objects.index(index)

	def add(self, obj):
		obj.changed.connect(self.changed)
		obj.statusChanged.connect(self.updateStatus, obj)
		self.objects.append(obj)
		if obj.active:
			self.added.emit(obj)
			self.changed.emit()

	def remove(self, obj):
		obj.changed.disconnect(self.changed)
		obj.statusChanged.disconnect(self.updateStatus, obj)
		self.objects.remove(obj)
		if obj.active:
			self.removed.emit(obj)
			self.changed.emit()

	def updateStatus(self, obj):
		if obj.active:
			self.added.emit(obj)
		else:
			self.removed.emit(obj)


class Node(Object):
	def __init__(self):
		super().__init__()
		self.preset = ObjectList()
		self.postset = ObjectList()

	def connect(self, target):
		self.postset.add(target)
		target.preset.add(self)
		self.changed.emit()

	def disconnect(self, target):
		self.postset.remove(target)
		target.preset.remove(self)
		self.changed.emit()


class Place(Node):
	tokens = Property("tokensChanged", 0)

	def __init__(self):
		super().__init__()
		self.tokensChanged = Signal()
		self.tokensChanged.connect(self.changed)

	def setTokens(self, tokens): self.tokens = tokens

	def take(self): self.tokens -= 1
	def give(self): self.tokens += 1


class Transition(Node):
	enabled = Property("enabledChanged", True)

	def __init__(self):
		super().__init__()
		self.enabledChanged = Signal()
		self.enabledChanged.connect(self.changed)

		self.triggered = Signal()

		self.preset.changed.connect(self.updateEnabled)
		self.postset.changed.connect(self.updateEnabled)

	def checkEnabled(self):
		for place in self.preset:
			if place.tokens == 0:
				return False
		return True

	def updateEnabled(self):
		self.enabled = self.checkEnabled()

	def trigger(self):
		for place in self.preset:
			place.take()
		for place in self.postset:
			place.give()
		self.triggered.emit()


class PetriNet(Object):
	deadlock = Property("deadlockChanged", True)

	def __init__(self):
		super().__init__()

		self.deadlockChanged = Signal()
		self.triggered = Signal()

		self.places = ObjectList()
		self.transitions = ObjectList()
		self.transitions.changed.connect(self.checkDeadlock)
		self.transitions.added.connect(self.registerTransition)
		self.transitions.removed.connect(self.unregisterTransition)

	def registerTransition(self, trans):
		trans.triggered.connect(self.triggered)

	def unregisterTransition(self, trans):
		trans.triggered.disconnect(self.triggered)

	def enabledTransitions(self):
		return [t for t in self.transitions if t.enabled]

	def checkDeadlock(self):
		self.deadlock = len(self.enabledTransitions()) == 0

	def triggerRandom(self):
		random.choice(self.enabledTransitions()).trigger()

	def setInitialMarking(self):
		for place in self.places:
			if len(place.preset) == 0:
				place.tokens = 1
			else:
				place.tokens = 0


	def combine(self, other):
		newSource = Place() # The new global source place.
		leftSource = Place() # The place on the path to self.
		rightSource = Place() # The place on the path to other.

		leftEnabling = Place() # The first transition on the path to self.
		rightEnabling = Place() # The first transition on the path to other.
		leftStart = Place() # The second transition on the path to self.
		rightStart = Place() # The second transition on the path to other.

		newSource.connect(leftEnabling)
		newSource.connect(rightEnabling)
		leftEnabling.connect(leftSource)
		rightEnabling.connect(leftSource)
		leftSource.connect(leftStart)
		rightSource.connect(rightStart)

		# Connect to the old source places.
		for place in self.places:
			if len(place.preset) == 0:
				leftStart.connect(place)
		for place in other.places:
			if len(place.preset) == 0:
				leftStart.connect(place)

		self.places.add(newSource)
		self.places.add(leftSource)
		self.places.add(rightSource)

		self.transitions.add(leftEnabling)
		self.transitions.add(rightEnabling)
		self.transitions.add(leftStart)
		self.transitions.add(rightStart)

		for place in other.places:
			self.places.add(place)
		for transition in other.transitions:
			self.transitions.add(transition)
