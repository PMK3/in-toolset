
from PyQt5.QtWidgets import *


class Action(QAction):
	def __init__(self, text, shortcut, checkable=False):
		super().__init__(text)
		self.setShortcut(shortcut)
		self.setCheckable(checkable)


class FileMenu(QMenu):
	def __init__(self):
		super().__init__("File")

		self.new = Action("New", "Ctrl+N")
		self.open = Action("Open", "Ctrl+O")
		self.save = Action("Save", "Ctrl+S")
		self.saveAs = Action("Save as", "Ctrl+Shift+S")
		self.export = Action("Export", "Ctrl+E")
		self.exportAs = Action("Export as", "Ctrl+Shift+E")
		self.quit = Action("Quit", "Ctrl+Q")

		self.addAction(self.new)
		self.addAction(self.open)
		self.addAction(self.save)
		self.addAction(self.saveAs)
		self.addAction(self.export)
		self.addAction(self.exportAs)
		self.addAction(self.quit)


class EditMenu(QMenu):
	def __init__(self):
		super().__init__("Edit")

		self.selectAll = Action("Select all", "Ctrl+A")
		self.setInitialMarking = Action("Set Initial Marking", "Ctrl+M")

		self.addAction(self.selectAll)
		self.addAction(self.setInitialMarking)


class ViewMenu(QMenu):
	def __init__(self):
		super().__init__("View")

		self.showGrid = Action("Show grid", "Ctrl+1", True)
		self.showGrid.setChecked(True)
		self.resetCamera = Action("Reset camera", "Ctrl+R")
		self.editIndustry = Action("Go to industry net", "Ctrl+I")

		self.addAction(self.showGrid)
		self.addSeparator()
		self.addAction(self.resetCamera)
		self.addAction(self.editIndustry)


class MenuBar(QMenuBar):
	def __init__(self):
		super().__init__()

		self.file = FileMenu()
		self.edit = EditMenu()
		self.view = ViewMenu()

		self.addMenu(self.file)
		self.addMenu(self.edit)
		self.addMenu(self.view)
