from PyQt5.QtCore import QXmlStreamWriter

class PNMLWriter:
	def __init__(self, net):
		self.net = net

	def save(self, file):
		stream = QXmlStreamWriter(file)
		stream.setAutoFormatting(True)
		stream.writeStartDocument()
		stream.writeStartElement("pnml.element")
		stream.writeCharacters('a')
		stream.writeEndElement()
		stream.writeEndDocument()
		return stream
