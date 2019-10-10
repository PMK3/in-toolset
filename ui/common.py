
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

class LabelItem(EditorItem):
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
		
	def disconnect(self):
		self.obj.positionChanged.disconnect(self.updateLabel)
		self.obj.labelChanged.disconnect(self.updateLabel)
		self.obj.deleted.disconnect(self.removeFromScene)
		
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
