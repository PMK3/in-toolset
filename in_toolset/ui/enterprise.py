
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ..model.ui import *
from .common import *
from .scene import *
from .. import config as config
import math


class TransitionFilter:
	def __init__(self, item):
		self.base = NodeFilter(item)
		self.item = item

	def applyToPen(self, pen):
		self.base.applyToPen(pen)

	def applyToBrush(self, brush):
		if self.item.node.obj.enabled:
			brush.setColor(QColor("#c0f6b3"))
		self.base.applyToBrush(brush)


class PlaceItem(NodeItem):
	def __init__(self, scene, style, node):
		super().__init__(scene, style.shapes["place"], node)
		self.connect(self.node.obj.tokensChanged, self.update)

		self.font = QFont()
		self.font.setPixelSize(16)

	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)

		if self.node.obj.tokens != 0:
			text = str(self.node.obj.tokens)
			painter.setFont(self.font)
			painter.drawText(self.shp.rect, Qt.AlignCenter, text)


class TransitionItem(NodeItem):
	def __init__(self, scene, style, node):
		super().__init__(scene, style.shapes["transition"], node)
		self.connect(self.node.obj.enabledChanged, self.update)
		self.connect(self.node.obj.triggered, self.flash)
		self.filter = TransitionFilter(self)


class TemporaryPlace(NodeBase):
	"""A placeholder place to be displayed on the canvas during placement of a place, to show the place of the place currently being placed."""
	def __init__(self, scene, style):
		super().__init__(scene, style.shapes["place"])


class TemporaryTransition(NodeBase):
	"""A placeholder transition to be displayed on the canvas during placement of a transition, to show the place of the transition currently being placed."""
	def __init__(self, scene, style):
		super().__init__(scene, style.shapes["transition"])


class TemporaryArrow(ArrowBase):
	"""A placeholder arrow to be displayed on the canvas during placement of a arrow (while it is being dragged), to show the orientation and place of the arrow currently being placed."""
	def __init__(self, scene, source):
		super().__init__(scene)

		self.source = source

	def setTarget(self, x, y):
		self.setPoints(self.source.x(), self.source.y(), x, y)

	def drag(self, param):
		self.setTarget(param.mouse.x(), param.mouse.y())


class EnterpriseController:
	def __init__(self, style, window, industry, enode):
		self.style = style

		self.window = window
		self.toolbar = window.toolbar
		self.scene = window.scene

		self.industry = industry
		self.enterprise = enode.obj
		self.enode = enode

	def startPlacement(self, pos):
		type = self.toolbar.currentTool("enterprise")
		if type == "place":
			self.scene.setHoverEnabled(False)
			item = TemporaryPlace(self.scene, self.style)
			item.setPos(alignToGrid(pos))
			return item
		elif type == "transition":
			self.scene.setHoverEnabled(False)
			item = TemporaryTransition(self.scene, self.style)
			item.setPos(alignToGrid(pos))
			return item
		elif type == "arrow":
			source = self.scene.findItem(pos, NodeItem)
			if source:
				item = TemporaryArrow(self.scene, source)
				item.setTarget(pos.x(), pos.y())
				return item

	def finishPlacement(self, pos, item):
		if isinstance(item, NodeBase):
			pos = alignToGrid(pos)
			x, y = pos.x(), pos.y()

			if not item.invalid:
				if isinstance(item, TemporaryPlace):
					obj = Place()
					self.enterprise.net.places.add(obj)
					self.industry.net.places.add(obj)

					node = UINode(obj)
					node.move(x, y)
					self.enterprise.graph.nodes.add(node)

				else:
					obj = UITransition()
					self.enterprise.net.transitions.add(obj)
					self.industry.net.transitions.add(obj)

					node = UINode(obj)
					node.move(x, y)
					self.enterprise.graph.nodes.add(node)

					arrow = UILooseArrow(node, obj)
					arrow.delete()
					self.enterprise.graph.looseArrows.add(arrow)

					arrow = UILooseArrow(self.enode, obj)
					arrow.delete()
					self.industry.graph.looseArrows.add(arrow)

		elif isinstance(item, TemporaryArrow):
			source = item.source
			target = self.scene.findItem(pos, NodeItem)
			if target and target != source:
				if self.checkConnection(source, target):
					arrow = UIInternalArrow(source.node, target.node)
					self.enterprise.graph.arrows.add(arrow)

		self.scene.setHoverEnabled(True)

	def checkConnection(self, source, target):
		if isinstance(source, PlaceItem) and isinstance(target, PlaceItem):
			QMessageBox.warning(
				self.window, "Invalid connection",
				"Places may not be connected to other places."
			)
			return False

		if isinstance(source, TransitionItem) and isinstance(target, TransitionItem):
			QMessageBox.warning(
				self.window, "Invalid connection",
				"Transitions may not be connected to other transitions."
			)
			return False

		if target.node.obj in source.node.obj.postset:
			QMessageBox.warning(
				self.window, "Duplicate arrow",
				"Only one arrow can be placed from one node to another."
			)
			return False

		return True


class PlaceSettings(SettingsWidget):
	def __init__(self, node):
		super().__init__()
		self.node = node
		self.connect(self.node.positionChanged, self.updatePos)
		self.connect(self.node.label.textChanged, self.updateLabel)

		self.obj = node.obj
		self.connect(self.obj.tokensChanged, self.updateTokens)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(self.node.x / GRID_SIZE))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(self.node.y / GRID_SIZE))
		self.y.setAlignment(Qt.AlignRight)
		self.label = QLineEdit(self.node.label.text)
		self.label.setMaxLength(config.get("ui.max_label_size"))
		self.label.textEdited.connect(self.node.label.setText)
		self.tokens = QSpinBox()
		self.tokens.setRange(0, 999)
		self.tokens.setValue(self.obj.tokens)
		self.tokens.valueChanged.connect(self.obj.setTokens)

		self.addField("X:", self.x)
		self.addField("Y:", self.y)
		self.addField("Label:", self.label)
		self.addField("Tokens:", self.tokens)

	def updatePos(self):
		self.x.setText("%i" %(self.node.x / GRID_SIZE))
		self.y.setText("%i" %(self.node.y / GRID_SIZE))

	def updateLabel(self):
		self.label.setText(self.node.label.text)

	def updateTokens(self):
		self.tokens.setValue(self.obj.tokens)


class TransitionSettings(SettingsWidget):
	def __init__(self, node):
		super().__init__()

		self.node = node
		self.obj = node.obj

		self.connect(self.node.positionChanged, self.updatePos)
		self.connect(self.node.label.textChanged, self.updateLabel)
		self.connect(self.obj.enabledChanged, self.updateEnabled)
		self.connect(self.obj.typeChanged, self.updateType)
		self.connect(self.obj.messageChanged, self.updateMessage)
		self.connect(self.obj.channelChanged, self.updateChannel)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(self.node.x / GRID_SIZE))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(self.node.y / GRID_SIZE))
		self.y.setAlignment(Qt.AlignRight)

		self.label = QLineEdit(self.node.label.text)
		self.label.setMaxLength(config.get("ui.max_label_size"))
		self.label.textEdited.connect(self.node.label.setText)

		self.trigger = QPushButton("Trigger")
		self.trigger.setEnabled(self.obj.enabled)
		self.trigger.clicked.connect(self.obj.trigger)

		self.type = QComboBox()
		self.type.addItems(["Internal", "Input", "Output"])
		self.type.setCurrentIndex(self.obj.type)
		self.type.currentIndexChanged.connect(self.obj.setType)

		self.message = QLineEdit(self.obj.message)
		self.message.setMaxLength(config.get("ui.max_label_size"))
		self.message.textEdited.connect(self.obj.setMessage)
		self.updateChannel()

		self.addField("X:", self.x)
		self.addField("Y:", self.y)
		self.addField("Label:", self.label)
		self.addSeparator()
		self.addField("Type:", self.type)
		self.addField("Message Type:", self.message)
		self.addSeparator()
		self.addWidget(self.trigger)

	def updatePos(self):
		self.x.setText("%i" %(self.node.x / GRID_SIZE))
		self.y.setText("%i" %(self.node.y / GRID_SIZE))

	def updateLabel(self):
		self.label.setText(self.node.label.text)

	def updateEnabled(self):
		self.trigger.setEnabled(self.obj.enabled)

	def updateType(self):
		self.type.setCurrentIndex(self.obj.type)
		self.message.setEnabled(
			self.obj.type != TransitionType.INTERNAL and not self.obj.channel
		)

	def updateMessage(self):
		self.message.setText(self.obj.message)

	def updateChannel(self):
		self.type.setEnabled(not self.obj.channel)
		self.message.setEnabled(
			self.obj.type != TransitionType.INTERNAL and not self.obj.channel
		)


class EnterpriseScene(PetriScene):
	def load(self, industry, node):
		self.industry = industry
		self.enterprise = node.obj
		self.enode = node

		self.loadPetriNet(node.obj)

	def registerTools(self, toolbar):
		toolbar.addGroup("enterprise")
		toolbar.selectTool("place")

	def createController(self):
		return EnterpriseController(self.style, self.window, self.industry, self.enode)

	def addNode(self, node):
		if isinstance(node.obj, Place):
			item = PlaceItem(self.scene, self.style, node)
		else:
			item = TransitionItem(self.scene, self.style, node)
		self.scene.addItem(item)

	def addArrow(self, arrow):
		item = ArrowItem(self.scene, arrow)
		item.setDistance(35)
		self.scene.addItem(item)

	def addLooseArrow(self, arrow):
		item = LooseArrowItem(self.scene, self.style, arrow)
		self.scene.addItem(item)

	def createSettingsWidget(self, items):
		filtered = [i for i in items if isinstance(i, NodeItem)]
		if len(filtered) == 1:
			item = filtered[0]
			if isinstance(item, PlaceItem):
				return PlaceSettings(item.node)
			return TransitionSettings(item.node)
