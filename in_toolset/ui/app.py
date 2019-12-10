
from PyQt5.QtWidgets import *
from ..model.project import Project
from ..model.ui import UIPetriNet
from .industry import IndustryScene
from .enterprise import EnterpriseScene
from .window import MainWindow
from .view import Style
import sys
import os


class Application:
	"""The main class, corresponding to one instance of the graphical toolkit.
	It manages windows and allows for basic managing of projects."""

	def start(self):
		"""Start the graphical interface and the program itself"""
		self.app = QApplication(sys.argv)
		
		style = Style()
		style.load(os.path.join(os.path.dirname(__file__), "../data/style.json"))
		
		self.window = MainWindow(style)
		self.window.newProject.connect(self.createProject)
		self.window.loadProject.connect(self.createProject)
		self.window.enterpriseSelected.connect(self.switchToScene)
		self.window.show()
		
		self.industryScene = IndustryScene(style, self.window)
		self.industryScene.enterpriseSelected.connect(self.switchToScene)

		self.enterpriseScene = EnterpriseScene(style, self.window)
		
		self.currentScene = None
		
		self.createProject()
		
		self.app.exec()
		
	def createProject(self, filename=None):
		"""Create a new project or load an existing one"""

		self.project = Project()
		if filename:
			try:
				self.project.load(filename)
			except:
				import traceback
				traceback.print_exc()
				
				text = "An error occurred while loading this file (it may be corrupted)."
				QMessageBox.warning(self.window, "Error", text)
				return
			
		self.industry = self.project.industry
			
		self.window.setProject(self.project)
		self.switchToScene(self.industry)
		
	def switchToScene(self, object):
		if self.currentScene:
			self.currentScene.cleanup()
		
		if object == self.industry:
			self.currentScene = self.industryScene
			self.currentScene.load(self.industry)
		else:
			self.currentScene = self.enterpriseScene
			self.currentScene.load(self.industry, object)
