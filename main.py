
import sys

version = sys.version_info
if version < (3, 6):
	version = "%i.%i.%i" %(version.major, version.minor, version.micro)
	msg = "Your Python version is old (%s). Please upgrade to 3.6 or higher." %version
	raise RuntimeError(msg)


from ui.app import Application

if __name__ == "__main__":
	app = Application()
	app.start()
