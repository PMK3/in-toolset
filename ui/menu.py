
from PyQt5.QtWidgets import *


class Action(QAction):
	def __init__(self, text, shortcut):
		super().__init__(text)
		self.setShortcut(shortcut)


class FileMenu(QMenu):
	def __init__(self):
		super().__init__("File")
		
		self.new = Action("New", "Ctrl+N")
		self.open = Action("Open", "Ctrl+O")
		self.save = Action("Save", "Ctrl+S")
		self.saveAs = Action("Save as", "Ctrl+Shift+S")
		self.quit = Action("Quit", "Ctrl+Q")
		
		self.addAction(self.new)
		self.addAction(self.open)
		self.addAction(self.save)
		self.addAction(self.saveAs)
		self.addAction(self.quit)
		
		
class EditMenu(QMenu):
	def __init__(self):
		super().__init__("Edit")
		
		self.selectAll = Action("Select all", "Ctrl+A")
		
		self.addAction(self.selectAll)


class MenuBar(QMenuBar):
	def __init__(self):
		super().__init__()
		
		self.file = FileMenu()
		self.edit = EditMenu()
		
		self.addMenu(self.file)
		self.addMenu(self.edit)
