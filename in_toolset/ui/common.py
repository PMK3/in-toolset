
from ..model.ui import *
from .view import *
import in_toolset.config


class ArrowBase(EditorShape):
	def __init__(self, scene):
		super().__init__(scene)
		self.setZValue(-1)
		
		self.dragMode = DragMode.SPECIAL

		self.element = ShapeElement(
			"arrow", x1=0, y1=0, x2=0, y2=0, curve=0, stretch=10
		)

		self.pen = QPen()
		self.pen.setCapStyle(Qt.RoundCap)
		self.pen.setWidth(2)

		part = ShapePart()
		part.setStroke(20)
		part.setPen(self.pen)
		part.addElement(self.element)

		shape = Shape()
		shape.addPart(part)

		self.setShape(shape)
		
	def setColor(self, color):
		self.pen.setColor(color)
		
	def setCurve(self, curve):
		self.element.curve = curve
		self.updateShape()
		
	def setType(self, type):
		self.element.type = type
		self.updateShape()

	def setPoints(self, x1, y1, x2, y2):
		self.element.x1 = x1
		self.element.y1 = y1
		self.element.x2 = x2
		self.element.y2 = y2
		self.updateShape()
		
		
class ArrowItem(ArrowBase):
	def __init__(self, scene, arrow):
		super().__init__(scene)
		self.arrow = arrow
		self.connect(self.arrow.restored, self.addToScene)
		self.connect(self.arrow.deleted, self.removeFromScene)
		self.connect(self.arrow.curveChanged, self.updateArrow)
		self.connect(self.arrow.source.positionChanged, self.updateArrow)
		self.connect(self.arrow.target.positionChanged, self.updateArrow)

		self.distance = 0

		self.updateArrow()
		
	def setDistance(self, distance):
		self.distance = distance
		self.updateArrow()
		
	def delete(self):
		self.arrow.delete()
		
	def drag(self, param):
		source = self.arrow.source
		target = self.arrow.target
		
		mx = param.mouse.x()
		my = param.mouse.y()
		dx = target.x - source.x
		dy = target.y - source.y
		length = math.sqrt(dx * dx + dy * dy)
		dist = (dy * mx - dx * my + target.x * source.y - target.y * source.x) / length
		
		# This is an approximation
		angle = math.atan2(-dist * 2, length / 2)
		offset = math.sin(angle) * self.distance * 2
		if abs(offset) > abs(dist):
			offset = -dist
		curve = -dist * 2 - offset
		
		self.arrow.setCurve(curve)
		
	def updateArrow(self):
		source = self.arrow.source
		target = self.arrow.target

		dx = target.x - source.x
		dy = target.y - source.y
		length = math.sqrt(dx * dx + dy * dy)
		
		# This is an approximation
		curveAngle = math.atan2(self.arrow.curve, length / 2)
		length -= math.cos(curveAngle) * self.distance
		
		angle1 = math.atan2(dy, dx) + curveAngle
		angle2 = math.atan2(dy, dx) - curveAngle
		
		self.setCurve(self.arrow.curve)
		
		self.setPoints(
			source.x + math.cos(angle1) * self.distance,
			source.y + math.sin(angle1) * self.distance,
			target.x - math.cos(angle2) * self.distance,
			target.y - math.sin(angle2) * self.distance
		)


class LabelBase(EditorItem):
	def __init__(self, scene):
		super().__init__(scene)
		
		self.font = QFont()
		self.font.setPixelSize(16)
		self.fontMetrics = QFontMetrics(self.font)
		
		self.color = Qt.black
		self.text = ""
		
	def setFontSize(self, size):
		self.font.setPixelSize(size)
		self.updateLabel()
		
	def setColor(self, color):
		self.color = color
		self.update()
		
	def setText(self, text):
		self.text = text
		self.updateLabel()
		
	def updateLabel(self):
		self.prepareGeometryChange()
		self.update()
		
	def boundingRect(self):
		rect = self.fontMetrics.boundingRect(self.text)
		rect.moveCenter(QPoint(0, 0))
		return QRectF(rect.adjusted(-2, -2, 2, 2))
		
	def paint(self, painter, option, widget):
		pen = QPen(self.color)
		if self.isSelected():
			pen.setColor(Qt.blue)
		painter.setPen(pen)

		painter.setFont(self.font)
		painter.drawText(self.boundingRect(), Qt.AlignCenter, self.text)

		
class LabelItem(LabelBase):
	def __init__(self, scene, label):
		super().__init__(scene)

		self.dragMode = DragMode.SPECIAL
		
		self.label = label
		self.connect(self.label.restored, self.addToScene)
		self.connect(self.label.deleted, self.removeFromScene)
		self.connect(self.label.textChanged, self.updateText)
		self.connect(self.label.angleChanged, self.updatePos)
		self.connect(self.label.distanceChanged, self.updatePos)
		self.connect(self.label.positionChanged, self.updatePos)
		
		self.distMin = 0
		self.distMax = 100
		
		self.updateText()
		self.updatePos()
		
	def delete(self):
		self.label.setText("")
		
	def drag(self, param):
		dx = param.pos.x() - self.label.x
		dy = param.pos.y() - self.label.y

		dist = math.sqrt(dx * dx + dy * dy)
		dist = min(max(dist, self.distMin), self.distMax)

		self.label.setAngle(math.atan2(dy, dx))
		self.label.setDistance(dist)
		
	def setRange(self, min, max):
		self.distMin = min
		self.distMax = max
		
	def updateText(self):
		self.setText(self.label.text)
		
	def updatePos(self):
		xoffs = math.cos(self.label.angle) * self.label.distance
		yoffs = math.sin(self.label.angle) * self.label.distance
		self.setPos(self.label.x + xoffs, self.label.y + yoffs)


class LooseArrowItem(EditorShape):
	def __init__(self, scene, style, arrow):
		super().__init__(scene, style.shapes["triangle"])
		
		self.arrow = arrow
		
		self.dragMode = DragMode.SPECIAL
		
		self.label = LabelItem(scene, arrow.label)
		self.label.setColor(QColor(128, 0, 255))
		self.label.setRange(0, 60)
		scene.addItem(self.label)
		
		self.connect(self.arrow.restored, self.addToScene)
		self.connect(self.arrow.deleted, self.removeFromScene)
		self.connect(self.arrow.positionChanged, self.updateArrow)
		self.connect(self.arrow.angleChanged, self.update)
		self.connect(self.arrow.transition.typeChanged, self.update)
		
		self.updateArrow()
		
	def updateArrow(self):
		self.setPos(self.arrow.x, self.arrow.y)
		self.update()
		
	def delete(self):
		self.arrow.delete()
		
	def drag(self, param):
		if isinstance(self.arrow.node.obj, UIPetriNet):
			if self.arrow.transition.channel:
				return
		dx = param.pos.x() - self.arrow.node.x
		dy = param.pos.y() - self.arrow.node.y
		self.arrow.setAngle(math.atan2(dy, dx))
		
	def paint(self, painter, option, widget):
		angle = self.arrow.angle
		if self.arrow.transition.type == TransitionType.INPUT:
			angle += math.pi
		
		painter.save()
		painter.rotate(angle * 180 / math.pi)
		super().paint(painter, option, widget)
		painter.restore()


class NodeBase(EditorShape):
	def __init__(self, scene, shape=None):
		super().__init__(scene, shape)
		self.dragMode = DragMode.NORMAL
		
	def drag(self, param):
		self.setPos(alignToGrid(param.pos))
		
	def checkCollisions(self):
		items = self.scene.collidingItems(self)
		if any(isinstance(item, NodeBase) for item in items):
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
			
			
class NodeFilter:
	def __init__(self, item):
		self.base = ShapeFilter(item)
		self.flashColor = QColor(128, 128, 255)
		self.item = item
		
	def applyToPen(self, pen):
		self.base.applyToPen(pen)
		
	def applyToBrush(self, brush):
		color = mergeColors(brush.color(), self.flashColor, self.item.flashValue)
		brush.setColor(color)
		
		self.base.applyToBrush(brush)
			
			
class NodeItem(NodeBase):
	def __init__(self, scene, shape, node):
		super().__init__(scene, shape)
		
		self.filter = NodeFilter(self)
		
		self.label = LabelItem(scene, node.label)
		scene.addItem(self.label)

		self.node = node
		self.connect(self.node.restored, self.addToScene)
		self.connect(self.node.deleted, self.removeFromScene)
		self.connect(self.node.positionChanged, self.updatePos)
		
		self.flashTimer = QTimer()
		self.flashTimer.setInterval(100)
		self.flashTimer.timeout.connect(self.updateFlash)
		
		self.flashValue = 0
		
		self.updatePos()
		
	def drag(self, param):
		pos = alignToGrid(param.pos)
		self.node.move(pos.x(), pos.y())

	def delete(self):
		self.flashTimer.stop()
		self.flashValue = 0
		
		self.node.delete()

	def updatePos(self):
		self.setPos(self.node.x, self.node.y)
		
	def updateFlash(self):
		self.flashValue -= .5
		if self.flashValue <= 0:
			self.flashTimer.stop()
			self.flashValue = 0
		
		self.update()
		
	def flash(self):
		self.flashValue = 1
		self.flashTimer.start()
		self.update()
