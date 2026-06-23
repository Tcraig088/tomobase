
import tomobase
print(tomobase.core.proxy)


project = "Tomobase"
author = "Tim"

extensions = [
    "sphinx_thebe",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "myst_nb",
]

thebe_config = {
    "selector": ".highlight",
    "use_binder": False,
    "server_url": "http://127.0.0.1:8888",
    "server_token": "jupyterlab",
}

autosummary_generate = True
nb_execution_mode = "off" #force

add_module_names = False
autodoc_member_order = "bysource"

napoleon_google_docstring = True
napoleon_numpy_docstring = False

html_theme = "sphinx_rtd_theme"

