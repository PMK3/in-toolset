
import sys

version = sys.version_info
if version < (3, 6):
	version = "%i.%i.%i" %(version.major, version.minor, version.micro)
	msg = "Your Python version is old (%s). Please upgrade to 3.6 or higher." %version
	raise RuntimeError(msg)


from ui.app import Application
from petri.petri import PetriNet
from petri.pnml import PNMLWriter
from PyQt5.QtCore import QFile
from PyQt5.QtCore import QIODevice

if __name__ == "__main__":
	petri = PetriNet()
	writer = PNMLWriter(petri)

	file = QFile("test.pnml")
	if file.open(QIODevice.WriteOnly):
		stream = writer.save(file)

	app = Application()
	app.start()
