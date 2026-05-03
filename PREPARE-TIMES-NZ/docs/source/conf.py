# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# pylint:disable = all

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "TIMES-NZ"
author = "Luke Searle, Achini Weerasinghe"
release = "v3.0.6"

html_show_copyright = False
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.mathjax",
    "docxbuilder",
]

myst_enable_extensions = ["colon_fence", "dollarmath"]

templates_path = ["_templates"]

exclude_patterns = []

myst_auto_section_label_prefix_document = True
# Table numbering
numfig = True
numfig_secnum_depth = 0

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "sphinx_book_theme"
# html_theme = "furo"
html_theme = "pydata_sphinx_theme"
html_theme_options = {
    "navbar_start": ["navbar-logo"],  # keep usual slots
    "navbar_end": ["navbar-icon-links"],
    "logo": {
        "image_light": "_static/eeca.png",
        "text": "TIMES-NZ documentation",
    },
}

html_context = {
    "default_mode": "light",
}

# custom settings for table expansion

html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["table_expand.js"]


# -- Options for docx output -------------------------------------------------

# template usage
docx_style = "_templates/EECATemplate.docx"


version_for_word = f"TIMES-NZ {release}"

docx_documents = [
    # (startdocname, targetname, docproperties, toctree_only)
    (
        "model_methodology/electricity/index",
        "Electricity supply assumptions.docx",
        {"title": "Electricity supply assumptions", "subject": version_for_word},
        True,
    ),
]

# Make tables slightly nicer by avoiding spread across pages
docx_table_options = {"in_single_page": True}
