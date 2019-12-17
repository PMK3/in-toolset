
from PyQt5.QtCore import QSettings

def getLastPath(): return settings.value("LastPath", "")
def setLastPath(path): settings.setValue("LastPath", path)

settings = QSettings("SE2019", "in-toolset")
