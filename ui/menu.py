
from PyQt5.QtWidgets import *


class Action(QAction):
	def __init__(self, text, shortcut):
		super().__init__(text)
		self.setShortcut(shortcut)


class FileMenu(QMenu):
	def __init__(self):
		super().__init__("File")
		
		self.quit = Action("Quit", "Ctrl+Q")
		
		self.addAction(self.quit)


class MenuBar(QMenuBar):
	def __init__(self):
		super().__init__()
		
		self.file = FileMenu()
		
		self.addMenu(self.file)
