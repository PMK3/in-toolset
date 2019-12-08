import os

class Config:
	types = {
		"ui.max_label_size": int,
		"ui.keyboard_scroll_speed": float
	}
	
	def __init__(self, filename):
		self.load(filename)
		
	def get(self, field): return self.settings[field]
	
	def set(self, field, value):
		if field not in self.types:
			raise ValueError("Unknown setting: %s" %field)
		self.settings[field] = self.types[field](value)
		
	def load(self, filename):
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
	return config.get(field)
