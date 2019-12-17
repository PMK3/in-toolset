from PyQt5.QtCore import QXmlStreamWriter
from .base import Place, Transition
from .ui import UIInternalArrow, UIChannelArrow

class PNMLWriter:
	"""Allows exporting a petrinet and a graph in PNML format"""

	def __init__(self, net, graph):
		self.net = net
		self.graph = graph

	def save(self, file):
		"""Write petrinet corresponding to `self.net` and `self.graph` to `file` in PNML format"""
		dictionary = {}
		id = 0
		stream = QXmlStreamWriter(file)
		stream.setAutoFormatting(True)
		stream.writeStartDocument()
		stream.writeStartElement("pnml")
		stream.writeStartElement("net")
		stream.writeAttribute("id", str(id))
		id += 1
		stream.writeAttribute("type", "http://www.pnml.org/version-2009/grammar/pnmlcoremodel")
		stream.writeStartElement("page")
		stream.writeAttribute("id", str(id))
		id += 1
		for enterprise in self.graph.nodes:
			graph = enterprise.obj.graph

			for node in graph.nodes:
				if isinstance(node.obj, Place):
					stream.writeStartElement("place")
				else:
					stream.writeStartElement("transition")
				stream.writeAttribute("id", str(id))
				dictionary[node.obj] = id
				id += 1
				stream.writeAttribute("name", str(node.label.text))
				if isinstance(node.obj, Place):
					stream.writeAttribute("initialMarking", str(node.obj.tokens))
				stream.writeEndElement()
			for arrow in graph.arrows:
				stream.writeStartElement("arc")
				stream.writeAttribute("id", str(id))
				id += 1
				stream.writeAttribute("source", str(dictionary[arrow.source.obj]))
				stream.writeAttribute("target", str(dictionary[arrow.target.obj]))
				stream.writeEndElement()
		for arrow in self.graph.arrows:
			stream.writeStartElement("place")
			shannel = str(id)
			stream.writeAttribute("id", channel)
			id += 1
			stream.writeAttribute("name", str(arrow.source.transition.message))
			stream.writeEndElement()

			stream.writeStartElement("arc")
			stream.writeAttribute("id", str(id))
			id += 1
			stream.writeAttribute("source", str(dictionary[arrow.source.transition]))
			stream.writeAttribute("target", channel)
			stream.writeEndElement()

			stream.writeStartElement("arc")
			stream.writeAttribute("id", str(id))
			id += 1
			stream.writeAttribute("source", channel)
			stream.writeAttribute("target", str(dictionary[arrow.target.transition]))
			stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndElement()
		stream.writeEndDocument()
		file.close()
