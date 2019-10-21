
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from petri.petri import *
from petri.industry import *
from ui.common import *
import config
import math


class ArrowType:
	INPUT = 0
	OUTPUT = 1

class NodeType:
	PLACE = 0
	TRANSITION = 1
	
NodeTypeMap = {
	"place": NodeType.PLACE,
	"transition": NodeType.TRANSITION
}
			

class ArrowFilter:
	def __init__(self, item):
		self.hover = HoverFilter(item)
		self.item = item
		
	def applyToPen(self, pen):
		self.hover.applyToPen(pen)
		if self.item.isSelected():
			pen.setColor(Qt.blue)
			
	def applyToBrush(self, brush): pass
			
			
class TransitionFilter:
	def __init__(self, item):
		self.hover = HoverFilter(item)
		self.item = item
		
	def applyToPen(self, pen):
		self.hover.applyToPen(pen)
	
	def applyToBrush(self, brush):
		if self.item.obj.enabled:
			brush.setColor(Qt.green)
		self.hover.applyToBrush(brush)


class ArrowItem(EditorShape):
	def __init__(self, scene):
		super().__init__(scene)
		self.setZValue(-1)

		self.arrow = ShapeElement(
			"arrow", x1=0, y1=0, x2=0, y2=0, stretch=10
		)

		self.pen = QPen()
		self.pen.setCapStyle(Qt.RoundCap)
		self.pen.setWidth(2)

		part = ShapePart()
		part.setStroke(20)
		part.setPen(self.pen)
		part.addElement(self.arrow)

		shape = Shape()
		shape.addPart(part)

		self.setShape(shape)
		
	def setColor(self, color):
		self.pen.setColor(color)

	def setPoints(self, x1, y1, x2, y2):
		self.arrow.x1 = x1
		self.arrow.y1 = y1
		self.arrow.x2 = x2
		self.arrow.y2 = y2
		self.updateShape()


class TemporaryArrow(ArrowItem):
	def __init__(self, scene, source):
		super().__init__(scene)

		self.source = source
		self.setPoints(source.x(), source.y(), source.x(), source.y())

	def drag(self, param):
		x, y = param.pos.x(), param.pos.y()
		self.setPoints(self.source.x(), self.source.y(), x, y)


class ActiveArrow(ArrowItem):
	def __init__(self, scene, obj, type):
		super().__init__(scene)

		self.filter = ArrowFilter(self)

		self.obj = obj
		self.type = type

		if type == ArrowType.INPUT:
			self.source = self.obj.place
			self.target = self.obj.transition
		else:
			self.source = self.obj.transition
			self.target = self.obj.place

		self.connect(self.obj.deleted, self.removeFromScene)
		self.connect(self.source.positionChanged, self.updateArrow)
		self.connect(self.target.positionChanged, self.updateArrow)

		self.updateArrow()
		
	def delete(self):
		self.obj.delete()

	def updateArrow(self):
		dx = self.target.x - self.source.x
		dy = self.target.y - self.source.y
		angle = math.atan2(dy, dx)

		self.setPoints(
			self.source.x + math.cos(angle) * 30,
			self.source.y + math.sin(angle) * 30,
			self.target.x - math.cos(angle) * 30,
			self.target.y - math.sin(angle) * 30
		)
		
		
class MessageArrow(ArrowItem):
	def __init__(self, scene, obj):
		super().__init__(scene)
		self.filter = HoverFilter(self)
		
		self.dragMode = DragMode.SPECIAL
		
		self.obj = obj
		self.connect(self.obj.positionChanged, self.updateArrow)
		self.connect(self.obj.arrowChanged, self.updateArrow)
		self.connect(self.obj.typeChanged, self.updateType)
		self.connect(self.obj.deleted, self.removeFromScene)
		
		self.setColor(QColor(128, 0, 255))
		
		self.updateType()
		
	def drag(self, param):
		dx = param.mouse.x() - self.obj.x
		dy = param.mouse.y() - self.obj.y
		angle = math.atan2(dy, dx)
		if self.obj.type == TransitionType.OUTPUT:
			angle -= math.pi
		
		self.obj.setArrowAngle(angle)
		
	def updateType(self):
		if self.obj.type == TransitionType.INTERNAL:
			self.hide()
		else:
			self.updateArrow()
			self.show()
		
	def updateArrow(self):
		dist = config.get("ui.message_arrow_distance")
		size = config.get("ui.message_arrow_length")
		
		angle = self.obj.arrowAngle
		if self.obj.type == TransitionType.OUTPUT:
			angle += math.pi
		
		xpos = self.obj.x + math.cos(angle) * dist
		ypos = self.obj.y + math.sin(angle) * dist
		xoffs = math.cos(angle) * size
		yoffs = math.sin(angle) * size
		
		self.setPos(xpos, ypos)
		
		if self.obj.type == TransitionType.INPUT:
			self.setPoints(xoffs, yoffs, 0, 0)
		else:
			self.setPoints(0, 0, xoffs, yoffs)


class PlaceNode(ActiveNode):
	def __init__(self, scene, style, obj):
		super().__init__(scene, style.shapes["place"], obj, NodeType.PLACE)
		self.connect(self.obj.tokensChanged, self.update)
		
		self.font = QFont()
		self.font.setPixelSize(16)
	
	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)
		
		if self.obj.tokens != 0:
			text = str(self.obj.tokens)
			painter.setFont(self.font)
			painter.drawText(self.shp.rect, Qt.AlignCenter, text)

			
class TransitionNode(ActiveNode):
	def __init__(self, scene, style, obj):
		super().__init__(scene, style.shapes["transition"], obj, NodeType.TRANSITION)
		self.connect(self.obj.enabledChanged, self.update)
		self.filter = TransitionFilter(self)
		
		arrow = MessageArrow(scene, obj)
		scene.addItem(arrow)
		
		
class EnterpriseController:
	def __init__(self, style, window):
		self.style = style
		
		self.toolbar = window.toolbar
		self.scene = window.scene
		
		self.net = None
		
	def load(self, net):
		self.net = net

	def startPlacement(self, pos):
		type = self.toolbar.currentTool("enterprise")
		if type in NodeTypeMap:
			self.scene.setHoverEnabled(False)
			shape = self.style.shapes[type]
			item = EditorNode(self.scene, shape)
			item.type = NodeTypeMap[type]
			item.setPos(alignToGrid(pos))
			return item
		elif type == "arrow":
			source = self.scene.findItem(pos, ActiveNode)
			if source:
				return TemporaryArrow(self.scene, source)

	def finishPlacement(self, pos, item):
		if isinstance(item, EditorNode):
			pos = alignToGrid(pos)
			x, y = pos.x(), pos.y()
			
			if not item.invalid:
				if item.type == NodeType.PLACE:
					place = Place(x, y)
					self.net.places.add(place)
				elif item.type == NodeType.TRANSITION:
					trans = EnterpriseTransition(x, y)
					self.net.transitions.add(trans)

		elif isinstance(item, TemporaryArrow):
			source = item.source
			target = self.scene.findItem(pos, ActiveNode)
			if target and target.type != source.type:
				if target.type == NodeType.TRANSITION:
					if target.obj.type != TransitionType.INPUT:
						arrow = Arrow(ArrowType.INPUT, source.obj, target.obj)
						self.net.inputs.add(arrow)
				else:
					if source.obj.type != TransitionType.OUTPUT:
						arrow = Arrow(ArrowType.OUTPUT, target.obj, source.obj)
						self.net.outputs.add(arrow)

		self.scene.setHoverEnabled(True)
		
		
class SeparatorLine(QFrame):
	def __init__(self):
		super().__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)
		
		
class GeneralSettings(QWidget):
	def __init__(self, net):
		super().__init__()
		self.setStyleSheet("font-size: 16px")
		
		self.net = net
		self.net.deadlockChanged.connect(self.updateDeadlock)

		self.label = QLabel("No item selected")
		self.label.setAlignment(Qt.AlignCenter)

		self.triggerRandom = QPushButton("Trigger random")
		self.triggerRandom.setEnabled(not self.net.deadlock)
		self.triggerRandom.clicked.connect(self.net.triggerRandom)

		self.layout = QVBoxLayout(self)
		self.layout.addWidget(self.label)
		self.layout.addWidget(self.triggerRandom)
		self.layout.setAlignment(Qt.AlignTop)
		
	def cleanup(self):
		self.net.deadlockChanged.disconnect(self.updateDeadlock)

	def setSelection(self, items):
		if len(items) == 0:
			self.label.setText("No item selected")
		elif len(items) == 1:
			self.label.setText("1 item selected")
		else:
			self.label.setText("%i items selected" %len(items))
			
	def updateDeadlock(self):
		self.triggerRandom.setEnabled(not self.net.deadlock)

			
class PlaceSettings(QWidget):
	def __init__(self, obj):
		super().__init__()
		self.obj = obj
		self.obj.positionChanged.connect(self.updatePos)
		self.obj.labelChanged.connect(self.updateLabel)
		self.obj.tokensChanged.connect(self.updateTokens)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(obj.x / GRID_SIZE))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(obj.y / GRID_SIZE))
		self.y.setAlignment(Qt.AlignRight)
		self.label = QLineEdit(obj.label)
		self.label.setMaxLength(config.get("ui.max_label_size"))
		self.label.textEdited.connect(self.obj.setLabel)
		self.tokens = QSpinBox()
		self.tokens.setRange(0, 999)
		self.tokens.setValue(obj.tokens)
		self.tokens.valueChanged.connect(self.obj.setTokens)

		self.layout = QFormLayout(self)
		self.layout.addRow("X:", self.x)
		self.layout.addRow("Y:", self.y)
		self.layout.addRow("Label:", self.label)
		self.layout.addRow("Tokens:", self.tokens)
		
	def cleanup(self):
		self.obj.positionChanged.disconnect(self.updatePos)
		self.obj.labelChanged.disconnect(self.updateLabel)
		self.obj.tokensChanged.disconnect(self.updateTokens)

	def updatePos(self):
		self.x.setText("%i" %(self.obj.x / GRID_SIZE))
		self.y.setText("%i" %(self.obj.y / GRID_SIZE))

	def updateLabel(self):
		self.label.setText(self.obj.label)
		
	def updateTokens(self):
		self.tokens.setValue(self.obj.tokens)

		
class TransitionSettings(QWidget):
	def __init__(self, obj):
		super().__init__()
		self.signals = SignalListener()
		
		self.obj = obj
		self.signals.connect(self.obj.positionChanged, self.updatePos)
		self.signals.connect(self.obj.labelChanged, self.updateLabel)
		self.signals.connect(self.obj.enabledChanged, self.updateEnabled)
		self.signals.connect(self.obj.sourceChanged, self.updateSource)
		self.signals.connect(self.obj.sinkChanged, self.updateSink)
		self.signals.connect(self.obj.typeChanged, self.updateType)
		self.signals.connect(self.obj.messageChanged, self.updateMessage)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(obj.x / GRID_SIZE))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(obj.y / GRID_SIZE))
		self.y.setAlignment(Qt.AlignRight)
		self.label = QLineEdit(obj.label)
		self.label.setMaxLength(config.get("ui.max_label_size"))
		self.label.textEdited.connect(self.obj.setLabel)
		self.trigger = QPushButton("Trigger")
		self.trigger.setEnabled(self.obj.enabled)
		self.trigger.clicked.connect(self.obj.trigger)
		self.type = QComboBox()
		self.type.addItems(["Internal", "Input", "Output"])
		self.type.setCurrentIndex(self.obj.type)
		self.type.currentIndexChanged.connect(self.obj.setType)
		self.message = QLineEdit(obj.message)
		self.message.setMaxLength(config.get("ui.max_label_size"))
		self.message.setEnabled(self.obj.type != TransitionType.INTERNAL)
		self.message.textEdited.connect(self.obj.setMessage)
		self.updateSource()
		self.updateSink()

		self.layout = QFormLayout(self)
		self.layout.addRow("X:", self.x)
		self.layout.addRow("Y:", self.y)
		self.layout.addRow("Label:", self.label)
		self.layout.addRow(SeparatorLine())
		self.layout.addRow("Type:", self.type)
		self.layout.addRow("Message:", self.message)
		self.layout.addRow(SeparatorLine())
		self.layout.addRow(self.trigger)
		
	def cleanup(self):
		self.signals.disconnect()

	def updatePos(self):
		self.x.setText("%i" %(self.obj.x / GRID_SIZE))
		self.y.setText("%i" %(self.obj.y / GRID_SIZE))

	def updateLabel(self):
		self.label.setText(self.obj.label)
		
	def updateEnabled(self):
		self.trigger.setEnabled(self.obj.enabled)
		
	def updateSource(self):
		model = self.type.model()
		item = model.item(TransitionType.INPUT)
		item.setEnabled(self.obj.source)
	
	def updateSink(self):
		model = self.type.model()
		item = model.item(TransitionType.OUTPUT)
		item.setEnabled(self.obj.sink)
		
	def updateType(self):
		self.type.setCurrentIndex(self.obj.type)
		self.message.setEnabled(self.obj.type != TransitionType.INTERNAL)
		
	def updateMessage(self):
		self.message.setText(self.obj.message)
		
		
class EnterpriseScene:
	def __init__(self, style, window):
		self.style = style
		self.window = window

		self.selectEnterprise = Signal()
		
		self.controller = EnterpriseController(style, self.window)
		
		self.toolbar = self.window.toolbar
		self.scene = self.window.scene
		self.view = self.window.view
		self.settings = self.window.settings
		
		self.signals = SignalListener()
		
	def load(self, enet):
		self.scene.clear()
		self.view.resetTransform()
		
		self.net = enet.net
		self.signals.connect(self.net.places.added, self.addPlace)
		self.signals.connect(self.net.transitions.added, self.addTransition)
		self.signals.connect(self.net.inputs.added, self.addInput)
		self.signals.connect(self.net.outputs.added, self.addOutput)
		
		for place in self.net.places:
			self.addPlace(place)
		for transition in self.net.transitions:
			self.addTransition(transition)
		for input in self.net.inputs:
			self.addInput(input)
		for output in self.net.outputs:
			self.addOutput(output)

		self.controller.load(enet.net)
		
		self.scene.setController(self.controller)
		self.signals.connect(self.scene.selectionChanged, self.updateSelection)
		
		self.view.setHandDrag(False)
		
		self.toolbar.reset()
		self.toolbar.addGroup("common")
		self.toolbar.addGroup("enterprise")
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
			
	def addPlace(self, obj):
		item = PlaceNode(self.scene, self.style, obj)
		self.scene.addItem(item)

	def addTransition(self, obj):
		item = TransitionNode(self.scene, self.style, obj)
		self.scene.addItem(item)

	def addInput(self, obj):
		item = ActiveArrow(self.scene, obj, ArrowType.INPUT)
		self.scene.addItem(item)

	def addOutput(self, obj):
		item = ActiveArrow(self.scene, obj, ArrowType.OUTPUT)
		self.scene.addItem(item)
		
	def updateSelection(self):
		if self.settings.widget() != self.generalSettings:
			self.settings.widget().cleanup()
		
		items = self.scene.selectedItems()
		widget = self.createSettingsWidget(items)
		self.settings.setWidget(widget)
		
	def createSettingsWidget(self, items):
		filtered = [i for i in items if isinstance(i, ActiveNode)]
		if len(filtered) == 1:
			item = filtered[0]
			if item.type == NodeType.PLACE:
				return PlaceSettings(item.obj)
			return TransitionSettings(item.obj)
		
		self.generalSettings.setSelection(items)
		return self.generalSettings
		
	def updateTool(self, tool):
		if tool == "selection":
			self.view.setHandDrag(False)
		elif tool == "hand":
			self.view.setHandDrag(True)
