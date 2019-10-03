
from base import Object, ObjectList, Node
from petri import PetriNet, Transition, Place


class NetInput(Transition):
	def __init__(self, net=None, x=0, y=0, messageType=None):
		super().__init__(net=net, x=x, y=y)
		self.messageType = messageType
		self.message = None


class NetOutput(NetInput):
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


class EnterpriseNet(Node):
	def __init__(self, industryNet):
		super().__init__(net=industryNet)
		self.industryNet = industryNet

		self.netInputs = ObjectList(self, NetInput)
		self.netOutputs = ObjectList(self, NetOutput)

		self.petriNet = PetriNet()

	def addInput(self, netInput):
		self.petriNet.transitions.add(netInput)
		self.netInputs.add(netInput)

	def addOutput(self, netOutput):
		self.petriNet.transitions.add(netOutput)
		self.netOutputs.add(netOutput)


class IndustryNet():
	def __init__(self):
		self.changed = Signal()

		self.enterprises = ObjectList(self, EnterpriseNet)
		self.messages = ObjectList(self, Message)
