
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.menu import MenuBar
from ui.view import *
from ui import settings
import petri
import math
import sys
import os


class ObjectType:
	PLACE = 0
	TRANSITION = 1
	ARROW = 2
	
ToolbarShapes = {
	ObjectType.PLACE: "place",
	ObjectType.TRANSITION: "transition",
	ObjectType.ARROW: "arrow"
}

ItemShapes = {
	ObjectType.PLACE: "place",
	ObjectType.TRANSITION: "transition",
}

ToolbarText = {
	ObjectType.PLACE: "Place",
	ObjectType.TRANSITION: "Transition",
	ObjectType.ARROW: "Arrow"
}

ToolbarTooltips = {
	ObjectType.PLACE: "Place (Q)",
	ObjectType.TRANSITION: "Transition (W)",
	ObjectType.ARROW: "Arrow (E)"
}

ToolbarShortcuts = {
	Qt.Key_Q: ObjectType.PLACE,
	Qt.Key_W: ObjectType.TRANSITION,
	Qt.Key_E: ObjectType.ARROW
}

ToolbarButtons = [
	ObjectType.PLACE, ObjectType.TRANSITION, ObjectType.ARROW
]


class ObjectButton(QToolButton):
	def __init__(self, type, text, tooltip, shape):
		super().__init__()
		self.setToolTip(tooltip)
		
		self.setFixedWidth(80)
		self.setFixedHeight(80)
		self.setCheckable(True)
		self.shape = shape
		self.text = text
		self.type = type
		
		self.font = QFont()
		self.font.setPixelSize(16)
		self.textRect = QRectF(0, 55, 80, 20)
	
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


class ObjectMenu(QToolBar):
	def __init__(self, style):
		super().__init__()
		self.setFloatable(False)
		
		self.style = style
		self.buttons = {}
		
		self.group = QButtonGroup(self)
		for type in ToolbarButtons:
			self.addButton(type)
		
	def addButton(self, type):
		shape = ToolbarShapes[type]
		text = ToolbarText[type]
		tooltip = ToolbarTooltips[type]
		
		button = ObjectButton(type, text, tooltip, self.style.shapes[shape])
		button.clicked.connect(lambda: button.setChecked(True))
		self.buttons[type] = button
		
		self.group.addButton(button)
		self.addWidget(button)
		
	def selectButton(self, type):
		self.buttons[type].setChecked(True)
		
	def currentItem(self):
		button = self.group.checkedButton()
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
		if len(items) > 0:
			self.label.setText("%i items selected" %len(items))
		else:
			self.label.setText("No item selected")

		
class ItemSettings(QWidget):
	def __init__(self, obj):
		super().__init__()
		self.obj = obj
		self.obj.positionChanged.connect(self.updatePos)
		
		self.setStyleSheet("font-size: 16px")
		
		self.x = QLabel("%i" %obj.x)
		self.x.setAlignment(Qt.AlignRight)
		self.y = QLabel("%i" %obj.y)
		self.y.setAlignment(Qt.AlignRight)
		self.label = QLineEdit(obj.label)
		self.label.textEdited.connect(self.obj.setLabel)
		
		self.layout = QFormLayout(self)
		self.layout.addRow("X:", self.x)
		self.layout.addRow("Y:", self.y)
		self.layout.addRow("Label:", self.label)
		
	def updatePos(self):
		self.x.setText("%i" %self.obj.x)
		self.y.setText("%i" %self.obj.y)
	
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
		if len(items) == 1:
			self.setWidget(self.createWidget(items[0]))
		else:
			self.generalSettings.setSelection(items)
			self.setWidget(self.generalSettings)
			
	def createWidget(self, item):
		return ItemSettings(item.obj)
		
		
class HoverFilter:
	def apply(self, color):
		return QColor(color.rgba() ^ 0x555555)
		

class PlacementItem(EditorItem):
	def __init__(self, scene, style, type):
		super().__init__(scene, style.shapes[ItemShapes[type]])
		self.type = type
		

class ActiveItem(EditorItem):
	def __init__(self, scene, style, type, obj):
		super().__init__(scene, style.shapes[ItemShapes[type]])
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		
		self.type = type
		
		self.obj = obj
		self.obj.deleted.connect(self.removeFromScene)
		self.obj.positionChanged.connect(self.updatePos)
		self.obj.labelChanged.connect(self.updateLabel)
		self.move(QPointF(obj.x, obj.y))
		
		self.hoverFilter = HoverFilter()
		
		self.font = QFont()
		self.font.setPixelSize(16)
		self.fontMetrics = QFontMetrics(self.font)
		
	def move(self, pos):
		pos = self.alignPos(pos)
		self.obj.move(pos.x(), pos.y())
	
	def delete(self):
		self.obj.delete()
		
	def updatePos(self):
		self.setPos(self.obj.x, self.obj.y)
		
	def updateLabel(self):
		self.prepareGeometryChange()
		self.update()
		
	def labelRect(self):
		rect = self.fontMetrics.boundingRect(self.obj.label)
		rect.moveCenter(QPoint(0, self.shape.rect[1] + self.shape.rect[3] + 12))
		return QRectF(rect.adjusted(-1, -1, 1, 1))
		
	def boundingRect(self):
		rect = super().boundingRect()
		return rect.united(self.labelRect())
		
	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)
		
		if self.isSelected():
			painter.save()
			pen = QPen(Qt.blue)
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(*self.shape.rect)
			painter.restore()
		
		painter.setFont(self.font)
		painter.drawText(self.labelRect(), Qt.AlignCenter, self.obj.label)
			
			
class ArrowType:
	INPUT = 0
	OUTPUT = 1
			
			
class ArrowItem(EditorObject):
	def __init__(self, scene):
		super().__init__(scene)
		self.setZValue(-1)
		
	def getSource(self): raise NotImplementedError("ArrowItem.getSource")
	def getTarget(self): raise NotImplementedError("ArrowItem.getTarget")
	
	def boundingRect(self):
		source = self.getSource()
		target = self.getTarget()		
		x = min(source.x(), target.x()) - 10
		y = min(source.y(), target.y()) - 10
		w = abs(source.x() - target.x()) + 20
		h = abs(source.y() - target.y()) + 20
		return QRectF(x, y, w, h)
	
	def paint(self, painter, option, widget):
		painter.setRenderHint(QPainter.Antialiasing)
		
		pen = QPen()
		pen.setCapStyle(Qt.RoundCap)
		pen.setWidth(4)
		painter.setPen(pen)
		
		source = self.getSource()
		target = self.getTarget()
		diff = target - source
		
		sx, sy = source.x(), source.y()
		tx, ty = target.x(), target.y()
		dx, dy = diff.x(), diff.y()
		
		angle = math.atan2(dy, dx)
		
		painter.drawLine(source, target)
		painter.drawLine(
			tx, ty,
			tx + 10 * math.cos(angle + math.pi * .75),
			ty + 10 * math.sin(angle + math.pi * .75)
		)
		painter.drawLine(
			tx, ty,
			tx + 10 * math.cos(angle - math.pi * .75),
			ty + 10 * math.sin(angle - math.pi * .75)
		)
	
			
class PlacementArrow(ArrowItem):
	def __init__(self, scene, source):
		super().__init__(scene)
		self.setZValue(-1)
		self.source = source
		self.target = source.pos()
		
	def getSource(self): return self.source.pos()
	def getTarget(self): return self.target
		
	def move(self, pos):
		self.prepareGeometryChange()
		self.target = pos
		self.update()

		
class ActiveArrow(ArrowItem):
	def __init__(self, scene, obj, type):
		super().__init__(scene)
		
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
	
	def getSource(self):
		dx = self.target.x - self.source.x
		dy = self.target.y - self.source.y
		angle = math.atan2(dy, dx)
		
		return QPointF(
			self.source.x + math.cos(angle) * 30,
			self.source.y + math.sin(angle) * 30
		)
	
	def getTarget(self):
		dx = self.target.x - self.source.x
		dy = self.target.y - self.source.y
		angle = math.atan2(dy, dx)
		
		return QPointF(
			self.target.x - math.cos(angle) * 30,
			self.target.y - math.sin(angle) * 30
		)
	
	def updateArrow(self):
		self.prepareGeometryChange()
		self.update()
		
			
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
		item = ActiveItem(self.scene, self.style, ObjectType.PLACE, obj)
		self.scene.addItem(item)
		
	def addTransition(self, obj):
		item = ActiveItem(self.scene, self.style, ObjectType.TRANSITION, obj)
		self.scene.addItem(item)
		
	def addInput(self, obj):
		item = ActiveArrow(self.scene, obj, ArrowType.INPUT)
		self.scene.addItem(item)
	
	def addOutput(self, obj):
		item = ActiveArrow(self.scene, obj, ArrowType.OUTPUT)
		self.scene.addItem(item)
		
	def startPlacement(self, pos):
		type = self.toolbar.currentItem()
		if type in [ObjectType.PLACE, ObjectType.TRANSITION]:
			self.scene.setHoverEnabled(False)
			item = PlacementItem(self.scene, self.style, type)
			item.move(pos)
			return item
		elif type == ObjectType.ARROW:
			source = self.scene.findItem(pos, ActiveItem)
			if source:
				return PlacementArrow(self.scene, source)
		
	def finishPlacement(self, pos, item):
		x, y = pos.x(), pos.y()
		
		if isinstance(item, PlacementItem):
			if not item.invalid:
				if item.type == ObjectType.PLACE:
					place = petri.Place(self.net, x, y)
					self.net.places.add(place)
				elif item.type == ObjectType.TRANSITION:
					trans = petri.Transition(self.net, x, y)
					self.net.transitions.add(trans)
		
		elif isinstance(item, PlacementArrow):
			source = item.source
			target = self.scene.findItem(pos, ActiveItem)
			if target and target.type != source.type:
				if target.type == ObjectType.TRANSITION:
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
		
		self.toolbar = ObjectMenu(style)
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
		menuBar.view.showGrid.toggled.connect(self.scene.setGridEnabled)
		self.setMenuBar(menuBar)
		
		self.updateWindowTitle()
		
	def closeEvent(self, e):
		if self.checkUnsaved():
			e.accept()
		else:
			e.ignore()
			
	def keyPressEvent(self, e):
		key = e.key()
		if key in ToolbarShortcuts:
			self.toolbar.selectButton(ToolbarShortcuts[key])
			
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
