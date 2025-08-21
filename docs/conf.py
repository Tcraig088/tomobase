# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os, sys


sys.path.insert(0, os.path.abspath(".."))
print(sys.path)
project = 'tomobase'
copyright = '2025, Timothy Craig'
author = 'Timothy Craig'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_rtd_theme',
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",      # Google/Numpy docstrings
    "sphinx.ext.viewcode",
    "autodoc_traits",
    'sphinx.ext.intersphinx'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store'] 



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

autosummary_generate = True  
autosummary_imported_members = True
# Type hints appear in signature + description
autodoc_typehints = "both"
#napoleon_google_docstring = True
napoleon_numpy_docstring = True
numpydoc_show_class_members = False
napoleon_use_param = False
napoleon_use_ivar = True




myst_enable_extensions = ["deflist", "attrs_inline","substitution", "fieldlist"]
myst_fence_as_directive = [
    "toctree", "autosummary", "autodoc", "automodule", "autoclass",
    "autofunction", "currentmodule"
]

autodoc_mock_imports = [
    "napari", "qtpy", "PyQt5", "PySide6",
    "matplotlib", "stackview", "scipy", "cupy" # if your package imports it at top-level
]



html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

wrap_signatures_with_css = True

html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": -1,
    "includehidden": True,
    "flyout_display": "attached",
    "version_selector": True,
    "language_selector": True,
}