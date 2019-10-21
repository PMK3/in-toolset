
from petri.industry import *
from ui.common import *
from common import *
import config


class EnterpriseItem(ActiveNode): pass

class MessageNode(EditorShape):
	def __init__(self, scene, enterprise, transition):
		super().__init__(scene)
		
		self.filter = HoverFilter(self)
		
		self.dragMode = DragMode.SPECIAL
		
		self.enterprise = enterprise
		self.enterprise.positionChanged.connect(self.updatePos)
		self.transition = transition
		self.transition.industryArrowChanged.connect(self.updatePos)
		
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
		
	def disconnect(self):
		self.enterprise.positionChanged.disconnect(self.updatePos)
		self.transition.industryArrowChanged.disconnect(self.updatePos)
		
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

	def finishPlacement(self, pos, item):
		if isinstance(item, EditorNode):
			pos = alignToGrid(pos)
			x, y = pos.x(), pos.y()

			if not item.invalid:
				enterprise = EnterpriseNode(x, y)
				self.net.enterprises.add(enterprise)

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

		for enterprise in self.net.enterprises:
			self.addEnterprise(enterprise)

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
		
		for transition in obj.net.transitions:
			if transition.type != TransitionType.INTERNAL:
				item = MessageNode(self.scene, obj, transition)
				self.scene.addItem(item)

	def updateSelection(self):
		if self.settings.widget() != self.generalSettings:
			self.settings.widget().cleanup()

		items = self.scene.selectedItems()
		widget = self.createSettingsWidget(items)
		self.settings.setWidget(widget)

	def createSettingsWidget(self, items):
		if len(items) == 1 and isinstance(items[0], EnterpriseItem):
			return EnterpriseSettings(items[0].obj, self)

		self.generalSettings.setSelection(items)
		return self.generalSettings

	def updateTool(self, tool):
		if tool == "selection":
			self.view.setHandDrag(False)
		elif tool == "hand":
			self.view.setHandDrag(True)
