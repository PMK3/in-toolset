
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ui.menu import MenuBar
import math
import sys


GRID_SIZE = 20


def round(value, base):
	return math.floor(value / base + 0.5) * base


class PetriNode(QGraphicsItem):
	def __init__(self, selectable):
		super().__init__()
		self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
		
		self.invalid = False
		
	def setInvalid(self, invalid):
		self.invalid = invalid
		self.update()
		
	def checkCollisions(self):
		scene = self.scene()
		if scene:
			items = self.scene().collidingItems(self)
			if any(isinstance(item, PetriNode) for item in items):
				self.setInvalid(True)
			else:
				self.setInvalid(False)
		
	def itemChange(self, change, value):
		if change == QGraphicsItem.ItemPositionChange:
			x = round(value.x(), GRID_SIZE)
			y = round(value.y(), GRID_SIZE)
			return QPointF(x, y)
		return super().itemChange(change, value)
		
	def boundingRect(self):
		return QRectF(-22, -22, 44, 44)
		
	def paint(self, painter, option, widget):
		rect = QRectF(-20, -20, 40, 40)
		
		painter.setBrush(QBrush(Qt.white))
		painter.drawEllipse(rect)
		
		if self.isSelected():
			pen = QPen(Qt.blue)
			pen.setWidth(2)
			painter.setPen(pen)
			painter.setBrush(Qt.NoBrush)
			painter.drawRect(rect)
			
		if self.invalid:
			brush = QBrush(Qt.red, Qt.BDiagPattern)
			painter.setBrush(brush)
			painter.setPen(Qt.NoPen)
			painter.drawRect(rect)
			
			
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
	def __init__(self, parent):
		super().__init__(-10000, -10000, 20000, 20000, parent)
		
		self.dragger = ItemDragger()
		self.placedItem = None
		self.dragButton = None
		
	def selectAll(self):
		for item in self.items():
			if isinstance(item, PetriNode):
				item.setSelected(True)
				
	def findItem(self, pos, *classes):
		for item in self.items(pos):
			if isinstance(item, classes):
				return item
				
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
				#TODO: Remove item from petri net
				self.removeItem(item)
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
				
				self.placedItem = PetriNode(False)
				self.placedItem.setPos(e.scenePos())
				self.addItem(self.placedItem)
				
				self.placedItem.checkCollisions()
				
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
					#TODO: Add item to petri net
					node = PetriNode(True)
					node.setPos(e.scenePos())
					self.addItem(node)
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
		
		self.resize(1080, 720)
		
		self.scene = PetriScene(self)
		self.view = PetriView(self.scene)
		self.setCentralWidget(self.view)
		
		menuBar = MenuBar()
		menuBar.file.quit.triggered.connect(self.close)
		menuBar.edit.selectAll.triggered.connect(self.scene.selectAll)
		self.setMenuBar(menuBar)
		
		self.setWindowTitle("Petri nets")


class Application:
	def start(self):
		self.app = QApplication(sys.argv)
		self.window = MainWindow()
		self.window.show()
		self.app.exec()
