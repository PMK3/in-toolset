
from petri.industry import *
from ui.common import *
from ui.enterprise import ArrowFilter
from common import *
import config


class EnterpriseItem(ActiveNode): pass

class MessageArrowItem(ArrowItem):
	def __init__(self, scene, obj):
		super().__init__(scene)

		self.filter =  ArrowFilter(self)

		self.dragMode = DragMode.SPECIAL

		self.obj = obj

		self.source = obj.output
		self.target = obj.input

		self.connect(self.obj.deleted, self.removeFromScene)
		self.connect(self.target.deleted, self.removeFromScene)
		self.connect(self.source.deleted, self.removeFromScene)
		self.connect(self.source.enterpriseNode.positionChanged, self.updateArrow)
		self.connect(self.target.enterpriseNode.positionChanged, self.updateArrow)
		self.connect(self.source.industryArrowChanged, self.updateArrow)
		self.connect(self.target.industryArrowChanged, self.updateArrow)

		self.updateArrow()

	def delete(self):
		self.obj.delete()

	def updateArrow(self):
		sourceX = self.source.enterpriseNode.x + math.cos(self.source.industryAngle)*40
		sourceY = self.source.enterpriseNode.y + math.sin(self.source.industryAngle)*40
		targetX = self.target.enterpriseNode.x + math.cos(self.target.industryAngle)*40
		targetY = self.target.enterpriseNode.y + math.sin(self.target.industryAngle)*40

		self.setPoints(
			sourceX,
			sourceY,
			targetX,
			targetY
		)


class TemporaryMessageArrow(ArrowItem):
	def __init__(self, scene, obj):
		super().__init__(scene)

		self.obj = obj
		self.setPoints(obj.x(), obj.y(), obj.x(), obj.y())

		self.fixedInput = False
		if isinstance(obj, MessageNode):
			if obj.transition.type == TransitionType.INPUT:
				self.fixedInput = True
			elif obj.transition.type == TransitionType.OUTPUT:
				self.fixedInput = False
			else:
				raise ValueError("Invalid object")
		elif isinstance(obj, EnterpriseItem):
			self.fixedInput = False
		else:
			raise ValueError("Invalid object")

	def drag(self, param):
		x, y = param.pos.x(), param.pos.y()
		if self.fixedInput:
			self.setPoints(x, y, self.obj.x(), self.obj.y())
		else:
			self.setPoints(self.obj.x(), self.obj.y(), x, y)


class MessageNode(EditorShape):
	def __init__(self, scene, enterprise, transition):
		super().__init__(scene)
		
		self.filter = HoverFilter(self)
		
		self.dragMode = DragMode.SPECIAL
		
		self.enterprise = enterprise
		self.transition = transition
		
		self.connect(self.enterprise.positionChanged, self.updatePos)
		self.connect(self.transition.industryArrowChanged, self.updatePos)
		self.connect(self.enterprise.deleted, self.transition.delete)
		self.connect(self.enterprise.deleted, self.removeFromScene)
		self.connect(self.transition.deleted, self.removeFromScene)
		
		circle = ShapeElement(
			"circle", x=0, y=0, r=8
		)
		
		pen = QPen(Qt.NoPen)
		if self.transition.type == TransitionType.INPUT:
			brush = QBrush(QColor(255, 128, 0))
		else:
			brush = QBrush(Qt.red)
		
		part = ShapePart()
		part.setPen(pen)
		part.setBrush(brush)
		part.addElement(circle)
		
		shape = Shape()
		shape.addPart(part)
		
		self.setShape(shape)
		
		self.updatePos()
		
	def drag(self, param):
		dx = param.pos.x() - self.enterprise.x
		dy = param.pos.y() - self.enterprise.y
		angle = math.atan2(dy, dx)
		
		self.transition.setIndustryAngle(angle)
		
	def updatePos(self):
		angle = self.transition.industryAngle
		posx = self.enterprise.x + math.cos(angle) * 40
		posy = self.enterprise.y + math.sin(angle) * 40
		
		self.setPos(posx, posy)


class IndustryController:
	def __init__(self, style, window):
		self.style = style

		self.toolbar = window.toolbar
		self.scene = window.scene

		self.net = None

	def load(self, net):
		self.net = net

	def startPlacement(self, pos):
		type = self.toolbar.currentTool("industry")
		if type == "enterprise":
			self.scene.setHoverEnabled(False)
			item = EditorNode(self.scene, self.style.shapes["enterprise"])
			item.setPos(alignToGrid(pos))
			return item
		elif type == "message":
			obj = self.scene.findItem(pos, MessageNode)
			if not obj:
				obj = self.scene.findItem(pos, EnterpriseItem)
			if obj:
				return TemporaryMessageArrow(self.scene, obj)


	def finishPlacement(self, pos, item):
		if isinstance(item, EditorNode):
			pos = alignToGrid(pos)
			x, y = pos.x(), pos.y()

			if not item.invalid:
				enterprise = EnterpriseNode(x, y)
				self.net.enterprises.add(enterprise)
		elif isinstance(item, TemporaryMessageArrow):
			if item.fixedInput:
				input = item.obj
				output = self.scene.findItem(pos, (MessageNode,EnterpriseItem))
			else:
				input = self.scene.findItem(pos, (MessageNode,EnterpriseItem))
				output = item.obj

			if (isinstance(input, MessageNode) or isinstance(input, EnterpriseItem)) and (isinstance(output, EnterpriseItem) or isinstance(output, MessageNode)):
				message = None

				if isinstance(input, MessageNode):
					input = input.transition
					message = input.message
				else:
					enterprise = input.obj
					input = EnterpriseTransition(0,0,enterprise)
					input.type = TransitionType.INPUT
					enterprise.net.transitions.add(input)

				if isinstance(output, MessageNode):
					output = output.transition
					if not message or output.message == input.message:
						message = output.message
					else:
						return
				else:
					enterprise = output.obj
					output = EnterpriseTransition(0,0,enterprise)
					output.type = TransitionType.OUTPUT
					output.message = message
					enterprise.net.transitions.add(output)

				if not message:
					message = ""

				input.message = message
				output.message = message

				if input and output and self.net.canConnect(input, output):
					self.net.connect(input, output)

		self.scene.setHoverEnabled(True)


class GeneralSettings(QWidget):
	def __init__(self, net):
		super().__init__()
		self.setStyleSheet("font-size: 16px")

		self.net = net

		self.label = QLabel("No item selected")
		self.label.setAlignment(Qt.AlignCenter)

		self.layout = QVBoxLayout(self)
		self.layout.addWidget(self.label)
		self.layout.setAlignment(Qt.AlignTop)

	def cleanup(self):
		pass

	def setSelection(self, items):
		if len(items) == 0:
			self.label.setText("No item selected")
		elif len(items) == 1:
			self.label.setText("1 item selected")
		else:
			self.label.setText("%i items selected" %len(items))

class MessageNodeSettings(QWidget):
	def __init__(self, obj, industryScene):
		super().__init__()
		self.obj = obj
		self.industryScene = industryScene
		self.obj.transition.messageTypeChanged.connect(self.updateType)

		self.setStyleSheet("font-size: 16px")

		self.type = QLineEdit(obj.transition.messageType)
		self.type.setMaxLength(config.get("ui.max_label_size"))
		self.type.textEdited.connect(self.obj.transition.setMessageType)

		self.layout = QFormLayout(self)
		self.layout.addRow("Message Type:", self.type)

	def cleanup(self):
		self.obj.transition.messageTypeChanged.disconnect(self.updateType)

	def updateType(self):
		self.type.setText(self.obj.transition.messageType)


class EnterpriseSettings(QWidget):
	def __init__(self, obj, industryScene):
		super().__init__()
		self.obj = obj
		self.industryScene = industryScene
		self.obj.positionChanged.connect(self.updatePos)
		self.obj.labelChanged.connect(self.updateLabel)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(obj.x / GRID_SIZE))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(obj.y / GRID_SIZE))
		self.y.setAlignment(Qt.AlignRight)

		self.label = QLineEdit(obj.label)
		self.label.setMaxLength(config.get("ui.max_label_size"))
		self.label.textEdited.connect(self.obj.setLabel)

		self.edit = QPushButton("Edit")
		self.edit.clicked.connect(lambda : self.industryScene.selectEnterprise(obj.id))

		self.layout = QFormLayout(self)
		self.layout.addRow("X:", self.x)
		self.layout.addRow("Y:", self.y)
		self.layout.addRow("Label:", self.label)
		self.layout.addRow(self.edit)

	def cleanup(self):
		self.obj.positionChanged.disconnect(self.updatePos)
		self.obj.labelChanged.disconnect(self.updateLabel)

	def updatePos(self):
		self.x.setText("%i" %(self.obj.x / GRID_SIZE))
		self.y.setText("%i" %(self.obj.y / GRID_SIZE))

	def updateLabel(self):
		self.label.setText(self.obj.label)


class IndustryScene:
	def __init__(self, style, window):
		self.style = style

		self.window = window

		self.controller = IndustryController(style, window)

		self.toolbar = window.toolbar
		self.scene = window.scene
		self.view = window.view
		self.settings = window.settings

		self.selectEnterprise = Signal()
		
		self.signals = SignalListener()

	def load(self, net):
		self.scene.clear()
		self.view.resetTransform()

		self.net = net
		self.signals.connect(self.net.enterprises.added, self.addEnterprise)
		self.signals.connect(self.net.messages.added, self.addMessage)

		for enterprise in self.net.enterprises:
			self.addEnterprise(enterprise)

		for message in self.net.messages:
			self.addMessage(message)

		self.controller.load(net)

		self.scene.setController(self.controller)
		self.signals.connect(self.scene.selectionChanged, self.updateSelection)

		self.view.setHandDrag(False)

		self.toolbar.reset()
		self.toolbar.addGroup("common")
		self.toolbar.addGroup("industry")
		self.toolbar.selectTool("selection")
		self.signals.connect(self.toolbar.selectionChanged, self.updateTool)

		self.generalSettings = GeneralSettings(self.net)
		self.settings.setWidget(self.generalSettings)

	def cleanup(self):
		self.signals.disconnect()

		self.generalSettings.cleanup()
		if self.settings.widget() != self.generalSettings:
			self.settings.widget().cleanup()
		self.scene.cleanup()

	def addEnterprise(self, obj):
		item = EnterpriseItem(self.scene, self.style.shapes["enterprise"], obj)
		item.doubleClicked.connect(lambda: self.window.selectEnterprise(obj.id))
		self.scene.addItem(item)
		self.signals.connect(obj.net.transitions.added, self.addTransition)
		
		for transition in obj.net.transitions:
			self.addTransition(transition)

	def addTransition(self, obj):
		if obj.type != TransitionType.INTERNAL:
			item = MessageNode(self.scene, obj.enterpriseNode, obj)
			self.scene.addItem(item)

	def addMessage(self, obj):
		item = MessageArrowItem(self.scene, obj)
		self.scene.addItem(item)

	def updateSelection(self):
		if self.settings.widget() != self.generalSettings:
			self.settings.widget().cleanup()

		items = self.scene.selectedItems()
		widget = self.createSettingsWidget(items)
		self.settings.setWidget(widget)

	def createSettingsWidget(self, items):
		if len(items) == 1:
			if isinstance(items[0], EnterpriseItem):
				return EnterpriseSettings(items[0].obj, self)
			elif isinstance(items[0], MessageNode):
				return MessageNodeSettings(items[0], self)

		self.generalSettings.setSelection(items)
		return self.generalSettings

	def updateTool(self, tool):
		if tool == "selection":
			self.view.setHandDrag(False)
		elif tool == "hand":
			self.view.setHandDrag(True)
