# in-toolset

in-toolset is an editor and (basic) simulator for industry workflow nets (inets), a model of interorganisational workflows based on petrinets.

Currently, the tool supports editing and manually simulating these industry workflows, and exporting industry nets as PNML petri nets,
but support for checking for bisimilarity using LTSmin and for automatically generating a subset of the language of triggering sequences of an inet in XES is planned, as is a model of "domains" for organisations and messages.

in-toolset has cross-platform support and has been verified to work on linux, MacOS, and windows.
It should work on most systems with python3.6 or newer and pyqt5.
The recommended way to install it is to run `pip install in-toolset`, this makes a command-line tool `in-toolset` available which starts the graphical editor.

The toolset was originally created by: Daniel Otten, Jakob Wuhrer, Julia Bolt, Ricardo Schaaf, and Yannik Marchand, on behalf of Pieter Kwantes of Leiden University.

It is provided here licensed under the GNU General Public License v3.0.

Documentation can be found at https://in-toolset.rtfd.org
