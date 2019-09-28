
from common import Signal, Property
import math


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

	def delete(self): self.active = False
	def restore(self): self.active = True


class Node(Object):
	x = Property("positionChanged", 0)
	y = Property("positionChanged", 0)
	label = Property("labelChanged", "")
	labelAngle = Property("labelChanged", math.pi / 2)
	labelDistance = Property("labelChanged", 35)
	
	def __init__(self, x, y):
		super().__init__()
		self.positionChanged = Signal()
		self.positionChanged.connect(self.changed)
		self.labelChanged = Signal()
		self.labelChanged.connect(self.changed)
		
		self.move(x, y)
	
	def move(self, x, y):
		self.x = x
		self.y = y

	def setLabel(self, label): self.label = label
	def setLabelAngle(self, angle): self.labelAngle = angle
	def setLabelDistance(self, dist): self.labelDistance = dist


class ObjectList:
	def __init__(self):
		self.changed = Signal()
		self.added = Signal()

		self.objects = {}
		self.nextId = 0
		
	def __getitem__(self, item):
		return self.objects[item]
		
	def __iter__(self):
		return (obj for obj in self.objects.values() if obj.active)

	def add(self, obj, id=None):
		if id is None:
			id = self.nextId
			self.nextId += 1
		
		obj.id = id

		obj.changed.connect(self.changed)

		self.objects[obj.id] = obj
		self.added.emit(obj)
		self.changed.emit()
		
	def merge(self, list):
		for obj in list:
			self.add(obj)
