
from petri.petri import Transition
from common import Signal, Property
import math
		
		
class TransitionType:
	INTERNAL = 0
	INPUT = 1
	OUTPUT = 2


class EnterpriseTransition(Transition):
	type = Property("typeChanged", TransitionType.INTERNAL)
	message = Property("messageChanged", "")
	arrowAngle = Property("arrowChanged", math.pi)
	
	def __init__(self, x, y):
		super().__init__(x, y)
		self.typeChanged = Signal()
		self.messageChanged = Signal()
		self.arrowChanged = Signal()
		
	def setType(self, type): self.type = type
	def setMessage(self, message): self.message = message
	def setArrowAngle(self, angle): self.arrowAngle = angle
