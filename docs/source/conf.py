# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

project = 'Clixon Python API'
copyright = '2024, Kristofer Hallin'
author = 'Kristofer Hallin'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.viewcode',
              'sphinx.ext.autodoc', "sphinx.ext.autodoc.typehints", "sphinx.ext.napoleon", "sphinx_rtd_theme"]
autodoc_typehints = 'description'
html_theme = 'sphinx_rtd_theme'
templates_path = ['_templates']
exclude_patterns = []
napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']
exclude_patterns = ['args.py']

path = "../../"

sys.path.insert(0, os.path.abspath(path))

try:
    import clixon
except ImportError:
    print("Clixon not installed")
    sys.exit(1)
