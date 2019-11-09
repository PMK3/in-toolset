import sys

version = sys.version_info
if version < (3, 6):
	version = "%i.%i.%i" %(version.major, version.minor, version.micro)
	msg = "Your Python version is old (%s). Please upgrade to 3.6 or higher." %version
	raise RuntimeError(msg)

import unittest
from ui.app import Application
from model.base import PetriNet
from model.pnml import PNMLWriter
from PyQt5.QtCore import QFile
from PyQt5.QtCore import QIODevice
from PyQt5.QtCore import QTest 
from PyQt5.QtCore import Qt
# not sure I need all this?

def test_defaults(self):
    # test the UI in its default state
    # self.assertEqual(self.form.ui.???.value(), ???)

