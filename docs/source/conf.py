import os
import sys
import sphinx_rtd_theme
sys.path.insert(0, os.path.abspath('../..'))

project = 'in-toolset'
copyright = '2019, Daniel Otten, Jakob Wuhrer, Julia Bolt, Ricardo Schaaf, and Yannik Marchand'
author = 'Daniel Otten, Jakob Wuhrer, Julia Bolt, Ricardo Schaaf, and Yannik Marchand'
release = '0.1.0'

extensions = ['sphinx.ext.autodoc']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
templates_path = ['_templates']
html_static_path = ['_static']
