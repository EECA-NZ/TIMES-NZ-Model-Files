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



## Reformatting 

You need to establish headings in Markdown, which don't immediately translate if you copy text into Markdown. Just label the page's title with `#` and subheadings with `##`, `###`, and so on. It's best to have only a single top-level heading per document, as this heading is used by the site's contents tables and navigation pane. It might also be useful to break documentation down into several pages, linked with an `index.md` toctree.

Paragraph breaks in Word do not immediately render as paragraph breaks in MyST Markdown, and instead just carry on on the same line. You need to add an additional linebreak. 

**Incorrect:**

```
Some text
New paragraph
```
Some text
New paragraph

**Correct:**

```
Some text

New paragraph
```
Some text

New paragraph

## Features

The following are some methods or features you might use when writing documentation. There are also examples in the existing source documents.

### Tables 

Our documentation includes a lot of tables of figures. We display these in markdown using a `list-table`. 

`list-table` code like this: 

```
```{list-table} Example Table
:header-rows: 1
:name: tab-example
* - Heading 1
  - Heading 2
* - A
  - B
```
```{list-table} Example Table
:header-rows: 1
:name: tab-example
* - Heading 1
  - Heading 2
* - A
  - B
```

Note: 
- All tables are automatically given a number reference due to setting `numfig = True` in `conf.py`. The order of the table numbers depends on the order of each table's page in the toctree structure.
- The `:name:` parameter does nothing by itself, but allows us to reference the table in the text using `{ref}` or `{numref}`. 
    - ```See {numref}`tab-example` for details``` renders as "See {numref}`tab-example` for details".
    - ```See {ref}`tab-example` for details``` renders as "See {ref}`tab-example` for details".

These table references work across the entire site, not just that page. So it's good to keep clear variable names for each table's :name:, and they can be linked from anywhere else.


#### Automatic table conversion

Converting tables to `list-table` format manually is not a good idea, as it is tedious and annoying. Instead, recommended steps to convert a table are as follows: 

1) Copy the table to convert into `docs/helpers/table_to_covert.csv`. This file is not tracked or created by git, so you will need to create it first. 
1) Execute the script `docs/helpers/convert_table.py`

This prints the required text to your console and you can copy-paste into a markdown document.

```{eval-rst}
.. note::
   It's theoretically possible to automate much more of this - we could automatically load assumptions from raw data and convert these into MyST markdown tables. Then, the tables would update when our assumptions updated.
```

#### Tables with merged cells

Sometimes, you might want to render a documentation table with merged cells. This is possible, but inelegant. You can use `rst` (or `{eval-rst}` in markdown) to accomplish this. Ensure it's declared as `.. table:` so that standard table features still apply.

Here's an example: 
```
```{eval-rst}  
.. table:: Example with merged cells
    :name: tab-merged

    +-------------------------+-------------------------+
    |   Main Heading (merged)                           |
    +-------------------------+-------------------------+
    | Subheading 1            | Subheading 2            |
    +=========================+=========================+
    | A                       | B                       |
    +-------------------------+-------------------------+
```

```{eval-rst}  
.. table:: Example with merged cells
    :name: tab-merged

    +-------------------------+-------------------------+
    |   Main Heading (merged)                           |
    +-------------------------+-------------------------+
    | Subheading 1            | Subheading 2            |
    +=========================+=========================+
    | A                       | B                       |
    +-------------------------+-------------------------+
```
You must tab-indent the table and `:name:`. The spacing is very particular. If anything is not placed precisely, the table will fail to render. This is often more trouble than it's worth. It might be better to just leave some cells null, like in {ref}`the battery page <storage-key-assumptions>`.

#### Expandable (large) tables 

Sometimes we want to add a table but it doesn't quite fit in the theme's banner, and a user will have to scroll to see it all. 

This is not ideal UX, so we added a custom class called 'expandable-table' for the Myst list tables. simply add the class to your list table, and it will render with the option to "pop out" and take up a full screen. 

```
```{list-table} Example Table (Expandable)
:header-rows: 1
:class: expandable-table
:name: tab-example-expandable
* - Heading 1
  - Heading 2
* - A
  - B
```

```{list-table} Example Table (Expandable)
:header-rows: 1
:class: expandable-table
:name: tab-example-expandable
* - Heading 1
  - Heading 2
* - A
  - B
```

It's usually only necessary to use this class if the table spills, generating a scroll bar. See {numref}`tab-final_island_shares` for a practical example.

### Linking to headings 

It's possible to add heading links, like the battery electricity example above. You need to first assign an ID to your target heading, then link to that ID in your text. 

First, label the heading you want to link to. It's possible to autogenerate slugs for different headings, but with the volume of text planned for this documentation, that might not be robust. It's also convenient to identify headings that have links elsewhere. We therefore add link IDs only when needed, like so: 

```
(heading-example-id)=
#### Example heading
```
This does nothing on its own - simply serves as an internal ID that ties to that heading. 

Then, you can use a standard `{ref}` approach to reference your ID, like:

```
{ref}`See this heading for more info<heading-example-id>`
```

This renders like so: 

{ref}`See this heading for more info<heading-example-id>`

(heading-example-id)=
#### Example heading

### Popup notes

You can make popup notes using `rst` like this: 

```
```{eval-rst}
.. note::
   This is a note
```

```{eval-rst}
.. note::
   This is a note
```

If you want to change the title, you need to extend the functionality using an admonition with a note class, like this: 

```
```{eval-rst}
.. admonition:: Custom note title
   :class: note

   This note has a custom title
```

```{eval-rst}
.. admonition:: Custom note title
   :class: note

   This note has a custom title
```

### Equations 

Equations from Word documents are very close to the required format for MyST Markdown. You can simply wrap inline equation text in `$`[^escape_dollar] signs, like: 

```
This is calculated via: $PI_i=(Expense_i)/(Expense_{2023})$
```
This is calculated via: $PI_i=(Expense_i)/(Expense_{2023})$[^subscript_note]

[^subscript_note]: If a subscript is more than one character, you should wrap it in `{}` to ensure correct rendering.
[^escape_dollar]: If your sentence contains multiple `$` signs naturally, you will need to escape some to stop the equation rendering, using `\$`. It's preferable to instead use `NZD` in any case.

It's also possible to make standalone equations with `{math}` blocks, like: 

```
```{math}
:label: eq-example

\sum_{i,r} (Capacity_{i,r} \cdot Availability_{{AW}_{i,r}})
    \ge (1 + \alpha) \cdot 
    \sum_{r} CapacityDemand_{{AW}_{r}}

```

```{math}
:label: eq-example

\sum_{i,r} (Capacity_{i,r} \cdot Availability_{{AW}_{i,r}})
    \ge (1 + \alpha) \cdot 
    \sum_{r} CapacityDemand_{{AW}_{r}}

```
Similar to tables, you can reference this `{math}` block with `{eq}`, which forms a link and lists the generated number: 

```
See Equation {eq}`eq-example` for more details.
```
See Equation {eq}`eq-example` for more details.

### Footnotes

Microsoft Word footnotes do not copy well into markdown. If you just copy a document's text, the footnote will appear only as an extra space. These need to be rewritten.

You can use the inline style `sometext[^a_footnote]`, which renders as "sometext[^a_footnote]". You must also provide the footnote details somewhere in order for this to render correctly. In this example, you would include `[^a_footnote]: text goes here` somewhere in your source file.

[^a_footnote]: text goes here

Some notes: 

- The footnote ID can be a number or text. It's probably good practise to give it a short and meaningful name, like any variable, to help manage these.
- The actual footnote details in your source documentation can be placed anywhere. It's best to put them close to the footnote source, to help keep things organised and make it easier to update/maintain these. 
- Footnote details at the bottom of the page are ordered based on where they appear in the text.
- If a footnote contains a URL, you should make this clickable by wrapping it in `<>`: `<https://www.google.com/>` renders as <https://www.google.com/>


## Document generation 

### Setup

Markdown documentation is the single source of truth. However, some users may want more traditional files, and so we use the same engine to generate Word or pdf documents. 

To achieve this, our `conf.py` is also setup with the sphinx extension `docxbuilder`, which can generate Word files using the same design as the site. `docxbuilder` handles almost entirely everything, with a few additional plugins for things like the mathjax interpreter. 

We include a few specific configuration options in `conf.py` in order to control these. First, we can select which `index.md` is used to build the word document in the `docx_document` list, and give the outputs a name and title:

```python
docx_documents = [
    # (startdocname, targetname, docproperties, toctree_only)
    ("model_methodology/electricity/index", 
    "Electricity supply assumptions.docx", 
    {"title": "Electricity supply assumptions"}, 
    True),    
]
```

We also include a Template as a source Word file, bundled in this repo. The Style settings in this Word document are inherited by all generated docs, using the `docx_style` setting. Adjusting the formatting of the outputs means adjusting the relevant styles in the template document. 

You can see more information on this setup at the sphinx builder documentation page [here](https://docxbuilder.readthedocs.io/en/latest/docxbuilder.html#usage).

### Building documents (and field updating)

The Sphinx engine can build Word documents from our documentation pages. This uses two key additional parameters:

1) Word Styles, which are stored in `source/_templates/EECATemplate.docx`. To change the look and feel of the output Word documents, change the inbuilt styles in this Word document. Note that this can be quite fiddly to modify, but once done it does not require any further changes. 

2) The document metadata, which is stored as a list called `docx_documents` in `source/conf.py`. Each new document is generated separately, and tied to an existing toctree file in the documentation. In this way we can generate multiple smaller documentation by selecting the relevant toctree's index file. This also contains additional metadata in the `docproperties` dict, which is used to populate the Word document's fields. See `conf.py` for examples of page setups. 

Note that we currently use a powershell script to automatically populate the document's fields, such as Table of Contents page numbers or Date and Title. It is not possible to do this in the input XML, as these are Word client side settings, intended to be manually updated by users. To avoid manually updating everything each time you generate Word documentation, we use a bash and powershell scripts 

```{eval-rst}
.. note::
   This process assumes you are working in WSL. If you are working in Windows, this process would be simpler as you can invoke powershell directly without moving files to the Windows system. TIMES-NZ developers work in Linux, so the Windows-native process is not documented here.
```
### Running the bash scripts

We use three scripts to fully automate the MSWord process: 

```
scripts/build-docx.sh
scripts/update-docx-fields.sh
scripts/update-fields.ps1
```

These build the Word documents to the Windows mount, open and update them in Word using Powershell, then bring them back to our build directory.

You will first need to make the bash scripts executable. You can do this with the following commands: 

```
chmod +x scripts/build-docx.sh
chmod +x scripts/update-docx-fields.sh
```

Then, simply run (again, from `docs/`): 

```
./scripts/build-docx.sh
```
Note that transfer between WSL and the Windows filesystem can be slow. Output files are stored in `docs/build/docx/`.

For an alternative, simpler process, you can simply run: `sphinx-build -b docx source build/docx`, which does not require any scripts. This creates the Word documents as above, but does not update the TOC, Date, Title, or other fields. 






