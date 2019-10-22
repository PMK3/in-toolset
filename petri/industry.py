
from petri.base import ObjectList, Node, Object
from petri.petri import PetriNet, Transition
from common import Signal, Property
import random
import math


ENTERPRISES = [
	"Petrochem",
	"SovOil",
	"Militech",
	"Arasaka",
	"Biotechnica",
	"Orbital Air",
	"TK Heavy",
	"YoYoDyne Systems",
	"ECorp",
	"Seburo",
	"Genesis Andross",
	"Kuromatsu Electrics",
	"Rossini Air Line",
	"Kenbishi Heavy Industries",
	"Toyoda Chemicals",
	"Armali Council",
	"Blackstone Enterprises",
	"Chronoarcheology Ltd.",
	"Cyberdyne systems",
	"Darkside Services",
	"Empathix",
	"Gaia, Inc,",
	"Soylent Corporation",
	"Multi-National United",
	"Meditech Corp"
]


class TransitionType:
	INTERNAL = 0
	INPUT = 1
	OUTPUT = 2


class EnterpriseTransition(Transition):
	type = Property("typeChanged", TransitionType.INTERNAL)
	message = Property("messageChanged", None)
	messageType = Property("messageTypeChanged", "")
	arrowAngle = Property("arrowChanged", math.pi)
	industryAngle = Property("industryArrowChanged", math.pi)
	
	def __init__(self, x, y):
		super().__init__(x, y)
		self.typeChanged = Signal()
		self.messageTypeChanged = Signal()
		self.messageChanged = Signal()
		self.arrowChanged = Signal()
		self.industryArrowChanged = Signal()
		
	def setType(self, type): self.type = type
	def setMessageType(self, messageType): self.messageType = messageType
	def setArrowAngle(self, angle): self.arrowAngle = angle
	def setIndustryAngle(self, angle): self.industryAngle = angle
	def setMessage(self, message): self.message = message

	def pushMessageType(self):
		if self.message:
			if self.type == TransitionType.INPUT and self.message.output:
				self.message.output.messageType = self.messageType
			if self.type == TransitionType.OUTPUT and self.message.input:
				self.message.input.messageType = self.messageType


class Message(Object):
	def __init__(self, input, output):
		super().__init__()
		self.input = input
		self.output = output
		self.input.deleted.connect(self.delete)
		self.output.deleted.connect(self.delete)


class EnterpriseNode(Node):
	def __init__(self, x, y):
		super().__init__(x, y)
		self.label = random.choice(ENTERPRISES)

		self.net = PetriNet()
		self.net.changed.connect(self.changed)


class IndustryNet:
	def __init__(self):
		self.changed = Signal()

		self.enterprises = ObjectList()
		self.messages = ObjectList()
		
		self.enterprises.changed.connect(self.changed)
		self.messages.changed.connect(self.changed)

	def canConnect(self, input, output):
		if not (input.type == TransitionType.INPUT and output.type == TransitionType.OUTPUT):
			return False
		if not input.messageType == output.messageType:
			return False
		#if input.net == output.net:
		#	return False
		return True

	def connect(self, input, output):
		if not self.canConnect(input, output):
			raise ValueError("Invalid transitions")
		message = Message(input, output)

		input.message = message
		output.message = message

		input.messageTypeChanged.connect(lambda: message.active and input.pushMessageType())
		output.messageTypeChanged.connect(lambda: message.active and output.pushMessageType())

		message.deleted.connect(lambda: message.output.setMessage(None))
		message.deleted.connect(lambda: message.input.setMessage(None))

		self.messages.add(message)
