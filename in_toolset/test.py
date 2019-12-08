import sys

version = sys.version_info
if version < (3, 6):
	version = "%i.%i.%i" %(version.major, version.minor, version.micro)
	msg = "Your Python version is old (%s). Please upgrade to 3.6 or higher." %version
	raise RuntimeError(msg)

import unittest
from in_toolset.model.base import *
from in_toolset.model.ui import *

class TestUITransition(unittest.TestCase):

    def testSetType(self):
        net = PetriNet()
        net.transitions.add(UITransition())
        net.transitions[0].setType("m1")
        self.assertTrue(net.transitions[0].type == "m1")

    def testSetMessage(self):
        net = PetriNet()
        net.transitions.add(UITransition())
        net.transitions[0].setMessage("m1")
        self.assertTrue(net.transitions[0].message == "m1")

    def testSetChannel(self):
        net = PetriNet()
        net.transitions.add(UITransition())
        net.transitions[0].setChannel("m1")
        self.assertTrue(net.transitions[0].channel == "m1")


class TestPlace(unittest.TestCase):

    def testSetTokens(self):
        net = PetriNet()
        net.places.add(Place())
        net.places[0].setTokens(9001)
        self.assertTrue(net.places[0].tokens > 9000)
        self.assertFalse(net.places[0].tokens > 9001)

    def testGive(self):
        net = PetriNet()
        net.places.add(Place())
        net.places[0].give()
        self.assertTrue(net.places[0].tokens == 1)
        net.places[0].give()
        self.assertTrue(net.places[0].tokens == 2)

    def testTake(self):
        net = PetriNet()
        net.places.add(Place())
        net.places[0].setTokens(2)
        self.assertTrue(net.places[0].tokens == 2)
        net.places[0].take()
        self.assertFalse(net.places[0].tokens > 1)
        self.assertTrue(net.places[0].tokens > 0)


class TestTransition(unittest.TestCase):

    def testCheckEnabled(self):
        net = PetriNet()
        net.transitions.add(Transition())
        self.assertTrue(net.transitions[0].checkEnabled())
        net.places.add(Place())
        net.places[0].postset.add(net.transitions[0])
        net.transitions[0].preset.add(net.places[0])
        self.assertFalse(net.transitions[0].checkEnabled())
        net.places[0].give()
        self.assertTrue(net.transitions[0].checkEnabled())

    def testUpdateEnabled(self):
        net = PetriNet()
        net.transitions.add(Transition())
        net.places.add(Place())
        net.places[0].postset.add(net.transitions[0])
        net.transitions[0].preset.add(net.places[0])
        net.transitions[0].updateEnabled()
        self.assertFalse(net.transitions[0].enabled)
        net.places[0].give()
        net.transitions[0].updateEnabled()
        self.assertTrue(net.transitions[0].enabled)

    def testTrigger(self):
        net = PetriNet()
        net.transitions.add(Transition())
        net.places.add(Place())
        net.places[0].postset.add(net.transitions[0])
        net.transitions[0].preset.add(net.places[0]) #place 0 points to transition 0
        net.places.add(Place())
        net.transitions[0].postset.add(net.places[1])
        net.places[1].preset.add(net.transitions[0]) #transition 0 points to place 1
        net.places[0].give()
        self.assertTrue(net.places[0].tokens == 1)
        self.assertTrue(net.places[1].tokens == 0)
        net.transitions[0].trigger()
        self.assertTrue(net.places[0].tokens == 0)
        self.assertTrue(net.places[1].tokens == 1)


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

    def testSetInitialMarking(self):
        net = PetriNet()
        net.places.add(Place())
        net.places.add(Place())
        self.assertTrue(net.places[0].tokens == 0)
        self.assertTrue(net.places[1].tokens == 0)
        net.setInitialMarking()
        self.assertTrue(net.places[0].tokens == 1)
        self.assertTrue(net.places[1].tokens == 1)



if __name__ == '__main__':
    unittest.main()
