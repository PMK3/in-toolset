
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

ToolbarButtons = [
	ObjectType.PLACE, ObjectType.TRANSITION, ObjectType.ARROW
]


class ObjectButton(QToolButton):
	def __init__(self, type, shape):
		super().__init__()
		self.setFixedWidth(shape.rect[2] + 12)
		self.setFixedHeight(shape.rect[3] + 12)
		self.setCheckable(True)
		self.shape = shape
		self.type = type
	
	def paintEvent(self, e):
		super().paintEvent(e)
		
		painter = QPainter()
		painter.begin(self)
		painter.translate(self.width() / 2, self.height() / 2)
		self.shape.draw(painter)
		painter.end()
			

class ObjectMenu(QToolBar):
	def __init__(self, style):
		super().__init__()
		self.setFloatable(False)
		
		self.style = style
		self.group = QButtonGroup(self)
		for type in ToolbarButtons:
			self.addButton(type)
		
	def addButton(self, type):
		shape = ToolbarShapes[type]
		button = ObjectButton(type, self.style.shapes[shape])
		button.clicked.connect(lambda: button.setChecked(True))
		self.group.addButton(button)
		self.addWidget(button)
		
	def currentItem(self):
		button = self.group.checkedButton()
		if button:
			return button.type
		return -1
		
		
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
		self.obj.positionChanged.connect(self.setPos)
		self.move(QPointF(obj.x, obj.y))
		
		self.hoverFilter = HoverFilter()
		
	def move(self, pos):
		pos = self.alignPos(pos)
		self.obj.move(pos.x(), pos.y())
	
	def delete(self):
		self.obj.delete()
		
	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)
		
		if self.isSelected():
			pen = QPen(Qt.blue)
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(*self.shape.rect)
			
			
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
	
	def updateArrow(self, x, y):
		self.prepareGeometryChange()
		self.update()
		
			
class Editor:
	def __init__(self, style, toolbar):
		self.toolbar = toolbar
		self.style = style
		
		self.scene = EditorScene(self)
		self.view = EditorView(self.scene)
		
	def widget(self):
		return self.view
		
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
		
	def selectAll(self):
		self.scene.selectAll()
		
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
		
		toolbar = ObjectMenu(style)
		self.addToolBar(Qt.LeftToolBarArea, toolbar)
		
		self.editor = Editor(style, toolbar)
		self.setCentralWidget(self.editor.widget())
		
		self.createProject()
		
		menuBar = MenuBar()
		menuBar.file.new.triggered.connect(self.handleNew)
		menuBar.file.open.triggered.connect(self.handleOpen)
		menuBar.file.save.triggered.connect(self.handleSave)
		menuBar.file.saveAs.triggered.connect(self.handleSaveAs)
		menuBar.file.quit.triggered.connect(self.close)
		menuBar.edit.selectAll.triggered.connect(self.editor.selectAll)
		self.setMenuBar(menuBar)
		
		self.updateWindowTitle()
		
	def closeEvent(self, e):
		if self.checkUnsaved():
			e.accept()
		else:
			e.ignore()
			
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
