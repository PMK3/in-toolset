from PyQt5.QtCore import QXmlStreamWriter

class PNMLWriter:
	def __init__(self, net):
		self.net = net

	def save(self, file):
		placeStart = 2;
		transitionStart = placeStart + len(self.net.places)
		arcStart = transitionStart + len(self.net.transitions)

		stream = QXmlStreamWriter(file)
		stream.setAutoFormatting(True)
		stream.writeStartDocument()
		stream.writeStartElement("pnml")
		stream.writeStartElement("net")
		stream.writeAttribute("id", "0")
		stream.writeAttribute("type", "http://www.pnml.org/version-2009/grammar/pnmlcoremodel")
		stream.writeStartElement("page")
		stream.writeAttribute("id", "1")
		arcs = 0;
		for i, place in enumerate(self.net.places):
			id = str(placeStart + i)
			stream.writeStartElement("place")
			stream.writeAttribute("id", id)
			stream.writeEndElement()
		for i, transition in enumerate(self.net.transitions):
			id = str(transitionStart + i)
			stream.writeStartElement("transition")
			stream.writeAttribute("id", id)
			stream.writeEndElement()
			for place in transition.preset:
				stream.writeStartElement("arc")
				stream.writeAttribute("id", str(arcStart + arcs))
				stream.writeAttribute("source", str(placeStart + self.net.places.index(place)))
				stream.writeAttribute("target", id)
				stream.writeEndElement()
				arcs += 1
			for place in transition.postset:
				stream.writeStartElement("arc")
				stream.writeAttribute("id", str(arcStart + arcs))
				stream.writeAttribute("source", id)
				stream.writeAttribute("target", str(placeStart + self.net.places.index(place)))
				stream.writeEndElement()
				arcs += 1
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndDocument()
		file.close()
