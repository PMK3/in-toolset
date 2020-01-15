
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from .view import EditorScene, EditorView
from .tools import ToolBar
from .menu import MenuBar
from . import settings
from ..common import Signal
from ..model.project import Project
import os


class IndustryItem(QListWidgetItem):
	def __init__(self, industry):
		super().__init__("Industry")
		self.obj = industry


class EnterpriseItem(QListWidgetItem):
	def __init__(self, node):
		super().__init__()

		self.obj = node
		self.obj.label.textChanged.connect(self.updateText)
		self.updateText()

	def updateText(self):
		name = self.obj.label.text
		if not name:
			name = "Enterprise"
		self.setText(name)


class NetListWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.enterpriseSelected = Signal()
		layout = QVBoxLayout()

		self.editIndustry = QPushButton("Go to industry net")
		self.editIndustry.clicked.connect(self.handleEditIndustry)
		layout.addWidget(self.editIndustry)

		self.listWidget = QListWidget()
		layout.addWidget(self.listWidget)

		self.setLayout(layout)
		self.show()

	def setProject(self, project):
		self.listWidget.clear()

		project.industry.graph.nodes.added.connect(self.addEnterprise)
		project.industry.graph.nodes.removed.connect(self.removeEnterprise)

		self.listWidget.addItem(IndustryItem(project.industry))
		for enterprise in project.industry.graph.nodes:
			self.addEnterprise(enterprise)

		self.listWidget.itemActivated.connect(self.handleItemActivated)

	def addEnterprise(self, enterprise):
		item = EnterpriseItem(enterprise)
		self.listWidget.addItem(item)

	def removeEnterprise(self, enterprise):
		for i in range(self.listWidget.count()):
			if self.listWidget.item(i).obj == enterprise:
				self.listWidget.takeItem(i)
				return

	def handleEditIndustry(self):
		industry = self.listWidget.item(0)
		self.listWidget.setCurrentItem(industry)
		self.enterpriseSelected.emit(industry.obj)

	def handleItemActivated(self, item):
		self.enterpriseSelected.emit(item.obj)


class MainWindow(QMainWindow):
	def __init__(self, style):
		super().__init__()
		self.newProject = Signal()
		self.loadProject = Signal()
		self.enterpriseSelected = Signal()

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
		self.nets.enterpriseSelected.connect(self.enterpriseSelected)
		netsDock = QDockWidget("Nets")
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
		menuBar.file.export.triggered.connect(self.handleExport)
		menuBar.file.exportAs.triggered.connect(self.handleExportAs)
		menuBar.file.quit.triggered.connect(self.close)
		menuBar.edit.selectAll.triggered.connect(self.scene.selectAll)
		menuBar.edit.setInitialMarking.triggered.connect(self.handleSetInitialMarking)
		menuBar.view.showGrid.toggled.connect(self.scene.setGridEnabled)
		menuBar.view.resetCamera.triggered.connect(self.view.resetTransform)
		menuBar.view.editIndustry.triggered.connect(self.selectIndustry)
		self.setMenuBar(menuBar)

	def setProject(self, project):
		self.nets.setProject(project)

		self.project = project
		self.project.filenameChanged.connect(self.updateWindowTitle)
		self.project.unsavedChanged.connect(self.updateWindowTitle)

		self.updateWindowTitle()

	def handleSetInitialMarking(self):
		self.project.industry.net.setInitialMarking()

	def selectIndustry(self):
		self.enterpriseSelected.emit(self.project.industry)

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
			self,
			"Save model",
			settings.getLastPath(),
			"Workflow model (*.flow);;All files (*.*)",
			"Workflow model (*.flow)",
			QFileDialog.DontUseNativeDialog
		)
		if not filename:
			return False
		if not '.' in filename:
			filename += ".flow"

		settings.setLastPath(os.path.dirname(filename))
		self.project.save(filename)
		return True

	def handleExport(self):
		if not self.project.exportname:
			return self.handleExportAs()
		self.project.export(self.project.exportname)
		return True

	def handleExportAs(self):
		exportname, filter = QFileDialog.getSaveFileName(
			self,
			"Export model",
			settings.getLastPath(),
			"PNML (*.pnml);;All files (*.*)",
			"PNML (*.pnml)",
			QFileDialog.DontUseNativeDialog
		)
		if not exportname:
			return False
		if not '.' in exportname:
			exportname += ".pnml"

		self.project.export(exportname)
		self.project.exportname = exportname
		return True
