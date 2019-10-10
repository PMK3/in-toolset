
from petri.base import Object, ObjectList, Node
from petri.petri import PetriNet, Transition, Place
from common import Signal
import random


class NetIO(Transition):
	def __init__(self, net=None, x=0, y=0, messageType=None):
		super().__init__(net=net, x=x, y=y)
		self.messageType = messageType
		self.message = None


class NetOutput(NetIO):
	pass

class NetInput(NetIO):
	pass

class Message(Object):
	def __init__(self, input, output):
		super().__init__(self)

		if input.messageType != output.messageType:
			raise ValueError("Cannot connect input to output of different type")
		if input.net == output.net:
			raise ValueError("Cannot connect input to output of same net")

		self.input = input
		self.output = output
		input.message = self
		output.message = self


class EnterpriseNode(Node):
	def __init__(self, x, y):
		super().__init__(x, y)

		self.inputs = ObjectList()
		self.outputs = ObjectList()
		names = [
			"Petrochem",
			"SovOil",
			"Militech",
			"Arasaka",
			"Biotechnica",
			"Orbital Air",
			"TK Heavy",
			"YoYoDyne Systems",
			"ECorp",
			"Hanka Precision Instruments",
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
			"Eschataological Enterprises",
			"Gaia, Inc,",
			"Soylent Corporation",
			"Multi-National United",
			"Meditech Corp"]

		self.label = random.choice(names)

		self.net = PetriNet()
		self.net.changed.connect(self.changed)

	def addInput(self, input):
		self.net.transitions.add(input)
		self.inputs.add(input)

	def addOutput(self, output):
		self.net.transitions.add(output)
		self.outputs.add(output)


class IndustryNet:
	def __init__(self):
		self.changed = Signal()

		self.enterprises = ObjectList()
		self.messages = ObjectList()
		
		self.enterprises.changed.connect(self.changed)
		self.messages.changed.connect(self.changed)
