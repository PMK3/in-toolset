
from PyQt5.QtWidgets import *
from petri.project import Project
from ui.industry import IndustryScene
from ui.enterprise import EnterpriseScene
from ui.window import MainWindow
from ui.view import Style
import sys


class Application:
	def start(self):
		self.app = QApplication(sys.argv)
		
		style = Style()
		style.load("data/style.json")
		
		self.window = MainWindow(style)
		self.window.newProject.connect(self.createProject)
		self.window.loadProject.connect(self.createProject)
		self.window.selectEnterprise.connect(self.switchToScene)
		self.window.show()
		
		self.industry = IndustryScene(style, self)
		self.enterprise = EnterpriseScene(style, self)
		
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
			
		self.industryNet = self.project.industry
			
		self.window.setProject(self.project)
		self.switchToScene(-1)
		
	def switchToScene(self, index):
		if self.currentScene:
			self.currentScene.cleanup()
		
		if index == -1:
			self.industry.load(self.industryNet)
			self.currentScene = self.industry
		else:
			self.enterprise.load(self.industryNet.enterprises[index])
			self.currentScene = self.enterprise

	def switchToEnterprise(self, enterprise):
		if self.currentScene:
			self.currentScene.cleanup()

		self.enterprise.load(enterprise)
		self.currentScene = self.enterprise
