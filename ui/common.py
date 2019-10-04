
from ui.view import *


def mergeColors(*colors):
	r = g = b = 0
	for color in colors:
		r += color.red()
		g += color.green()
		b += color.blue()
	
	r //= len(colors)
	g //= len(colors)
	b //= len(colors)
	return QColor(r, g, b)


class HoverFilter:
	def __init__(self, item):
		self.item = item

	def applyToPen(self, pen):
		if self.item.hover:
			color = mergeColors(pen.color(), QColor(Qt.gray))
			pen.setColor(color)

	def applyToBrush(self, brush):
		if self.item.hover:
			color = mergeColors(brush.color(), QColor(Qt.gray))
			brush.setColor(color)


class EditorNode(EditorShape):
	def __init__(self, scene, shape=None):
		super().__init__(scene, shape)
		self.dragMode = DragMode.NORMAL
		
	def drag(self, pos):
		self.setPos(alignToGrid(pos))
		
	def checkCollisions(self):
		items = self.scene.collidingItems(self)
		if any(isinstance(item, EditorNode) for item in items):
			self.setInvalid(True)
		else:
			self.setInvalid(False)
		
	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)
		
		if self.invalid:
			painter.save()
			brush = QBrush(Qt.red, Qt.BDiagPattern)
			painter.setBrush(brush)
			painter.setPen(Qt.NoPen)
			painter.drawRect(self.shp.rect)
			painter.restore()
			
			
class ActiveNode(EditorNode):
	def __init__(self, scene, shape, obj, type=None):
		super().__init__(scene, shape)
		
		self.type = type

		self.obj = obj
		self.obj.deleted.connect(self.removeFromScene)
		self.obj.positionChanged.connect(self.updatePos)
		self.setPos(obj.x, obj.y)
		
		self.filter = HoverFilter(self)
		
	def disconnect(self):
		self.obj.deleted.disconnect(self.removeFromScene)
		self.obj.positionChanged.disconnect(self.updatePos)

	def drag(self, pos):
		pos = alignToGrid(pos)
		self.obj.move(pos.x(), pos.y())

	def delete(self):
		self.obj.delete()

	def updatePos(self):
		self.setPos(self.obj.x, self.obj.y)
		
	def borderColor(self):
		if self.isSelected():
			return Qt.blue
		return None

	def paint(self, painter, option, widget):
		super().paint(painter, option, widget)
		
		color = self.borderColor()
		if color is not None:
			painter.save()
			pen = QPen(color)
			pen.setWidth(2)
			painter.setPen(pen)
			painter.drawRect(self.shp.rect)
			painter.restore()
