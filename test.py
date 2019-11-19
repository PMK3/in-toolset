import sys

version = sys.version_info
if version < (3, 6):
	version = "%i.%i.%i" %(version.major, version.minor, version.micro)
	msg = "Your Python version is old (%s). Please upgrade to 3.6 or higher." %version
	raise RuntimeError(msg)

import unittest
from model.base import *

class TestPetriNet(unittest.TestCase):
    def testEnabledTransitions(self):
        net = PetriNet()
        self.assertTrue(len(net.enabledTransitions()) == 0)
        net.transitions.add(Transition())
        self.assertTrue(len(net.enabledTransitions()) == 1)
        net.places.add(Place())
        net.places[0].postset.add(net.transitions[0])
        net.transitions[0].preset.add(net.places[0])
        self.assertTrue(len(net.enabledTransitions()) == 0)
        net.places[0].give()
        self.assertTrue(len(net.enabledTransitions()) == 1)

    def testDeadlock(self):
        net = PetriNet()
        net.checkDeadlock()
        self.assertTrue(net.deadlock)
        net.transitions.add(Transition())
        net.checkDeadlock()
        self.assertFalse(net.deadlock)
        net.places.add(Place())
        net.places[0].postset.add(net.transitions[0])
        net.transitions[0].preset.add(net.places[0])
        net.checkDeadlock()
        self.assertTrue(net.deadlock)
        net.places[0].give()
        net.checkDeadlock()
        self.assertFalse(net.deadlock)

    def testTriggerRandom(self):
        net = PetriNet()
        net.transitions.add(Transition())
        net.places.add(Place())
        net.places[0].postset.add(net.transitions[0])
        net.transitions[0].preset.add(net.places[0])
        net.places[0].give()
        net.triggerRandom()
        self.assertTrue(net.places[0].tokens == 0)


if __name__ == '__main__':
    unittest.main()
