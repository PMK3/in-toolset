
from enum import Enum, auto
from signal import Signal
import math
import json


class Object:
	def __init__(self, net):
		self.changed = Signal()
		self.deleted = Signal()

		self.net = net
		self.active = True
		self.id = None

	def delete(self):
		if self.active:
			self.active = False
			self.deleted.emit()
			self.changed.emit()

	def load(self, data):
		self.id = data["id"]

	def save(self):
		return {
			"id": self.id
		}

	def similar(self, obj):
		return False


class Node(Object):
	def __init__(self, net, x=0, y=0):
		super().__init__(net)
		self.positionChanged = Signal()
		self.labelChanged = Signal()

		self.x = x
		self.y = y

		self.label = ""
		self.labelAngle = math.pi / 2
		self.labelDistance = 35

	def move(self, x, y):
		self.x = x
		self.y = y
		self.positionChanged.emit()
		self.changed.emit()

	def setLabel(self, label):
		self.label = label
		self.labelChanged.emit()
		self.changed.emit()

	def setLabelAngle(self, angle):
		self.labelAngle = angle
		self.labelChanged.emit()
		self.changed.emit()

	def setLabelDistance(self, dist):
		self.labelDistance = dist
		self.labelChanged.emit()
		self.changed.emit()

	def load(self, data):
		super().load(data)
		self.x = data["x"]
		self.y = data["y"]
		self.label = data["label"]
		self.labelAngle = data["labelAngle"]
		self.labelDistance = data["labelDistance"]

	def save(self):
		data = super().save()
		data["x"] = self.x
		data["y"] = self.y
		data["label"] = self.label
		data["labelAngle"] = self.labelAngle
		data["labelDistance"] = self.labelDistance
		return data


class ObjectList:
	def __init__(self, net, cls):
		self.changed = Signal()
		self.added = Signal()

		self.changed.connect(net.changed.emit)

		self.net = net
		self.cls = cls
		self.objects = {}
		self.nextId = 0

	def __getitem__(self, item):
		return self.objects[item]

	def __iter__(self):
		return [obj for obj in self.objects.values() if obj.active].__iter__()

	def add(self, obj):
		if obj.id in self.objects:
			return

		if any(obj.similar(x) for x in self):
			return

		if obj.id is None:
			obj.id = self.nextId
			self.nextId += 1

		obj.changed.connect(self.changed.emit)

		self.objects[obj.id] = obj
		self.added.emit(obj)
		self.changed.emit()

	def load(self, infos):
		for info in infos:
			obj = self.cls(self.net)
			obj.load(info)
			self.add(obj)
		self.nextId = max(self.objects, default=0) + 1

	def save(self):
		list = []
		for obj in self.objects.values():
			if obj.active:
				list.append(obj.save())
		return list
