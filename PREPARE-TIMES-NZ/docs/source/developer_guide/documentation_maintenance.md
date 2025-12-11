# Documentation maintenance 


```{eval-rst}
.. admonition:: Recursion
   :class: note

   *Documentation must describe itself*
```

Model developers should update the methodology documentation to reflect changes to the code. This document describes some key features of the Markdown, Myst, and RST features used to build the documentation site. It is best to use consistent approaches where possible to minimise maintenance overhead. 


## Package setup

Packages used for the docs site are kept separate from other `PREPARE-TIMES-NZ` packages. You can install these to your poetry environment with 

```
poetry install --with docs
```

To deploy the site, packages and their dependencies were exported to `requirements.txt`, so that the external host environment functions properly. If you update or change the packages in the docs group, you can refresh the `requirements.txt` using: 

```
poetry export --with docs --without-hashes -o docs/requirements.txt
```

This is only required if the packages in the `docs` group have been changed or updated. 

```{eval-rst}
.. note::
   We might move RTD to reading directly from poetry - this means we can delete `requirements.txt` and skip this extra step.
```

## Indexes, toctrees, and structure

Documentation is captured in `docs/source`, and organised by directory. Each directory should contain an `index.md` file. 

The directory's `index.md` serves as the landing page for that directory, and should include a "toctree", or table of contents tree, which either links to documents in that directory, or other `index.md` files in nested directories below. 

An example toctree: 

```
```{toctree}
:maxdepth: 2 
:caption: Topics

overview_doc
subject_matter_1/index
subject_matter_2/index

Custom Heading for document <document_actual_filename>

```

Note that: 

- Each listed file should match a markdown file, relative to the path of `index.md`. The `.md` suffixes are not included. 

- The top level heading in each linked document will be used as the display name for that document in the TOC. 
    - For this reason, it's best that each document has only ONE top-level heading, so that each section in the navbar corresponds to a unique page. 

- If you wish to customise the heading, you can do so by adding a new heading here, then linking to your actual file by wrapping the address in `<>`. 
   


## Local testing 

When in `PREPARE-TIMES-NZ/docs`, you can build a local version of the documentation site by running: 

```
sphinx-autobuild -E source build/html
```

This command reads the files in `source` and builds the site in `build`. `build` is gitignored. It then serves the page locally at <http://127.0.0.1:8000>, and rebuilds the local site live as you edit your page's content. 



## Tables 

Our documentation includes a lot of tables of figures. We display these in markdown using a `list-table`. 

`list-table` code like this: 

```
```{list-table} Example Table
:header-rows: 1
:label: example-table
* - Heading 1
  - Heading 2
* - A
  - B
```

This renders as: 

```{list-table} Example Table
:header-rows: 1
:name: example-table
* - Heading 1
  - Heading 2
* - A
  - B
```

Note: 
- All tables are automatically given a number reference due to setting `numfig = True` in `conf.py`. The order of the table numbers depends on the order of each table's page in the toctree structure.
- The `:name:` parameter does nothing by itself, but allows us to reference the table in the text using `{ref}` or `{numref}`. 
    - ```See {numref}`example-table` for details``` renders as "See {numref}`example-table` for details".
    - ```See {ref}`example-table` for details``` renders as "See {ref}`example-table` for details".



### Automatic table conversion

It is quite a pain to write all of our tables out into this new format. A script was written in `docs/helpers` called `convert_table.py`. Steps to convert a table are as follows: 

1) Copy the table to convert into `docs/helpers/table_to_covert.csv`
1) Execute the script `docs/helpers/convert_table.py`

This prints the required text to your console and you can copy-paste into a markdown document.

```{eval-rst}
.. note::
   It's theoretically possible to automate much more of this - we could automatically load assumptions from raw data and convert these into MyST markdown tables. Then, the tables would update when our assumptions updated.
```

### Tables with merged cells

Sometimes, you might want to render a documentation table with merged cells. You could write some html for this, but you might prefer 


## Footnotes

Microsoft Word footnotes do not copy