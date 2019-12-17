
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ..common import *
from .. import config as config
import json
import math


GRID_SIZE = 20


def round(value, base):
	return math.floor(value / base + 0.5) * base
	
def alignToGrid(pos):
	x = round(pos.x(), GRID_SIZE)
	y = round(pos.y(), GRID_SIZE)
	return QPointF(x, y)
	
def mergeColors(c1, c2, p=.5):
	r = c1.red() * (1 - p) + c2.red() * p
	g = c1.green() * (1 - p) + c2.green() * p
	b = c1.blue() * (1 - p) + c2.blue() * p
	return QColor(r, g, b)
	

ShapeColors = {
	"black": QColor(0, 0, 0),
	"white": QColor(255, 255, 255),
	
	"red": QColor(255, 0, 0),
	"green": QColor(0, 255, 0),
	"blue": QColor(0, 0, 255),
	
	"lightred": QColor(255, 128, 128),
	"lightblue": QColor(128, 128, 255),
	
	"yellow": QColor(255, 255, 0),
	
	"orange": QColor(255, 128, 0),
	
	"lightorange": QColor(255, 192, 128)
}

class ShapeElement:
	def __init__(self, type, **data):
		self.type = type
		if self.type == "line":
			self.x1, self.y1 = data["x1"], data["y1"]
			self.x2, self.y2 = data["x2"], data["y2"]
			self.curve = data["curve"]
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
		elif self.type == "arrow":
			self.x1, self.y1 = data["x1"], data["y1"]
			self.x2, self.y2 = data["x2"], data["y2"]
			self.stretch = data["stretch"]
			self.curve = data["curve"]
		elif self.type == "polygon":
			self.points = data["points"]
		else:
			raise ValueError("Unknown shape element type: %s" %self.type)
			
			
class ShapePart:
	def __init__(self):
		self.pen = QPen()
		self.brush = QBrush()
		self.path = QPainterPath()
		self.elements = []
		self.stroke = 0
		
	def setPen(self, pen): self.pen = pen
	def setBrush(self, brush): self.brush = brush
	def setStroke(self, stroke): self.stroke = stroke
	
	def addElement(self, element):
		self.elements.append(element)
		
	def load(self, data):
		pen = data.get("pen")
		if pen:
			self.pen = QPen(ShapeColors[pen["color"]])
			self.pen.setWidth(pen["width"])
			self.pen.setCapStyle(Qt.RoundCap)
		
		brush = data.get("brush")
		if brush:
			self.brush = QBrush(ShapeColors[brush["color"]])
		
		self.elements = []
		for element in data["elements"]:
			self.elements.append(ShapeElement(**element))
		
	def update(self):
		self.path = QPainterPath()
		
		for element in self.elements:
		
			if element.type == "line":
				dx = element.x2 - element.x1
				dy = element.y2 - element.y1
				angle = math.atan2(dy, dx)
				
				centerx = (element.x1 + element.x2) / 2
				centery = (element.y1 + element.y2) / 2
				
				controlx = centerx + math.cos(angle + math.pi / 2) * element.curve
				controly = centery + math.sin(angle + math.pi / 2) * element.curve
				
				self.path.moveTo(element.x1, element.y1)
				self.path.quadTo(controlx, controly, element.x2, element.y2)
				self.path.quadTo(controlx, controly, element.x1, element.y1)
			
			elif element.type == "arc":
				self.path.arcMoveTo(element.x, element.y, element.w, element.h, element.start)
				self.path.arcTo(element.x, element.y, element.w, element.h, element.start, element.span)
			
			elif element.type == "circle":
				self.path.addEllipse(QPointF(element.x, element.y), element.r, element.r)
			
			elif element.type == "rect":
				self.path.addRect(element.x, element.y, element.w, element.h)
				
			elif element.type == "polygon":
				points = []
				for point in element.points:
					points.append(QPointF(point[0], point[1]))
				self.path.addPolygon(QPolygonF(points))
			
			elif element.type == "arrow":
				dx = element.x2 - element.x1
				dy = element.y2 - element.y1
				length = math.sqrt(dx * dx + dy * dy)
				
				angle1 = math.atan2(dy, dx)
				angle2 = angle1 - math.atan2(element.curve, length / 2)
				
				centerx = (element.x1 + element.x2) / 2
				centery = (element.y1 + element.y2) / 2
				
				controlx = centerx + math.cos(angle1 + math.pi / 2) * element.curve
				controly = centery + math.sin(angle1 + math.pi / 2) * element.curve
				
				self.path.moveTo(element.x1, element.y1)
				self.path.quadTo(controlx, controly, element.x2, element.y2)
				self.path.quadTo(controlx, controly, element.x1, element.y1)
				
				self.path.moveTo(element.x2, element.y2)
				self.path.lineTo(
					element.x2 + element.stretch * math.cos(angle2 + math.pi * .75),
					element.y2 + element.stretch * math.sin(angle2 + math.pi * .75)
				)
				
				self.path.moveTo(element.x2, element.y2)
				self.path.lineTo(
					element.x2 + element.stretch * math.cos(angle2 - math.pi * .75),
					element.y2 + element.stretch * math.sin(angle2 - math.pi * .75)
				)
		
		if self.stroke > 0:
			stroker = QPainterPathStroker()
			stroker.setWidth(self.stroke)
			shapePath = stroker.createStroke(self.path)
			self.shapePath = self.path.united(shapePath)
		else:
			self.shapePath = self.path
	
	
class Shape:
	def __init__(self):
		self.parts = []
		self.path = QPainterPath()
		self.shapePath = QPainterPath()
		self.rect = QRectF()
		
	def addPart(self, part):
		self.parts.append(part)
		self.update()
		
	def load(self, data):
		self.parts = []
		for part in data:
			shapePart = ShapePart()
			shapePart.load(part)
			self.parts.append(shapePart)
			
		self.update()
			
	def draw(self, painter, filter=None):
		painter.setRenderHint(QPainter.Antialiasing)
		
		for part in self.parts:
			painter.save()
			
			pen = QPen(part.pen)
			if filter:
				filter.applyToPen(pen)
			painter.setPen(pen)
				
			brush = QBrush(part.brush)
			if filter:
				filter.applyToBrush(brush)
			painter.setBrush(brush)
			
			painter.drawPath(part.path)
			painter.restore()
		
	def update(self):
		self.path = QPainterPath()
		self.shapePath = QPainterPath()
		for part in self.parts:
			part.update()
			self.path.addPath(part.path)
			self.shapePath.addPath(part.shapePath)
		self.rect = self.shapePath.boundingRect()
		
		
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

			
class DragMode:
	NONE = 0
	NORMAL = 1
	SPECIAL = 2

	
class EditorItem(QGraphicsItem):
	def __init__(self, scene):
		super().__init__()
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		
		self.signals = SignalListener()
		
		self.scene = scene
		self.dragMode = DragMode.NONE
		self.invalid = False
		
		self.doubleClicked = Signal()
	
	def connect(self, signal, callback):
		self.signals.connect(signal, callback)
	
	def disconnect(self):
		self.signals.disconnect()
	
	def setInvalid(self, invalid):
		if self.invalid != invalid:
			self.invalid = invalid
			self.update()
			
	def drag(self, param): pass
	def delete(self): pass
	
	def removeFromScene(self):
		self.scene.removeItem(self)
		
	def addToScene(self):
		self.scene.addItem(self)
		
	def checkCollisions(self): pass
	
	
class ShapeFilter:
	def __init__(self, item):
		self.item = item

	def applyToPen(self, pen):
		if self.item.isSelected():
			pen.setColor(Qt.blue)
		if self.item.hover:
			color = mergeColors(pen.color(), QColor(Qt.gray))
			pen.setColor(color)

	def applyToBrush(self, brush):
		if self.item.hover:
			color = mergeColors(brush.color(), QColor(Qt.gray))
			brush.setColor(color)
	
	
class EditorShape(EditorItem):
	def __init__(self, scene, shape=None):
		super().__init__(scene)
		self.hover = False
		self.filter = ShapeFilter(self)
		
		self.shp = shape
		if self.shp is None:
			self.shp = Shape()
	
	def setShape(self, shape):
		self.shp = shape
		self.updateShape()
		
	def updateShape(self):
		self.prepareGeometryChange()
		self.shp.update()
		self.update()
		
	def setHover(self, hover):
		if self.hover != hover:
			self.hover = hover
			self.update()
		
	def checkHover(self, pos):
		pos = self.mapFromScene(pos)
		self.setHover(self.contains(pos))
		
	def shape(self):
		return self.shp.shapePath
		
	def boundingRect(self):
		return self.shp.rect.adjusted(-2, -2, 2, 2)
		
	def paint(self, painter, option, widget):
		self.shp.draw(painter, self.filter)
	
	
class DragParam:
	def __init__(self, pos, mouse):
		self.pos = pos
		self.mouse = mouse

	
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
				item.drag(DragParam(base + posDiff, pos))
			for item in self.items:
				item.checkCollisions()
	
	def finish(self, pos):
		if any(item.invalid for item in self.items):
			for item, base in zip(self.items, self.itemBase):
				item.drag(DragParam(base, self.dragBase))
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
	def __init__(self):
		super().__init__(-10000, -10000, 20000, 20000)
		
		self.dragger = ObjectDragger()
		self.placedItem = None
		
		self.hoverEnabled = True
		self.gridEnabled = True
		
		self.controller = None
		
	def cleanup(self):
		for item in self.items():
			item.disconnect()
		
	def setController(self, controller):
		self.controller = controller
		
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
			if isinstance(item, EditorShape):
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
					if item.dragMode == DragMode.NORMAL:
						items = [i for i in self.selectedItems() if i.dragMode == DragMode.NORMAL]
						self.dragger.init(pos, items)
					elif item.dragMode == DragMode.SPECIAL:
						self.dragger.init(pos, [item])
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
			self.placedItem.drag(DragParam(e.scenePos(), e.scenePos()))
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

	def mouseDoubleClickEvent(self, e):
		pos = e.scenePos()
		if e.button() == Qt.LeftButton:
			item = self.findItem(pos, EditorItem)
			if item:
				item.doubleClicked.emit()
		

class EditorView(QGraphicsView):
	def __init__(self, scene):
		super().__init__(scene)
		self.setMouseTracking(True)
		self.setDragMode(QGraphicsView.RubberBandDrag)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.horizontalScrollBar().disconnect()
		self.verticalScrollBar().disconnect()
		
		self.prevPos = None
		self.prevDelta = None
		self.handDrag = False
		
		self.zoom = 1
		
		self.scrollStep = config.get("ui.keyboard_scroll_speed")
		
	def updateDragMode(self):
		if self.handDrag:
			self.setDragMode(QGraphicsView.ScrollHandDrag)
		else:
			self.setDragMode(QGraphicsView.RubberBandDrag)
		
	def setHandDrag(self, enabled):
		self.handDrag = enabled
		if self.prevPos is None:
			self.updateDragMode()
		
	def mousePressEvent(self, e):
		super().mousePressEvent(e)
		if e.button() == Qt.LeftButton:
			if not self.itemAt(e.pos()):
				self.prevPos = self.mapToScene(e.pos())
				self.prevDelta = QPointF()
		
	def mouseMoveEvent(self, e):
		super().mouseMoveEvent(e)
		if self.dragMode() == QGraphicsView.ScrollHandDrag:
			if self.prevPos is not None:
				pos = self.mapToScene(e.pos())
				delta = pos - self.prevPos + self.prevDelta
				self.translate(delta.x(), delta.y())
				self.prevPos = pos
				self.prevDelta = delta
		
	def mouseReleaseEvent(self, e):
		super().mouseReleaseEvent(e)
		if e.button() == Qt.LeftButton:
			self.updateDragMode()
			self.prevPos = None
			self.prevDelta = None
		
	def keyPressEvent(self, e):
		super().keyPressEvent(e)
		
		key = e.key()
		if key == Qt.Key_Left:
			self.translate(self.scrollStep, 0)
		elif key == Qt.Key_Right:
			self.translate(-self.scrollStep, 0)
		elif key == Qt.Key_Up:
			self.translate(0, self.scrollStep)
		elif key == Qt.Key_Down:
			self.translate(0, -self.scrollStep)
		
	def wheelEvent(self, e):
		zoom = 1.0008 ** e.angleDelta().y()
		newZoom = self.zoom * zoom
		if newZoom > 0.1 and newZoom < 10:
			self.zoom = newZoom
			prevPos = self.mapToScene(e.pos())
			self.scale(zoom, zoom)
			newPos = self.mapToScene(e.pos())
			delta = newPos - prevPos
			self.translate(delta.x(), delta.y())
