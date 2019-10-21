
from ui.view import *
import config


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
		self.connect(self.obj.positionChanged, self.updateLabel)
		self.connect(self.obj.positionChanged, self.updateLabel)
		self.connect(self.obj.labelChanged, self.updateLabel)
		self.connect(self.obj.deleted, self.removeFromScene)

		self.font = QFont()
		self.font.setPixelSize(16)
		self.fontMetrics = QFontMetrics(self.font)

		self.updateLabel()
		
	def delete(self):
		self.obj.setLabel("")
		self.obj.setLabelAngle(math.pi / 2)
		self.obj.setLabelDistance(35)

	def drag(self, param):
		dx = param.pos.x() - self.obj.x
		dy = param.pos.y() - self.obj.y

		dist = math.sqrt(dx * dx + dy * dy)
		dist = min(max(dist, config.get("ui.label_distance_min")), config.get("ui.label_distance_max"))

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
		return QRectF(rect.adjusted(-2, -2, 2, 2))

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
		
	def drag(self, param):
		self.setPos(alignToGrid(param.pos))
		
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
		self.connect(self.obj.deleted, self.removeFromScene)
		self.connect(self.obj.positionChanged, self.updatePos)
		self.setPos(obj.x, obj.y)
		
		self.filter = HoverFilter(self)

		self.label = LabelItem(scene, obj)
		scene.addItem(self.label)
		
	def drag(self, param):
		pos = alignToGrid(param.pos)
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