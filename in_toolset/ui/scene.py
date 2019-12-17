
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from ..common import Signal, SignalListener


class SeparatorLine(QFrame):
	def __init__(self):
		super().__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)


class SettingsWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setStyleSheet("font-size: 16px")
		
		self.layout = QFormLayout(self)
		
		self.signals = SignalListener()
		
	def connect(self, signal, callback):
		self.signals.connect(signal, callback)
		
	def cleanup(self):
		self.signals.disconnect()
		
	def addSeparator(self):
		self.layout.addRow(SeparatorLine())
		
	def addField(self, label, widget):
		self.layout.addRow(label, widget)
		
	def addWidget(self, widget):
		self.layout.addRow(widget)
		
		
class GeneralSettings(SettingsWidget):
	def __init__(self, net):
		super().__init__()
		
		self.net = net.net
		self.connect(self.net.deadlockChanged, self.updateDeadlock)
		
		self.label = QLabel("No item selected")
		self.label.setAlignment(Qt.AlignCenter)
		
		self.triggerRandom = QPushButton("Trigger random")
		self.triggerRandom.setEnabled(not self.net.deadlock)
		self.triggerRandom.clicked.connect(self.net.triggerRandom)
		
		self.addWidget(self.label)
		self.addWidget(self.triggerRandom)
		
	def setSelection(self, items):
		if len(items) == 0:
			self.label.setText("No item selected")
		elif len(items) == 1:
			self.label.setText("1 item selected")
		else:
			self.label.setText("%i items selected" %len(items))
			
	def updateDeadlock(self):
		self.triggerRandom.setEnabled(not self.net.deadlock)


class PetriScene:
	def __init__(self, style, window):
		self.style = style
		self.window = window
		
		self.toolbar = self.window.toolbar
		self.scene = self.window.scene
		self.view = self.window.view
		self.settings = self.window.settings
		
		self.enterpriseSelected = Signal()
		
		self.signals = SignalListener()
		
	def loadPetriNet(self, net):
		self.scene.clear()
		self.view.resetTransform()
		
		self.net = net
		self.connect(net.graph.nodes.added, self.addNode)
		self.connect(net.graph.arrows.added, self.addArrow)
		self.connect(net.graph.looseArrows.added, self.addLooseArrow)
		
		for node in net.graph.nodes:
			self.addNode(node)
		for arrow in net.graph.arrows:
			self.addArrow(arrow)
		for arrow in net.graph.looseArrows:
			self.addLooseArrow(arrow)
		
		self.controller = self.createController()
		self.scene.setController(self.controller)
		
		self.connect(self.scene.selectionChanged, self.updateSelection)
		
		self.view.setHandDrag(False)
		
		self.toolbar.reset()
		self.toolbar.addGroup("common")
		self.toolbar.selectTool("selection")
		self.registerTools(self.toolbar)
		self.connect(self.toolbar.selectionChanged, self.updateTool)
		
		self.generalSettings = self.createGeneralSettings()
		self.settings.setWidget(self.generalSettings)
		
	def cleanup(self):
		self.signals.disconnect()
		
		self.generalSettings.cleanup()
		if self.settings.widget() != self.generalSettings:
			self.settings.widget().cleanup()
		self.scene.cleanup()
		
	def updateSelection(self):
		if self.settings.widget() != self.generalSettings:
			self.settings.widget().cleanup()

		items = self.scene.selectedItems()
		widget = self.createSettingsWidget(items)
		if widget:
			self.settings.setWidget(widget)
		else:
			self.generalSettings.setSelection(items)
			self.settings.setWidget(self.generalSettings)
		
	def updateTool(self, tool):
		if tool == "selection":
			self.view.setHandDrag(False)
		elif tool == "hand":
			self.view.setHandDrag(True)
		
	def connect(self, signal, callback):
		self.signals.connect(signal, callback)
		
	def registerTools(self, toolbar): pass
	
	def addNode(self, node): pass
	def addArrow(self, arrow): pass
	def addLooseArrow(self, arrow): pass
	
	def createGeneralSettings(self): return GeneralSettings(self.net)
	def createSettingsWidget(self, items): return None
	
	def createController(self): raise NotImplementedError

