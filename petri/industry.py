
from petri.base import ObjectList, Node
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
	messageType = Property("messageTypeChanged", "")
	arrowAngle = Property("arrowChanged", math.pi)
	industryAngle = Property("industryArrowChanged", math.pi)
	
	def __init__(self, x, y):
		super().__init__(x, y)
		self.typeChanged = Signal()
		self.messageTypeChanged = Signal()
		self.arrowChanged = Signal()
		self.industryArrowChanged = Signal()
		
	def setType(self, type): self.type = type
	def setMessageType(self, messageType): self.messageType = messageType
	def setArrowAngle(self, angle): self.arrowAngle = angle
	def setIndustryAngle(self, angle): self.industryAngle = angle



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
