
from ..common import Signal, Property
import random


class Object:
	"""A basic object class, objects can be marked as deleted and have :py:class:`~in_toolset.common.Signal`-typed members to signify deletion or changes"""
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
		"""Mark the object as deleted"""
		self.active = False

	def restore(self):
		"""Mark the object as active"""
		self.active = True


class ObjectList:
	"""A list of objects of the :py:class:`~in_toolset.model.base.Object` class.
	When iterating over an ObjectList, deleted or inactive Objects are filtered out."""
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
		"""Iterate over all active objects in the list"""
		return (obj for obj in self.objects if obj.active)

	def index(self, index):
		return self.objects.index(index)

	def add(self, obj):
		"""Add an object to the list"""
		obj.changed.connect(self.changed)
		obj.statusChanged.connect(self.updateStatus, obj)
		self.objects.append(obj)
		if obj.active:
			self.added.emit(obj)
			self.changed.emit()

	def remove(self, obj):
		"""Remove an item from the list"""
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
	"""A special child class of :py:class:`~in_toolset.model.base.Object`.
	It introduces directional connections between Nodes, which allows for the creation of graphs and the like"""
	def __init__(self):
		super().__init__()
		self.preset = ObjectList()
		self.postset = ObjectList()

	def connect(self, target):
		"""Create an outgoing connection from `self` to `target`"""
		self.postset.add(target)
		target.preset.add(self)
		self.changed.emit()

	def disconnect(self, target):
		"""Remove an outgoing connection from `self` to `target` if present"""
		self.postset.remove(target)
		target.preset.remove(self)
		self.changed.emit()


class Place(Node):
	"""A representation of a place as in petri nets, implemented as a child class of :py:class:`~in_toolset.model.base.Node`.
	Can contain a positive number of uncoloured tokens,
	and can be connected to incoming or outgoing transitions transitions."""
	tokens = Property("tokensChanged", 0)

	def __init__(self):
		super().__init__()
		self.tokensChanged = Signal()
		self.tokensChanged.connect(self.changed)

	def setTokens(self, tokens):
		"""Set the number of tokens in `self` to `tokens`"""
		self.tokens = tokens

	def take(self):
		"""Decrease the number of tokens by 1"""
		self.tokens -= 1

	def give(self):
		"""Increase the number of tokens by 1"""
		self.tokens += 1


class Transition(Node):
	"""A representation of a transition as in petri nets, implemented as a child class of :py:class:`~in_toolset.model.base.Node`.
	Can be connected to an arbitrary number of places."""
	
	enabled = Property("enabledChanged", True) #:The :py:class:`~in_toolset.common.Property` `enabled` shows whether the transition is currently enabled.

	def __init__(self):
		super().__init__()
		self.enabledChanged = Signal()
		self.enabledChanged.connect(self.changed)

		self.triggered = Signal() #:The :py:class:`~in_toolset.common.Signal` `triggered` emits when the transition is triggered

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
		"""Trigger `self`, updating the amount of tokens contained in all connected places"""
		for place in self.preset:
			place.take()
		for place in self.postset:
			place.give()
		self.triggered.emit()


class PetriNet(Object):
	"""A representation of a petrinet, containing places and transitions, implemented as a child class of :py:class:`~in_toolset.model.base.Object`.
	Places and transitions are represented as objects of type :py:class:`~in_toolset.model.base.Place` and :py:class:`~in_toolset.model.base.Transition` , respectively"""
	
	deadlock = Property("deadlockChanged", True) #:The :py:class:`~in_toolset.common.Property` `deadlock` shows whether the petrinet is currently in deadlock. A petrinet is in deadlock if there are no enabled transitions.

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
		"""Trigger a random transition, if possible"""
		random.choice(self.enabledTransitions()).trigger()

	def setInitialMarking(self):
		"""(Re)Set all places in `self` to the default initial marking.
			This default initial marking is defined such that all places without any incoming transitions will contain one token,
			and the others will be empty."""
		for place in self.places:
			if len(place.preset) == 0:
				place.tokens = 1
			else:
				place.tokens = 0


	def combine(self, other):
		"""Merge `other` and `self` into a new PetriNet and return it.
		This allows for bisimulation using LTSmin"""
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
