
from PyQt5.QtWidgets import *
from in_toolset.model.project import Project
from in_toolset.model.ui import UIPetriNet
from in_toolset.ui.industry import IndustryScene
from in_toolset.ui.enterprise import EnterpriseScene
from in_toolset.ui.window import MainWindow
from in_toolset.ui.view import Style
import sys
import os


class Application:
	def start(self):
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
