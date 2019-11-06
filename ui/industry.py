
from model.ui import *
from ui.common import *
from ui.scene import *
from common import *
import config
import random


ENTERPRISE_NAMES = [
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

def randomEnterpriseName():
	return random.choice(ENTERPRISE_NAMES)


class EnterpriseItem(NodeItem):
	def __init__(self, scene, style, obj):
		super().__init__(scene, style.shapes["enterprise"], obj)
		self.connect(self.node.obj.net.triggered, self.flash)


class ChannelArrowItem(ArrowItem):
	def __init__(self, scene, arrow):
		super().__init__(scene, arrow)
		
		self.setType("line")
		
		self.connect(self.arrow.curveChanged, self.updateAngle)
		self.connect(self.arrow.source.node.positionChanged, self.updateAngle)
		self.connect(self.arrow.target.node.positionChanged, self.updateAngle)
		
	def updateAngle(self):
		if self.arrow.active:
			source = self.arrow.source
			target = self.arrow.target
			
			dx = target.node.x - source.node.x
			dy = target.node.y - source.node.y
			length = math.sqrt(dx * dx + dy * dy)
			
			angle1 = math.atan2(dy, dx)
			angle2 = math.atan2(self.arrow.curve, length / 2)
			self.arrow.source.setAngle(angle1 + angle2)
			self.arrow.target.setAngle(angle1 - angle2 + math.pi)


class TemporaryArrowItem(ArrowBase):
	def __init__(self, scene, source):
		super().__init__(scene)

		self.setType("line")

		self.source = source
				
	def setTarget(self, x, y):
		if isinstance(self.source, LooseArrowItem):
			dx = x - self.source.arrow.node.x
			dy = y - self.source.arrow.node.y
			self.source.arrow.setAngle(math.atan2(dy, dx))
		
		sx = self.source.x()
		sy = self.source.y()
		self.setPoints(x, y, sx, sy)

	def drag(self, param):
		self.setTarget(param.mouse.x(), param.mouse.y())


class IndustryController:
	def __init__(self, style, window, industry):
		self.style = style

		self.window = window
		self.toolbar = window.toolbar
		self.scene = window.scene

		self.net = industry.net
		self.graph = industry.graph

	def startPlacement(self, pos):
		type = self.toolbar.currentTool("industry")
		if type == "enterprise":
			self.scene.setHoverEnabled(False)
			item = NodeBase(self.scene, self.style.shapes["enterprise"])
			item.setPos(alignToGrid(pos))
			return item
		elif type == "message":
			obj = self.scene.findItem(pos, EnterpriseItem, LooseArrowItem)
			if obj:
				if isinstance(obj, LooseArrowItem):
					if obj.arrow.transition.channel:
						return
				arrow = TemporaryArrowItem(self.scene, obj)
				arrow.setTarget(pos.x(), pos.y())
				return arrow

	def finishPlacement(self, pos, item):
		if isinstance(item, NodeBase):
			pos = alignToGrid(pos)
			x, y = pos.x(), pos.y()

			if not item.invalid:
				name = randomEnterpriseName()
				
				enterprise = UIPetriNet()
				node = UINode(enterprise)
				node.label.setText(name)
				node.move(x, y)
				self.graph.nodes.add(node)
		
		elif isinstance(item, TemporaryArrowItem):
			sourceItem = item.source
			targetItem = self.scene.findItem(pos, EnterpriseItem, LooseArrowItem)
			if targetItem and targetItem != sourceItem:
				source, target = self.fixTransitions(sourceItem, targetItem)
				
				if self.checkConnection(source, target):
					dx = target.node.x - source.node.x
					dy = target.node.y - source.node.y
					angle = math.atan2(dy, dx)
					
					source.setAngle(angle)
					target.setAngle(angle + math.pi)
					
					channel = Place()
					self.net.places.add(channel)
					
					arrow = UIChannelArrow(source, target, channel)
					self.graph.arrows.add(arrow)

		self.scene.setHoverEnabled(True)
		
	def checkConnection(self, source, target):
		if source.node == target.node:
			QMessageBox.warning(
				self.window, "Loops not allowed",
				"An enterprise may not be connected to itself."
			)
			return False
		
		if source.transition.channel or target.transition.channel:
			QMessageBox.warning(
				self.window, "Already connected",
				"This transition is already connected"
			)
			return False
			
		if not source.transition.message:
			source.transition.message = target.transition.message
		if not target.transition.message:
			target.transition.message = source.transition.message
			
		if source.transition.message != target.transition.message:
			QMessageBox.warning(
				self.window, "Incompatible message type",
				"Only transitions with the same message type can be connected."
			)
			return False
			
		return True
		
	def fixTransitions(self, sourceItem, targetItem):
		if isinstance(sourceItem, EnterpriseItem):
			if isinstance(targetItem, EnterpriseItem):
				source = self.addTransition(sourceItem, TransitionType.OUTPUT)
				target = self.addTransition(targetItem, TransitionType.INPUT)
				return source, target
				
		if isinstance(sourceItem, LooseArrowItem):
			if isinstance(targetItem, LooseArrowItem):
				if targetItem.arrow.transition.type == TransitionType.INPUT:
					return sourceItem.arrow, targetItem.arrow
				return targetItem.arrow, sourceItem.arrow
		
			sourceItem, targetItem = targetItem, sourceItem
		
		if targetItem.arrow.transition.type == TransitionType.INPUT:
			source = self.addTransition(sourceItem, TransitionType.OUTPUT)
			source.transition.message = targetItem.arrow.transition.message
			return source, targetItem.arrow
		
		target = self.addTransition(sourceItem, TransitionType.INPUT)
		target.transition.message = targetItem.arrow.transition.message
		return targetItem.arrow, target
		
	def addTransition(self, target, type):
		enterprise = target.node.obj
		
		transition = UITransition()
		transition.type = type
		self.net.transitions.add(transition)
		enterprise.net.transitions.add(transition)
		
		node = UINode(transition)
		enterprise.graph.nodes.add(node)
		
		arrow = UILooseArrow(node, transition)
		enterprise.graph.looseArrows.add(arrow)
		
		output = UILooseArrow(target.node, transition)
		self.graph.looseArrows.add(output)
		
		return output


class EnterpriseSettings(SettingsWidget):
	def __init__(self, obj):
		super().__init__()
		self.obj = obj
		self.connect(self.obj.positionChanged, self.updatePos)
		self.connect(self.obj.label.textChanged, self.updateLabel)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(obj.x / GRID_SIZE))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(obj.y / GRID_SIZE))
		self.y.setAlignment(Qt.AlignRight)

		self.label = QLineEdit(obj.label.text)
		self.label.setMaxLength(config.get("ui.max_label_size"))
		self.label.textEdited.connect(self.obj.label.setText)

		self.addField("X:", self.x)
		self.addField("Y:", self.y)
		self.addField("Name:", self.label)

	def updatePos(self):
		self.x.setText("%i" %(self.obj.x / GRID_SIZE))
		self.y.setText("%i" %(self.obj.y / GRID_SIZE))

	def updateLabel(self):
		self.label.setText(self.obj.label.text)
		
		
class LooseArrowSettings(SettingsWidget):
	def __init__(self, obj):
		super().__init__()
		self.obj = obj
		self.connect(self.obj.label.textChanged, self.updateType)
		self.connect(self.obj.transition.channelChanged, self.updateEnabled)

		self.setStyleSheet("font-size: 16px")

		self.type = QLineEdit(self.obj.label.text)
		self.type.setMaxLength(config.get("ui.max_label_size"))
		self.type.textEdited.connect(self.obj.label.setText)
		self.type.setEnabled(not self.obj.transition.channel)

		self.addField("Message type:", self.type)

	def updateType(self):
		self.type.setText(self.obj.label.text)
	
	def updateEnabled(self):
		self.type.setEnabled(not self.obj.transition.channel)


class IndustryScene(PetriScene):
	def __init__(self, style, window):
		super().__init__(style, window)
		
		self.enterpriseSelected = Signal()
		
	def load(self, industry):
		self.loadPetriNet(industry)
		
	def registerTools(self, toolbar):
		toolbar.addGroup("industry")
		toolbar.selectTool("enterprise")
		
	def createController(self):
		return IndustryController(self.style, self.window, self.net)
		
	def addNode(self, node):
		item = EnterpriseItem(self.scene, self.style, node)
		item.doubleClicked.connect(lambda: self.enterpriseSelected(node))
		self.scene.addItem(item)

	def addArrow(self, arrow):
		item = ChannelArrowItem(self.scene, arrow)
		self.scene.addItem(item)
		
	def addLooseArrow(self, arrow):
		item = LooseArrowItem(self.scene, self.style, arrow)
		self.scene.addItem(item)

	def createSettingsWidget(self, items):
		classes = (EnterpriseItem, LooseArrowItem)
		filtered = [item for item in items if isinstance(item, classes)]
		if len(filtered) == 1:
			item = filtered[0]
			if isinstance(item, EnterpriseItem):
				return EnterpriseSettings(item.node)
			return LooseArrowSettings(item.arrow)
