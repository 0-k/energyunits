# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

from energyunits import __version__

# -- Project information -----------------------------------------------------

project = "energyunits"
copyright = "2024-2026, Martin Klein"
author = "Martin Klein"
release = __version__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
]

templates_path = []
highlight_language = "text"  # unlabelled code blocks are not Python
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"

# -- autodoc configuration ---------------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "description"

# -- myst configuration ------------------------------------------------------

myst_heading_anchors = 3
# README/CHANGELOG link to repository files by absolute URL; nothing to resolve locally.
suppress_warnings = ["myst.xref_missing"]
