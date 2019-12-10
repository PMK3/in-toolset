
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ..common import Signal
import string
import json
import os
		
		
KeyCodes = {string.ascii_uppercase[i]: Qt.Key_A + i for i in range(26)}
		

class Tool:
	def __init__(self, data):
		self.name = data["name"]
		self.shape = data["shape"]
		self.text = data["text"]
		self.tooltip = data["tooltip"]
		self.shortcut = KeyCodes[data["shortcut"]]
		
		
class ToolGroup:
	def __init__(self):
		self.name = None
		self.shape = None
		self.tools = []
		

class ToolList:
	def __init__(self):
		self.groups = {}
		self.tools = {}
		
	def load(self, filename):
		with open(filename) as f:
			data = json.load(f)
		
		for info in data["tools"]:
			tool = Tool(info)
			self.tools[tool.name] = tool
			
		for info in data["groups"]:
			group = ToolGroup()
			group.name = info["name"]
			group.shape = info["shape"]
			for name in info["tools"]:
				group.tools.append(self.tools[name])
			self.groups[group.name] = group
			
			
class ToolButton(QToolButton):
	def __init__(self, style, tool):
		super().__init__()
		self.setToolTip(tool.tooltip)

		self.setFixedWidth(80)
		self.setFixedHeight(80)
		self.setCheckable(True)
		self.shape = style.shapes[tool.shape]
		self.text = tool.text
		self.name = tool.name

		self.font = QFont()
		self.font.setPixelSize(16)
		self.textRect = QRectF(0, 55, 80, 20)

		self.clicked.connect(lambda: self.setChecked(True))

	def paintEvent(self, e):
		super().paintEvent(e)
		
		painter = QPainter()
		painter.begin(self)
		
		painter.translate(40, 30)
		self.shape.draw(painter)
		painter.resetTransform()

		painter.setFont(self.font)
		painter.drawText(self.textRect, Qt.AlignCenter, self.text)

		painter.end()
		
		
class ToolBarHeader(QWidget):
	def __init__(self, style, group):
		super().__init__()
		self.setMinimumWidth(40)
		self.setMinimumHeight(40)
		self.shape = style.shapes[group.shape]
		self.orientation = Qt.Vertical
		
	def setOrientation(self, orientation):
		self.orientation = orientation
		self.update()
		
	def paintEvent(self, e):
		super().paintEvent(e)
		
		painter = QPainter()
		painter.begin(self)
		
		painter.save()
		
		if self.orientation == Qt.Horizontal:
			gradient = QLinearGradient(0, 0, self.width(), 0)
		else:
			gradient = QLinearGradient(0, 0, 0, self.height())
		gradient.setColorAt(0, QColor(160, 160, 160))
		gradient.setColorAt(1, QPalette().color(QPalette.Window))
		
		painter.setPen(Qt.NoPen)
		painter.setBrush(gradient)
		painter.drawRect(self.rect())
		
		painter.restore()
		
		painter.translate(self.rect().center())
		self.shape.draw(painter)
		
		painter.end()


class ToolBar(QToolBar):
	"""The menu bar that can be used to select the active tools for left and right mouse buttons"""
	def __init__(self, style):
		super().__init__()
		self.selectionChanged = Signal()
		
		self.setFloatable(False)
		
		self.style = style
		
		self.tools = ToolList()
		self.tools.load(os.path.join(os.path.dirname(__file__), "../data/tools.json"))
		
		self.reset()
		
	def reset(self):
		"""Empty the toolbar"""
		self.clear()
		
		self.groups = {}
		self.buttons = {}
		self.shortcuts = {}
		
	def addGroup(self, name):
		"""Make a group of tools availabe, so that their corresponding tool buttons may be visible in the toolbar."""
		group = self.tools.groups[name]
		
		header = ToolBarHeader(self.style, group)
		self.orientationChanged.connect(header.setOrientation)
		self.addWidget(header)
		
		buttonGroup = QButtonGroup(self)
		buttonGroup.buttonToggled.connect(self.handleToggled)
		for tool in group.tools:
			button = ToolButton(self.style, tool)
			buttonGroup.addButton(button)
			self.addWidget(button)
			self.buttons[tool.name] = button
			self.shortcuts[tool.shortcut] = tool.name
		
		self.groups[group.name] = buttonGroup
		
	def handleToggled(self, button, state):
		if state:
			self.selectionChanged.emit(button.name)

	def handleKey(self, key):
		if key in self.shortcuts:
			self.selectTool(self.shortcuts[key])
			
	def selectTool(self, name):
		"""Select and enable the tool with name `name`"""
		self.buttons[name].setChecked(True)

	def currentTool(self, group):
		"""Return the currently active tool for a specific group, if there is an active too in said group.
		Otherwise, return -1."""
		button = self.groups[group].checkedButton()
		if button:
			return button.name
		return -1
