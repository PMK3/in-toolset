from PyQt5.QtCore import QXmlStreamWriter

class PNMLWriter:
	def __init__(self, net):
		self.net = net

	def save(self, file):
		stream = QXmlStreamWriter(file)
		stream.setAutoFormatting(True)
		stream.writeStartDocument()
		stream.writeStartElement("pnml")
		stream.writeStartElement("net")
		stream.writeAttribute("id", "0")
		stream.writeAttribute("type", "http://www.pnml.org/version-2009/grammar/pnmlcoremodel")
		stream.writeStartElement("page")
		stream.writeAttribute("id", "0")
		stream.writeStartElement("place")
		stream.writeAttribute("id", "0")
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndDocument()
		file.close()
