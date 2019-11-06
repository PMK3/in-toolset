
from .base import Object, ObjectList, PetriNet, Transition, Place
from common import Signal, Property
import math


class TransitionType:
	INTERNAL = 0
	INPUT = 1
	OUTPUT = 2

class UITransition(Transition):
	type = Property("typeChanged", TransitionType.INTERNAL)
	message = Property("messageChanged", "")
	channel = Property("channelChanged", None)
	
	def __init__(self):
		super().__init__()
		self.typeChanged = Signal()
		self.typeChanged.connect(self.changed)
		self.messageChanged = Signal()
		self.messageChanged.connect(self.changed)
		self.channelChanged = Signal()
		self.channelChanged.connect(self.changed)
		
	def setType(self, type): self.type = type
	def setMessage(self, message): self.message = message
	def setChannel(self, channel): self.channel = channel


# Subclassed by: UILabel, UINode, UILooseArrow
class UIObject(Object):
	x = Property("positionChanged", 0)
	y = Property("positionChanged", 0)
	
	def __init__(self):
		super().__init__()
		self.positionChanged = Signal()
		self.positionChanged.connect(self.changed)
		
	def move(self, x, y):
		self.x = x
		self.y = y


class UILabel(UIObject):
	text = Property("textChanged", "")
	angle = Property("angleChanged", math.pi / 2)
	distance = Property("distanceChanged", 35)
	
	def __init__(self):
		super().__init__()
		self.textChanged = Signal()
		self.angleChanged = Signal()
		self.distanceChanged = Signal()
		
		self.textChanged.connect(self.changed)
		self.angleChanged.connect(self.changed)
		self.distanceChanged.connect(self.changed)
		
	def setText(self, text): self.text = text
	def setAngle(self, angle): self.angle = angle
	def setDistance(self, dist): self.distance = dist


# Holds UIPetriNet, UITransition or Place 
class UINode(UIObject):
	def __init__(self, obj):
		super().__init__()
		self.obj = obj
		self.obj.changed.connect(self.changed)
		self.obj.deleted.connect(self.delete)

		self.label = UILabel()
		self.deleted.connect(self.label.delete)
		self.deleted.connect(self.obj.delete)
		
		self.positionChanged.connect(self.updateLabel)
		
	def updateLabel(self):
		self.label.move(self.x, self.y)
		
		
# Arrow between instances of UILooseArrow or UINode
class UIArrow(Object):
	curve = Property("curveChanged", 0)
	
	def __init__(self, source, target):
		super().__init__()
		self.source = source
		self.target = target
		
		source.deleted.connect(self.delete)
		target.deleted.connect(self.delete)
		
		self.curveChanged = Signal()
		self.curveChanged.connect(self.changed)
		
	def setCurve(self, curve): self.curve = curve
		

# Arrow between instances of UINode (enterprise)
class UIInternalArrow(UIArrow):
	def __init__(self, source, target):
		super().__init__(source, target)
		
		source.obj.connect(target.obj)
		
		self.deleted.connect(self.disconnect)
		
	def disconnect(self):
		self.source.obj.disconnect(self.target.obj)
	
	
# Arrow between instances of UILooseArrow (industry)
class UIChannelArrow(UIArrow):
	def __init__(self, source, target, channel):
		super().__init__(source, target)
		
		self.channel = channel
		self.channel.deleted.connect(self.delete)
		self.deleted.connect(self.channel.delete)
		self.deleted.connect(self.unregister)
		
		source.transition.setChannel(self.channel)
		target.transition.setChannel(self.channel)
		
		self.channel.connect(target.transition)
		source.transition.connect(self.channel)
		
	def unregister(self):
		self.source.transition.setChannel(None)
		self.target.transition.setChannel(None)
		
		
# Message arrow around UINode
# Belongs to a UITransition
class UILooseArrow(UIObject):
	angle = Property("angleChanged", math.pi)
	
	def __init__(self, node, transition):
		super().__init__()
		self.angleChanged = Signal()
		self.angleChanged.connect(self.updatePos)
		
		self.node = node
		self.node.positionChanged.connect(self.updatePos)
		self.node.deleted.connect(self.delete)
		
		self.transition = transition
		self.transition.messageChanged.connect(self.updateText)
		self.transition.typeChanged.connect(self.updateType)
		self.transition.deleted.connect(self.delete)
		
		self.label = UILabel()
		self.label.distance = 15
		self.label.textChanged.connect(self.updateMessage)
		self.deleted.connect(self.label.delete)
		self.restored.connect(self.label.restore)
		
		self.deleted.connect(self.unregister)
		
		self.updatePos()
		self.updateText()
		self.updateType()
	
	def setAngle(self, angle): self.angle = angle

	def unregister(self):
		self.transition.setType(TransitionType.INTERNAL)
		
	def updateType(self):
		if self.transition.type == TransitionType.INTERNAL:
			self.delete()
		else:
			self.restore()
		
	def updatePos(self):
		x = self.node.x + math.cos(self.angle) * 40
		y = self.node.y + math.sin(self.angle) * 40
		self.move(x, y)
		self.label.move(x, y)
		
	def updateMessage(self):
		self.transition.setMessage(self.label.text)
	
	def updateText(self):
		self.label.setText(self.transition.message)

		
# Graph with UINode, UIArrow and UILooseArrow objects
class UIGraph(Object):
	def __init__(self):
		super().__init__()
		
		self.nodes = ObjectList()
		self.nodes.changed.connect(self.changed)
		
		self.arrows = ObjectList()
		self.arrows.changed.connect(self.changed)
		
		self.looseArrows = ObjectList()
		self.looseArrows.changed.connect(self.changed)
		
		
# Petri net with graph
class UIPetriNet(Object):
	def __init__(self):
		super().__init__()
		
		self.net = PetriNet()
		self.net.changed.connect(self.changed)
		
		self.graph = UIGraph()
		self.graph.changed.connect(self.changed)
