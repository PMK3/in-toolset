
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import json
import math


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
			
	def draw(self, painter, filter=None):
		painter.save()
		painter.setRenderHint(QPainter.Antialiasing)
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
				pen.setCapStyle(Qt.RoundCap)
				painter.setPen(pen)
			elif element.type == "brush":
				color = QColor(element.color)
				if filter:
					color = filter.apply(color)
				brush = QBrush(color)
				painter.setBrush(brush)
		painter.restore()
		
		
class Style:
	def __init__(self):
		self.shapes = {}
		
	def load(self, filename):
		with open(filename) as f:
			info = json.load(f)
		
		for name, data in info["shapes"].items():
			shape = Shape()
			shape.load(data)
			self.shapes[name] = shape


class EditorObject(QGraphicsItem):
	def __init__(self, scene):
		super().__init__()
		self.scene = scene
		
	def move(self, pos):
		self.setPos(pos)
		
	def delete(self):
		self.removeFromScene()
	
	def removeFromScene(self):
		self.scene.removeItem(self)
		
	def addToScene(self):
		self.scene.addItem(self)
		
	def checkCollisions(self): pass
			
			
class EditorItem(EditorObject):
	def __init__(self, scene, shape):
		super().__init__(scene)
		self.shape = shape
		self.invalid = False
		self.hover = False
		self.hoverFilter = None
		
	def move(self, pos):
		self.setPos(self.alignPos(pos))
		
	def alignPos(self, pos):
		x = round(pos.x(), GRID_SIZE)
		y = round(pos.y(), GRID_SIZE)
		return QPointF(x, y)
	
	def setInvalid(self, invalid):
		if self.invalid != invalid:
			self.invalid = invalid
			self.update()
	
	def setHover(self, hover):
		if self.hover != hover:
			self.hover = hover
			self.update()
		
	def checkHover(self, pos):
		pos = self.mapFromScene(pos)
		self.setHover(self.contains(pos))
		
	def checkCollisions(self):
		items = self.scene.collidingItems(self)
		if any(isinstance(item, EditorItem) for item in items):
			self.setInvalid(True)
		else:
			self.setInvalid(False)
			
	def boundingRect(self):
		x, y, w, h = self.shape.rect
		return QRectF(x - 2, y - 2, w + 4, h + 4)
		
	def paint(self, painter, option, widget):
		filter = None
		if self.hover:
			filter = self.hoverFilter
		self.shape.draw(painter, filter)
		
		if self.invalid:
			painter.save()
			brush = QBrush(Qt.red, Qt.BDiagPattern)
			painter.setBrush(brush)
			painter.setPen(Qt.NoPen)
			painter.drawRect(*self.shape.rect)
			painter.restore()
	
	
class ObjectDragger:
	def __init__(self):
		self.reset()
	
	def reset(self):
		self.items = []
		self.itemBase = []
		self.dragBase = None
		
	def isDragging(self):
		return self.items and self.dragBase
		
	def init(self, pos, items):
		self.dragBase = pos
		
		for item in items:
			item.setZValue(item.zValue() + .5)
		self.items = items
		self.itemBase = [item.pos() for item in items]
		
	def update(self, pos):
		if self.isDragging():
			posDiff = pos - self.dragBase
			for item, base in zip(self.items, self.itemBase):
				item.move(base + posDiff)
			for item in self.items:
				item.checkCollisions()
	
	def finish(self, pos):
		if any(item.invalid for item in self.items):
			for item, base in zip(self.items, self.itemBase):
				item.move(base)
				item.setInvalid(False)
		
		for item in self.items:
			item.setZValue(item.zValue() - .5)
		
		self.reset()
		
	def removeItem(self, item):
		if item in self.items:
			index = self.items.index(item)
			self.items.pop(index)
			self.itemBase.pop(index)


class EditorScene(QGraphicsScene):
	def __init__(self, controller):
		super().__init__(-10000, -10000, 20000, 20000)
		
		self.controller = controller
		
		self.dragger = ObjectDragger()
		self.placedItem = None
		
		self.hoverEnabled = True
		self.gridEnabled = True
		
	def selectAll(self):
		for item in self.items():
			item.setSelected(True)
			
	def findItem(self, pos, *classes):
		for item in self.items(pos):
			if isinstance(item, classes):
				return item
				
	def updateHover(self, pos):
		enabled = self.hoverEnabled and not self.dragger.isDragging()
		for item in self.items():
			if isinstance(item, EditorItem):
				if enabled:
					item.checkHover(pos)
				else:
					item.setHover(False)
			
	def setHoverEnabled(self, hover):
		self.hoverEnabled = hover
		
	def setGridEnabled(self, grid):
		self.gridEnabled = grid
		self.update()
			
	def drawBackground(self, painter, rect):
		pen = QPen()
		pen.setColor(QColor(230, 230, 230))
		painter.setPen(pen)
		
		if self.gridEnabled:
			for x in range(int(rect.left()) // GRID_SIZE, int(rect.right()) // GRID_SIZE + 1):
				painter.drawLine(x * GRID_SIZE, rect.top(), x * GRID_SIZE, rect.bottom())
			for y in range(int(rect.top()) // GRID_SIZE, int(rect.bottom()) // GRID_SIZE + 1):
				painter.drawLine(rect.left(), y * GRID_SIZE, rect.right(), y * GRID_SIZE)
			
	def keyPressEvent(self, e):
		super().keyPressEvent(e)
		if e.key() == Qt.Key_Delete:
			for item in self.selectedItems():
				self.dragger.removeItem(item)
				item.delete()
			if self.placedItem:
				self.placedItem.checkCollisions()
			
	def mousePressEvent(self, e):
		pos = e.scenePos()
		if self.dragger.isDragging() or self.placedItem:
			e.accept()
		else:
			super().mousePressEvent(e)
			if e.button() == Qt.LeftButton:
				item = self.findItem(pos, EditorItem)
				if item:
					self.dragger.init(pos, self.selectedItems())
			elif e.button() == Qt.RightButton:
				self.placedItem = self.controller.startPlacement(pos)
				if self.placedItem:
					self.placedItem.checkCollisions()
					self.addItem(self.placedItem)
				e.accept()
					
	def mouseMoveEvent(self, e):
		super().mouseMoveEvent(e)
		
		self.updateHover(e.scenePos())
		
		self.dragger.update(e.scenePos())
		if self.placedItem:
			self.placedItem.move(e.scenePos())
			self.placedItem.checkCollisions()
			
	def mouseReleaseEvent(self, e):
		super().mouseReleaseEvent(e)
		if e.button() == Qt.LeftButton:
			self.dragger.finish(e.scenePos())
		elif e.button() == Qt.RightButton:
			if self.placedItem:
				self.removeItem(self.placedItem)
				self.controller.finishPlacement(e.scenePos(), self.placedItem)
				self.placedItem = None


class EditorView(QGraphicsView):
	def __init__(self, scene):
		super().__init__(scene)
		self.setMouseTracking(True)
		self.setDragMode(QGraphicsView.RubberBandDrag)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.horizontalScrollBar().disconnect()
		self.verticalScrollBar().disconnect()
		
		self.zoom = 1
		
	def keyPressEvent(self, e):
		super().keyPressEvent(e)
		
		key = e.key()
		if key == Qt.Key_Left:
			self.translate(10, 0)
		elif key == Qt.Key_Right:
			self.translate(-10, 0)
		elif key == Qt.Key_Up:
			self.translate(0, 10)
		elif key == Qt.Key_Down:
			self.translate(0, -10)
		
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
