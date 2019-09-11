
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
	def __init__(self):
		super().__init__()
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
		
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
			painter.setBrush(QBrush())
			painter.drawRect(rect)


class PetriScene(QGraphicsScene):
	def __init__(self, parent):
		super().__init__(-10000, -10000, 20000, 20000, parent)
		
	def mousePressEvent(self, e):
		super().mousePressEvent(e)
		if e.button() == Qt.RightButton:
			item = PetriNode()
			item.setPos(e.scenePos())
			self.addItem(item)
		
	def drawBackground(self, painter, rect):
		pen = QPen()
		pen.setColor(Qt.gray)
		painter.setPen(pen)
		
		for x in range(int(rect.left()) // GRID_SIZE, int(rect.right()) // GRID_SIZE + 1):
			painter.drawLine(x * GRID_SIZE, rect.top(), x * GRID_SIZE, rect.bottom())
		for y in range(int(rect.top()) // GRID_SIZE, int(rect.bottom()) // GRID_SIZE + 1):
			painter.drawLine(rect.left(), y * GRID_SIZE, rect.right(), y * GRID_SIZE)


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
		self.setMenuBar(menuBar)
		
		self.setWindowTitle("Petri nets")


class Application:
	def start(self):
		self.app = QApplication(sys.argv)
		self.window = MainWindow()
		self.window.show()
		self.app.exec()
