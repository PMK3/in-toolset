
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.menu import MenuBar
from ui import settings
import petri
import json
import math
import sys
import os


GRID_SIZE = 20


def round(value, base):
	return math.floor(value / base + 0.5) * base
	
	
class ShapeElement:
	colors = {
		"black": Qt.black,
		"white": Qt.white
	}
	
	def load(self, data):
		self.type = data["type"]
		if self.type == "line":
			self.x1, self.y1 = data["x1"], data["y1"]
			self.x2, self.y2 = data["x2"], data["y2"]
		elif self.type == "arc":
			self.x, self.y = data["x"], data["y"]
			self.w, self.h = data["w"], data["h"]
			self.start, self.span = data["start"], data["span"]
		elif self.type == "circle":
			self.x, self.y = data["x"], data["y"]
			self.r = data["r"]
		elif self.type == "rect":
			self.x, self.y = data["x"], data["y"]
			self.w, self.h = data["w"], data["h"]
			
		elif self.type == "pen":
			self.width = data["width"]
		elif self.type == "brush":
			self.color = self.colors[data["color"]]
	
	
class Shape:
	def __init__(self):
		self.rect = [-80, -80, 160, 160]
		self.elements = []
		
	def load(self, data):
		self.rect = data["rect"]
		
		self.elements = []
		for element in data["elements"]:
			ele = ShapeElement()
			ele.load(element)
			self.elements.append(ele)
			
	def draw(self, painter):
		painter.save()
		for element in self.elements:
			if element.type == "line":
				painter.drawLine(element.x1, element.y1, element.x2, element.y2)
			elif element.type == "arc":
				painter.drawArc(element.x, element.y, element.w, element.h, element.start * 16, element.span * 16)
			elif element.type == "circle":
				painter.drawEllipse(QPointF(element.x, element.y), element.r, element.r)
			elif element.type == "rect":
				painter.drawRect(element.x, element.y, element.w, element.h)
				
			elif element.type == "pen":
				pen = QPen()
				pen.setWidth(element.width)
				painter.setPen(pen)
			elif element.type == "brush":
				brush = QBrush(element.color)
				painter.setBrush(brush)
		painter.restore()
		
		
class ShapeStore:
	def __init__(self):
		self.shapes = {}
		
	def __getitem__(self, item):
		return self.shapes[item]
		
	def load(self, filename):
		with open(filename) as f:
			shapes = json.load(f)
		
		for name, data in shapes.items():
			shape = Shape()
			shape.load(data)
			self.shapes[name] = shape
			
			
class ObjectType:
	PLACE = 0
	TRANSITION = 1
			
			
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
	def __init__(self, shapes):
		super().__init__()
		self.setFloatable(False)
		
		self.group = QButtonGroup(self)
		self.addButton(ObjectType.PLACE, shapes["place"])
		self.addButton(ObjectType.TRANSITION, shapes["transition"])
		
	def addButton(self, type, shape):
		button = ObjectButton(type, shape)
		button.clicked.connect(lambda: button.setChecked(True))
		self.group.addButton(button)
		self.addWidget(button)
		
	def currentItem(self):
		button = self.group.checkedButton()
		if button:
			return button.type
		return -1
		
		
class ObjectState:
	PLACING = 0
	ACTIVE = 1


class PetriNode(QGraphicsItem):
	def __init__(self, scene, obj, shape, state):
		super().__init__()
		if state == ObjectState.ACTIVE:
			self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
		
		self.obj = obj
		if state == ObjectState.ACTIVE:
			self.obj.deleted.connect(self.removeFromScene)
			self.obj.positionChanged.connect(self.updatePos)
		
		self.scene = scene
		self.shape = shape
		self.invalid = False

		self.updatePos()
		self.addToScene()
	
	def delete(self):
		self.obj.delete()
		
	def setInvalid(self, invalid):
		self.invalid = invalid
		self.update()
		
	def removeFromScene(self):
		self.scene.removeItem(self)

	def addToScene(self):
		self.scene.addItem(self)
		
	def updatePos(self):
		self.setPos(self.obj.x, self.obj.y)
		
	def checkCollisions(self):
		items = self.scene.collidingItems(self)
		if any(isinstance(item, PetriNode) for item in items):
			self.setInvalid(True)
		else:
			self.setInvalid(False)
		
	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemPositionChange:
			x = round(value.x(), GRID_SIZE)
			y = round(value.y(), GRID_SIZE)
			return QPointF(x, y)
		if change == QGraphicsItem.ItemPositionHasChanged:
			self.obj.move(value.x(), value.y())
			return value
		return super().itemChange(change, value)
		
	def boundingRect(self):
		x, y, w, h = self.shape.rect
		return QRectF(x - 2, y - 2, w + 4, h + 4)
		
	def paint(self, painter, option, widget):
		self.shape.draw(painter)
		
		if self.isSelected():
			pen = QPen(Qt.blue)
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(*self.shape.rect)
			
		if self.invalid:
			brush = QBrush(Qt.red, Qt.BDiagPattern)
			painter.setBrush(brush)
			painter.setPen(Qt.NoPen)
			painter.drawRect(*self.shape.rect)
			
	
class PlaceNode(PetriNode):
	def __init__(self, scene, obj, shapes, state):
		super().__init__(scene, obj, shapes["place"], state)
		self.type = ObjectType.PLACE
		
		
class TransitionNode(PetriNode):
	def __init__(self, scene, obj, shapes, state):
		super().__init__(scene, obj, shapes["transition"], state)
		self.type = ObjectType.TRANSITION

		
class ItemDragger:
	def __init__(self):
		self.reset()
	
	def reset(self):
		self.items = []
		self.itemBase = []
		self.dragBase = None
		self.moveBack = False
		
	def isDragging(self):
		return self.items and self.dragBase
		
	def init(self, pos, moveBack):
		self.dragBase = pos
		self.moveBack = moveBack
		
	def update(self, pos):
		if self.isDragging():
			posDiff = pos - self.dragBase
			for item, base in zip(self.items, self.itemBase):
				item.setPos(base + posDiff)
			for item in self.items:
				item.checkCollisions()
	
	def finish(self, pos):
		if self.moveBack:
			if any(item.invalid for item in self.items):
				for item, base in zip(self.items, self.itemBase):
					item.setPos(base)
					item.setInvalid(False)
		
		for item in self.items:
			item.setZValue(0)
		
		self.reset()
				
	def setItems(self, items):
		for item in items:
			item.setZValue(1)
		self.items = items
		self.itemBase = [item.pos() for item in items]
		
	def removeItem(self, item):
		if item in self.items:
			index = self.items.index(item)
			self.items.pop(index)
			self.itemBase.pop(index)


class PetriScene(QGraphicsScene):
	def __init__(self, toolbar, shapes):
		super().__init__(-10000, -10000, 20000, 20000)
		
		self.toolbar = toolbar
		self.shapes = shapes
		
		self.dragger = ItemDragger()
		self.placedItem = None
		self.dragButton = None
		
	def setProject(self, project):
		self.project = project
		self.project.net.placeAdded.connect(self.addPlace)
		self.project.net.transitionAdded.connect(self.addTransition)
		self.clear()
		
	def addPlace(self, place):
		PlaceNode(self, place, self.shapes, ObjectState.ACTIVE)
		
	def addTransition(self, transition):
		TransitionNode(self, transition, self.shapes, ObjectState.ACTIVE)
		
	def selectAll(self):
		for item in self.items():
			if isinstance(item, PetriNode):
				item.setSelected(True)
				
	def findItem(self, pos, *classes):
		for item in self.items(pos):
			if isinstance(item, classes):
				return item
				
	def createItem(self, pos):
		type = self.toolbar.currentItem()
		if type == ObjectType.PLACE:			
			obj = petri.Place(pos.x(), pos.y())
			item = PlaceNode(self, obj, self.shapes, ObjectState.PLACING)
			item.checkCollisions()
			return item
		elif type == ObjectType.TRANSITION:
			obj = petri.Transition(pos.x(), pos.y())
			item = TransitionNode(self, obj, self.shapes, ObjectState.PLACING)
			item.checkCollisions()
			return item
	
	def placeItem(self, type, obj):
		if type == ObjectType.PLACE:
			self.project.net.addPlace(obj)
		elif type == ObjectType.TRANSITION:
			self.project.net.addTransition(obj)
	
	def drawBackground(self, painter, rect):
		pen = QPen()
		pen.setColor(Qt.gray)
		painter.setPen(pen)
		
		for x in range(int(rect.left()) // GRID_SIZE, int(rect.right()) // GRID_SIZE + 1):
			painter.drawLine(x * GRID_SIZE, rect.top(), x * GRID_SIZE, rect.bottom())
		for y in range(int(rect.top()) // GRID_SIZE, int(rect.bottom()) // GRID_SIZE + 1):
			painter.drawLine(rect.left(), y * GRID_SIZE, rect.right(), y * GRID_SIZE)
			
	def keyPressEvent(self, e):
		if e.key() == Qt.Key_Delete:
			for item in self.selectedItems():
				self.dragger.removeItem(item)
				item.delete()
			if self.placedItem:
				self.placedItem.checkCollisions()
		
	def mousePressEvent(self, e):
		if self.dragger.isDragging():
			e.accept()
		else:
			super().mousePressEvent(e)
			if e.button() == Qt.LeftButton:
				item = self.findItem(e.scenePos(), PetriNode)
				if item:
					self.dragButton = Qt.LeftButton
					self.dragger.init(e.scenePos(), True)
					self.dragger.setItems(self.selectedItems())
			elif e.button() == Qt.RightButton:
				self.dragButton = Qt.RightButton
				
				self.placedItem = self.createItem(e.scenePos())
				if self.placedItem:
					self.dragger.init(e.scenePos(), False)
					self.dragger.setItems([self.placedItem])
				
				e.accept()
				
	def mouseMoveEvent(self, e):
		super().mouseMoveEvent(e)
		self.dragger.update(e.scenePos())
		
	def mouseReleaseEvent(self, e):
		super().mouseReleaseEvent(e)
		if e.button() == self.dragButton:
			self.dragger.finish(e.scenePos())
			if self.placedItem:
				self.removeItem(self.placedItem)
				if not self.placedItem.invalid:
					self.placeItem(self.placedItem.type, self.placedItem.obj)
				self.placedItem = None
			self.dragButton = None


class PetriView(QGraphicsView):
	def __init__(self, scene):
		super().__init__(scene)
		self.setDragMode(QGraphicsView.RubberBandDrag)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.horizontalScrollBar().disconnect()
		self.verticalScrollBar().disconnect()
		
		self.zoom = 1
		
	def wheelEvent(self, e):
		zoom = 1.001 ** e.angleDelta().y()
		newZoom = self.zoom * zoom
		if newZoom > 0.1 and newZoom < 10:
			self.zoom = newZoom
			prevPos = self.mapToScene(e.pos())
			self.scale(zoom, zoom)
			newPos = self.mapToScene(e.pos())
			delta = newPos - prevPos
			self.translate(delta.x(), delta.y())		
		
		
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setContextMenuPolicy(Qt.PreventContextMenu)
		
		shapes = ShapeStore()
		shapes.load("data/shapes.json")
		
		self.resize(1080, 720)
		
		objectMenu = ObjectMenu(shapes)
		self.addToolBar(Qt.LeftToolBarArea, objectMenu)
		
		self.scene = PetriScene(objectMenu, shapes)
		self.view = PetriView(self.scene)
		self.setCentralWidget(self.view)
		
		self.createProject()
		
		menuBar = MenuBar()
		menuBar.file.new.triggered.connect(self.handleNew)
		menuBar.file.open.triggered.connect(self.handleOpen)
		menuBar.file.save.triggered.connect(self.handleSave)
		menuBar.file.saveAs.triggered.connect(self.handleSaveAs)
		menuBar.file.quit.triggered.connect(self.close)
		menuBar.edit.selectAll.triggered.connect(self.scene.selectAll)
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
		self.scene.setProject(self.project)
		
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
