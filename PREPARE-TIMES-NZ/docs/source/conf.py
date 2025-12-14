# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# pylint:disable = all

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PREPARE-TIMES-NZ"
author = "Luke Searle, Achini Weerasinghe"
release = "v3.0.0"

html_show_copyright = False
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser", "sphinx.ext.mathjax", "sphinx.ext.autosectionlabel"]

myst_enable_extensions = ["colon_fence", "dollarmath", "auto_section_label"]

templates_path = ["_templates"]

exclude_patterns = []

myst_auto_section_label_prefix_document = True
# Table numbering
numfig = True
numfig_secnum_depth = 1

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "sphinx_book_theme"
# html_theme = "furo"
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "navbar_start": ["navbar-logo"],  # keep usual slots
    "logo": {
        "text": "PREPARE-TIMES-NZ",  # or a short title
    },
}
