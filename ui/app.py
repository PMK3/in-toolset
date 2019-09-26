
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.menu import MenuBar
from ui.view import *
from ui import settings
from signal import Signal
import petri
import math
import sys
import os


class ToolType:
	PLACE = 0
	TRANSITION = 1
	ARROW = 2

	SELECTION = 10
	DRAGGER = 11

class ToolSet:
	OBJECTS = 0
	DRAGGING = 1

ToolbarShapes = {
	ToolType.PLACE: "place",
	ToolType.TRANSITION: "transition",
	ToolType.ARROW: "arrow",

	ToolType.SELECTION: "selection",
	ToolType.DRAGGER: "hand"
}

ToolbarText = {
	ToolType.PLACE: "Place",
	ToolType.TRANSITION: "Transition",
	ToolType.ARROW: "Arrow",

	ToolType.SELECTION: "Select",
	ToolType.DRAGGER: "Move"
}

ToolbarTooltips = {
	ToolType.PLACE: "Place (P)",
	ToolType.TRANSITION: "Transition (T)",
	ToolType.ARROW: "Arrow (A)",

	ToolType.SELECTION: "Selection tool (S)",
	ToolType.DRAGGER: "Hand drag tool (M)"
}

ToolbarShortcuts = {
	Qt.Key_P: ToolType.PLACE,
	Qt.Key_T: ToolType.TRANSITION,
	Qt.Key_A: ToolType.ARROW,

	Qt.Key_S: ToolType.SELECTION,
	Qt.Key_M: ToolType.DRAGGER
}

ToolbarButtons = {
	ToolSet.OBJECTS: [ToolType.PLACE, ToolType.TRANSITION, ToolType.ARROW],
	ToolSet.DRAGGING: [ToolType.SELECTION, ToolType.DRAGGER]
}

ToolbarHeaders = {
	ToolSet.OBJECTS: "mouseright",
	ToolSet.DRAGGING: "mouseleft"
}

ToolbarGroups = [ToolSet.DRAGGING, ToolSet.OBJECTS]


class NodeType:
	PLACE = 0
	TRANSITION = 1

NodeShapes = {
	NodeType.PLACE: "place",
	NodeType.TRANSITION: "transition",
}

NodeTools = {
	ToolType.PLACE: NodeType.PLACE,
	ToolType.TRANSITION: NodeType.TRANSITION
}


class ToolButton(QToolButton):
	def __init__(self, style, type):
		super().__init__()
		self.setToolTip(ToolbarTooltips[type])

		self.setFixedWidth(80)
		self.setFixedHeight(80)
		self.setCheckable(True)
		self.shape = style.shapes[ToolbarShapes[type]]
		self.text = ToolbarText[type]
		self.type = type

		self.font = QFont()
		self.font.setPixelSize(16)
		self.textRect = QRectF(0, 55, 80, 20)

		self.clicked.connect(lambda: self.setChecked(True))

	def paintEvent(self, e):
		super().paintEvent(e)
		
		painter = QPainter()
		painter.begin(self)
		
		painter.translate(40, 30)
		self.shape.draw(painter)
		painter.resetTransform()

		painter.setFont(self.font)
		painter.drawText(self.textRect, Qt.AlignCenter, self.text)

		painter.end()
		
		
class ToolBarHeader(QWidget):
	def __init__(self, style, type):
		super().__init__()
		self.setMinimumWidth(40)
		self.setMinimumHeight(40)
		self.shape = style.shapes[ToolbarHeaders[type]]
		self.orientation = Qt.Vertical
		
	def setOrientation(self, orientation):
		self.orientation = orientation
		self.update()
		
	def paintEvent(self, e):
		super().paintEvent(e)
		
		painter = QPainter()
		painter.begin(self)
		
		painter.save()
		
		if self.orientation == Qt.Horizontal:
			gradient = QLinearGradient(0, 0, self.width(), 0)
		else:
			gradient = QLinearGradient(0, 0, 0, self.height())
		gradient.setColorAt(0, QColor(160, 160, 160))
		gradient.setColorAt(1, QPalette().color(QPalette.Window))
		
		painter.setPen(Qt.NoPen)
		painter.setBrush(gradient)
		painter.drawRect(self.rect())
		
		painter.restore()
		
		painter.translate(self.rect().center())
		self.shape.draw(painter)
		
		painter.end()


class ToolBar(QToolBar):
	def __init__(self, style):
		super().__init__()
		self.selectionChanged = Signal()

		self.setFloatable(False)

		self.groups = {}
		self.buttons = {}

		for groupType in ToolbarGroups:
			header = ToolBarHeader(style, groupType)
			self.orientationChanged.connect(header.setOrientation)
			self.addWidget(header)

			group = QButtonGroup(self)
			group.buttonToggled.connect(self.handleToggled)
			for toolType in ToolbarButtons[groupType]:
				button = ToolButton(style, toolType)
				group.addButton(button)
				self.addWidget(button)
				self.buttons[toolType] = button
			self.groups[groupType] = group

	def handleToggled(self, button, state):
		if state:
			self.selectionChanged.emit(button.type)

	def selectTool(self, type):
		self.buttons[type].setChecked(True)

	def currentTool(self, group):
		button = self.groups[group].checkedButton()
		if button:
			return button.type
		return -1


class GeneralSettings(QWidget):
	def __init__(self, scene):
		super().__init__()
		self.setStyleSheet("font-size: 16px")

		self.label = QLabel("No item selected")
		self.label.setAlignment(Qt.AlignCenter)

		self.layout = QVBoxLayout(self)
		self.layout.addWidget(self.label)
		self.layout.setAlignment(Qt.AlignTop)

	def setSelection(self, items):
		if len(items) == 0:
			self.label.setText("No item selected")
		elif len(items) == 1:
			self.label.setText("1 item selected")
		else:
			self.label.setText("%i items selected" %len(items))


class NodeSettings(QWidget):
	def __init__(self, obj):
		super().__init__()
		self.obj = obj
		self.obj.positionChanged.connect(self.updatePos)

		self.setStyleSheet("font-size: 16px")

		self.x = QLabel("%i" %(obj.x / 20))
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %(obj.y / 20))
		self.y.setAlignment(Qt.AlignRight)
		self.label = QLineEdit(obj.label)
		self.label.setMaxLength(20)
		self.label.textEdited.connect(self.obj.setLabel)

		self.layout = QFormLayout(self)
		self.layout.addRow("X:", self.x)
		self.layout.addRow("Y:", self.y)
		self.layout.addRow("Label:", self.label)

	def updatePos(self):
		self.x.setText("%i" %(self.obj.x / 20))
		self.y.setText("%i" %(self.obj.y / 20))

	def updateLabel(self, label):
		self.label.setText(label)


class SettingsDock(QDockWidget):
	def __init__(self, editor):
		super().__init__("Settings")

		self.setFixedWidth(200)

		self.scene = editor.scene

		self.generalSettings = GeneralSettings(self.scene)

		self.setFeatures(QDockWidget.DockWidgetMovable)
		self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
		self.setWidget(self.generalSettings)

		self.scene.selectionChanged.connect(self.handleSelectionChanged)

	def handleSelectionChanged(self):
		items = self.scene.selectedItems()
		if len(items) == 1 and isinstance(items[0], ActiveNode):
			self.setWidget(self.createWidget(items[0]))
		else:
			self.generalSettings.setSelection(items)
			self.setWidget(self.generalSettings)

	def createWidget(self, item):
		return NodeSettings(item.obj)


class HoverFilter:
	def __init__(self, item):
		self.item = item

	def applyToPen(self, pen):
		if self.item.hover:
			color = pen.color()
			color = QColor(color.rgba() ^ 0x555555)
			pen.setColor(color)

	def applyToBrush(self, brush):
		if self.item.hover:
			color = brush.color()
			color = QColor(color.rgba() ^ 0x555555)
			brush.setColor(color)


class ArrowFilter(HoverFilter):
	def applyToPen(self, pen):
		super().applyToPen(pen)
		if self.item.isSelected():
			pen.setColor(Qt.blue)


class PlacementNode(EditorNode):
	def __init__(self, scene, style, type):
		super().__init__(scene, style.shapes[NodeShapes[type]])
		self.type = type


class LabelItem(EditorObject):
	def __init__(self, scene, obj):
		super().__init__(scene)

		self.dragMode = DragMode.SPECIAL

		self.obj = obj
		self.obj.positionChanged.connect(self.updateLabel)
		self.obj.labelChanged.connect(self.updateLabel)
		self.obj.deleted.connect(self.removeFromScene)

		self.font = QFont()
		self.font.setPixelSize(16)
		self.fontMetrics = QFontMetrics(self.font)

		self.updateLabel()
		
	def delete(self):
		self.obj.setLabel("")
		self.obj.setLabelAngle(math.pi / 2)
		self.obj.setLabelDistance(35)

	def drag(self, pos):
		dx = pos.x() - self.obj.x
		dy = pos.y() - self.obj.y

		dist = math.sqrt(dx * dx + dy * dy)
		dist = min(max(dist, 20), 60)

		self.obj.setLabelAngle(math.atan2(dy, dx))
		self.obj.setLabelDistance(dist)

	def updateLabel(self):
		xoffs = math.cos(self.obj.labelAngle) * self.obj.labelDistance
		yoffs = math.sin(self.obj.labelAngle) * self.obj.labelDistance
		self.setPos(self.obj.x + xoffs, self.obj.y + yoffs)

		self.prepareGeometryChange()
		self.update()

	def boundingRect(self):
		rect = self.fontMetrics.boundingRect(self.obj.label)
		rect.moveCenter(QPoint(0, 0))
		return QRectF(rect.adjusted(-1, -1, 1, 1))

	def paint(self, painter, option, widget):
		if self.isSelected():
			pen = QPen(Qt.blue)
			painter.setPen(pen)

		painter.setFont(self.font)
		painter.drawText(self.boundingRect(), Qt.AlignCenter, self.obj.label)



class ActiveNode(EditorNode):
	def __init__(self, scene, style, type, obj):
		super().__init__(scene, style.shapes[NodeShapes[type]])
		self.type = type

		self.obj = obj
		self.obj.deleted.connect(self.removeFromScene)
		self.obj.positionChanged.connect(self.updatePos)
		self.setPos(obj.x, obj.y)

		self.filter = HoverFilter(self)

	def drag(self, pos):
		pos = alignToGrid(pos)
		self.obj.move(pos.x(), pos.y())

	def delete(self):
		self.obj.delete()

	def updatePos(self):
		self.setPos(self.obj.x, self.obj.y)

	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)

		if self.isSelected():
			painter.save()
			pen = QPen(Qt.blue)
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(self.shp.rect)
			painter.restore()


class ArrowType:
	INPUT = 0
	OUTPUT = 1


class ArrowItem(EditorShape):
	def __init__(self, scene):
		super().__init__(scene)
		self.setZValue(-1)

		self.arrow = ShapeElement(
			"arrow", x1=0, y1=0, x2=0, y2=0, stretch=10
		)

		pen = QPen()
		pen.setCapStyle(Qt.RoundCap)
		pen.setWidth(2)

		part = ShapePart()
		part.setPen(pen)
		part.addElement(self.arrow)

		shape = Shape()
		shape.addPart(part)

		self.setShape(shape)

	def setPoints(self, x1, y1, x2, y2):
		self.arrow.x1 = x1
		self.arrow.y1 = y1
		self.arrow.x2 = x2
		self.arrow.y2 = y2
		self.updateShape()


class PlacementArrow(ArrowItem):
	def __init__(self, scene, source):
		super().__init__(scene)

		self.source = source
		self.setPoints(source.x(), source.y(), source.x(), source.y())

	def drag(self, pos):
		self.setPoints(self.source.x(), self.source.y(), pos.x(), pos.y())


class ActiveArrow(ArrowItem):
	def __init__(self, scene, obj, type):
		super().__init__(scene)

		self.filter = ArrowFilter(self)

		self.type = type

		self.obj = obj
		self.obj.deleted.connect(self.removeFromScene)

		if type == ArrowType.INPUT:
			self.source = self.obj.place
			self.target = self.obj.transition
		else:
			self.source = self.obj.transition
			self.target = self.obj.place

		self.source.positionChanged.connect(self.updateArrow)
		self.target.positionChanged.connect(self.updateArrow)

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


class Editor:
	def __init__(self, style, toolbar):
		self.toolbar = toolbar
		self.style = style

	def setScene(self, scene):
		self.scene = scene

	def setProject(self, project):
		self.scene.clear()
		self.net = project.net
		self.net.places.added.connect(self.addPlace)
		self.net.transitions.added.connect(self.addTransition)
		self.net.inputs.added.connect(self.addInput)
		self.net.outputs.added.connect(self.addOutput)

	def addPlace(self, obj):
		item = ActiveNode(self.scene, self.style, NodeType.PLACE, obj)
		label = LabelItem(self.scene, obj)
		self.scene.addItem(item)
		self.scene.addItem(label)

	def addTransition(self, obj):
		item = ActiveNode(self.scene, self.style, NodeType.TRANSITION, obj)
		label = LabelItem(self.scene, obj)
		self.scene.addItem(item)
		self.scene.addItem(label)

	def addInput(self, obj):
		item = ActiveArrow(self.scene, obj, ArrowType.INPUT)
		self.scene.addItem(item)

	def addOutput(self, obj):
		item = ActiveArrow(self.scene, obj, ArrowType.OUTPUT)
		self.scene.addItem(item)

	def startPlacement(self, pos):
		type = self.toolbar.currentTool(ToolSet.OBJECTS)
		if type in NodeTools:
			self.scene.setHoverEnabled(False)
			item = PlacementNode(self.scene, self.style, NodeTools[type])
			item.drag(pos)
			return item
		elif type == ToolType.ARROW:
			source = self.scene.findItem(pos, ActiveNode)
			if source:
				return PlacementArrow(self.scene, source)

	def finishPlacement(self, pos, item):
		pos = alignToGrid(pos)
		x, y = pos.x(), pos.y()

		if isinstance(item, PlacementNode):
			if not item.invalid:
				if item.type == NodeType.PLACE:
					place = petri.Place(self.net, x, y)
					self.net.places.add(place)
				elif item.type == NodeType.TRANSITION:
					trans = petri.Transition(self.net, x, y)
					self.net.transitions.add(trans)

		elif isinstance(item, PlacementArrow):
			source = item.source
			target = self.scene.findItem(pos, ActiveNode)
			if target and target.type != source.type:
				if target.type == NodeType.TRANSITION:
					arrow = petri.Arrow(self.net, source.obj, target.obj)
					self.net.inputs.add(arrow)
				else:
					arrow = petri.Arrow(self.net, target.obj, source.obj)
					self.net.outputs.add(arrow)

		self.scene.setHoverEnabled(True)


class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setContextMenuPolicy(Qt.PreventContextMenu)

		self.resize(1080, 720)

		style = Style()
		style.load("data/style.json")

		self.toolbar = ToolBar(style)
		self.toolbar.selectTool(ToolType.SELECTION)
		self.toolbar.selectionChanged.connect(self.updateTool)
		self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

		self.editor = Editor(style, self.toolbar)
		self.scene = EditorScene(self.editor)
		self.view = EditorView(self.scene)
		self.editor.setScene(self.scene)
		self.setCentralWidget(self.view)

		settingsDock = SettingsDock(self.editor)
		self.addDockWidget(Qt.RightDockWidgetArea, settingsDock)

		self.createProject()

		menuBar = MenuBar()
		menuBar.file.new.triggered.connect(self.handleNew)
		menuBar.file.open.triggered.connect(self.handleOpen)
		menuBar.file.save.triggered.connect(self.handleSave)
		menuBar.file.saveAs.triggered.connect(self.handleSaveAs)
		menuBar.file.quit.triggered.connect(self.close)
		menuBar.edit.selectAll.triggered.connect(self.scene.selectAll)
		menuBar.edit.setInitialMarking.triggered.connect(self.editor.net.setInitialMarking)
		menuBar.view.showGrid.toggled.connect(self.scene.setGridEnabled)
		menuBar.view.resetCamera.triggered.connect(self.view.resetTransform)
		self.setMenuBar(menuBar)

		self.updateWindowTitle()

	def closeEvent(self, e):
		if self.checkUnsaved():
			e.accept()
		else:
			e.ignore()

	def updateTool(self, tool):
		if tool == ToolType.SELECTION:
			self.view.setHandDrag(False)
		elif tool == ToolType.DRAGGER:
			self.view.setHandDrag(True)

	def keyPressEvent(self, e):
		key = e.key()
		if key in ToolbarShortcuts:
			self.toolbar.selectTool(ToolbarShortcuts[key])

	def updateWindowTitle(self):
		name = self.project.filename
		if name is None:
			name = "untitled"
		self.setWindowTitle("Petri - %s%s" %(name, "*" * self.project.unsaved))

	def createProject(self, filename=None):
		self.project = petri.Project()
		self.project.filenameChanged.connect(self.updateWindowTitle)
		self.project.unsavedChanged.connect(self.updateWindowTitle)
		self.editor.setProject(self.project)

		if filename:
			self.project.load(filename)

		self.updateWindowTitle()

	def checkUnsaved(self):
		if self.project.unsaved:
			msg = "This model has unsaved changes. Do you want to save them?"
			buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
			result = QMessageBox.question(self, "Save changes?", msg, buttons)
			if result == QMessageBox.Save: return self.handleSave()
			elif result == QMessageBox.Discard: return True
			else: return False
		return True

	def handleNew(self):
		if self.checkUnsaved():
			self.createProject()
			return True
		return False

	def handleOpen(self):
		if not self.checkUnsaved():
			return False

		filename, filter = QFileDialog.getOpenFileName(
			self, "Load model", settings.getLastPath(),
			"Workflow model (*.flow);;All files (*.*)"
		)
		if not filename:
			return False

		settings.setLastPath(os.path.dirname(filename))
		self.createProject(filename)
		return True

	def handleSave(self):
		if not self.project.filename:
			return self.handleSaveAs()
		self.project.save(self.project.filename)
		return True

	def handleSaveAs(self):
		filename, filter = QFileDialog.getSaveFileName(
			self, "Save model", settings.getLastPath(),
			"Workflow model (*.flow);;All files (*.*)"
		)
		if not filename:
			return False

		settings.setLastPath(os.path.dirname(filename))
		self.project.save(filename)
		return True


class Application:
	def start(self):
		self.app = QApplication(sys.argv)
		self.window = MainWindow()
		self.window.show()
		self.app.exec()
