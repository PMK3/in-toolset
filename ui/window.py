
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from ui.view import EditorScene, EditorView
from ui.tools import ToolBar
from ui.menu import MenuBar
from ui import settings
from common import Signal
import os


class EnterpriseItem(QListWidgetItem):
	def __init__(self, enterprise):
		super().__init__()
		
		self.enterprise = enterprise
		self.enterprise.labelChanged.connect(self.updateLabel)
		self.enterprise.deleted.connect(lambda: self.setHidden(True))
		
		self.updateLabel()
		
	def updateLabel(self):
		name = self.enterprise.label
		if not name:
			name = "Enterprise"
		self.setText(name)


class NetListWidget(QListWidget):
	def setProject(self, project):
		self.clear()
		
		project.industry.enterprises.added.connect(self.addEnterprise)
		
		self.addItem("Industry")
		for enterprise in project.industry.enterprises:
			self.addEnterprise(enterprise)
			
	def addEnterprise(self, enterprise):
		item = EnterpriseItem(enterprise)
		self.addItem(item)


class MainWindow(QMainWindow):
	def __init__(self, style):
		super().__init__()
		self.newProject = Signal()
		self.loadProject = Signal()
		self.selectEnterprise = Signal()
		
		self.setContextMenuPolicy(Qt.PreventContextMenu)

		self.resize(1080, 720)

		self.toolbar = ToolBar(style)
		self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
				
		self.scene = EditorScene()
		self.view = EditorView(self.scene)
		self.setCentralWidget(self.view)

		self.settings = QDockWidget("Settings")
		self.settings.setFixedWidth(200)
		self.settings.setFeatures(QDockWidget.DockWidgetMovable)
		self.settings.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
		self.addDockWidget(Qt.RightDockWidgetArea, self.settings)
		
		self.nets = NetListWidget()
		self.nets.itemActivated.connect(self.handleEnterpriseSelected)
		netsDock = QDockWidget("Enterprises")
		netsDock.setFixedWidth(200)
		netsDock.setFeatures(QDockWidget.DockWidgetMovable)
		netsDock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
		netsDock.setWidget(self.nets)
		self.addDockWidget(Qt.RightDockWidgetArea, netsDock)

		menuBar = MenuBar()
		menuBar.file.new.triggered.connect(self.handleNew)
		menuBar.file.open.triggered.connect(self.handleOpen)
		menuBar.file.save.triggered.connect(self.handleSave)
		menuBar.file.saveAs.triggered.connect(self.handleSaveAs)
		menuBar.file.quit.triggered.connect(self.close)
		menuBar.edit.selectAll.triggered.connect(self.scene.selectAll)
		menuBar.view.showGrid.toggled.connect(self.scene.setGridEnabled)
		menuBar.view.resetCamera.triggered.connect(self.view.resetTransform)
		menuBar.view.editIndustry.triggered.connect(lambda: self.selectEnterprise(-1))
		self.setMenuBar(menuBar)
		
	def setProject(self, project):
		self.nets.setProject(project)
		
		self.project = project
		self.project.filenameChanged.connect(self.updateWindowTitle)
		self.project.unsavedChanged.connect(self.updateWindowTitle)
		
		self.updateWindowTitle()
		
	def handleEnterpriseSelected(self, item):
		if isinstance(item, EnterpriseItem):
			self.selectEnterprise(item.enterprise.id)
		else:
			self.selectEnterprise(-1)

	def closeEvent(self, e):
		if self.checkUnsaved():
			e.accept()
		else:
			e.ignore()

	def keyPressEvent(self, e):
		self.toolbar.handleKey(e.key())

	def updateWindowTitle(self):
		name = self.project.filename
		if name is None:
			name = "untitled"
		self.setWindowTitle("Petri - %s%s" %(name, "*" * self.project.unsaved))

	def checkUnsaved(self):
		if self.project.unsaved:
			msg = "This model has unsaved changes. Do you want to save them?"
			buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
			result = QMessageBox.question(self, "Save changes?", msg, buttons)
			if result == QMessageBox.Save: return self.handleSave()
			elif result == QMessageBox.Discard: return True
			else: return False
		return True

	def handleNew(self):
		if self.checkUnsaved():
			self.newProject.emit()
			return True
		return False

	def handleOpen(self):
		if not self.checkUnsaved():
			return False

		filename, filter = QFileDialog.getOpenFileName(
			self, "Load model", settings.getLastPath(),
			"Workflow model (*.flow);;All files (*.*)"
		)
		if not filename:
			return False

		settings.setLastPath(os.path.dirname(filename))
		self.loadProject.emit(filename)
		return True

	def handleSave(self):
		if not self.project.filename:
			return self.handleSaveAs()
		self.project.save(self.project.filename)
		return True

	def handleSaveAs(self):
		filename, filter = QFileDialog.getSaveFileName(
			self, "Save model", settings.getLastPath(),
			"Workflow model (*.flow);;All files (*.*)"
		)
		if not filename:
			return False

		settings.setLastPath(os.path.dirname(filename))
		self.project.save(filename)
		return True