
import sys

def main():
	version = sys.version_info
	if version < (3, 6):
		version = "%i.%i.%i" %(version.major, version.minor, version.micro)
		msg = "Your Python version is old (%s). Please upgrade to 3.6 or higher." %version
		raise RuntimeError(msg)

	from in_toolset.ui.app import Application

	app = Application()
	app.start()
