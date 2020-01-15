import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="in-toolset",
	version="0.1.3",
	author="Example Author",
	author_email="author@example.com",
	description="An editor and simulator for industry workflow nets (inets), a model of interorganisational workflows based on petrinets",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/jakobwuhrer/in-toolset",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: GNU General Public License (GPL)",
		"Operating System :: OS Independent",
	],
	install_requires=[
		'pyqt5',
	],
	entry_points={
		'console_scripts': [
			'in-toolset=in_toolset.main:main',
		],
	},
	python_requires='>=3.6',
	include_package_data=True,
)
