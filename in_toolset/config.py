"""The config module allows for configuration of the behaviour of in-toolset,
using a text file with key-value items as storage for the settings"""

import os

class Config:
	"""Manages basic configuration of the graphical interface as a list of key-value pairs"""
	types = {
		"ui.max_label_size": int,
		"ui.keyboard_scroll_speed": float
	}
	
	def __init__(self, filename):
		self.load(filename)
		
	def get(self, field):
		"""Get the value of `field`"""
		return self.settings[field]
	
	def set(self, field, value):
		"""Set the value of `field` to `value`"""
		if field not in self.types:
			raise ValueError("Unknown setting: %s" %field)
		self.settings[field] = self.types[field](value)
		
	def load(self, filename):
		"""Load the key-value pairs from the file `filename` into `self`"""
		self.settings = {}
		with open(filename) as f:
			for index, line in enumerate(f):
				line = line.strip()
				if line:
					if "=" in line:
						field, value = line.split("=", 1)
						self.set(field.strip(), value.strip())
					else:
						raise ValueError("Syntax error at line %i" %index)


config = Config(os.path.join(os.path.dirname(__file__), "data/config.txt"))

def get(field):
	"""Get the current value of the configuration field `field`"""
	return config.get(field)
