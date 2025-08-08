## VSCode and Poetry

Poetry creates a virtual environment that may not be in your project directory, so VSCode might not pick it up automatically. We need to set the VSCode interpreter to align with Poetry. 

Currently, only the `PREPARE-TIMES-NZ` module includes a Poetry setup with `pyproject.toml`. 

#### Step 1

Run the following in your terminal to find the virtual environment path: `poetry env info --path`

This will give you something like `/home/YourName/.cache/pypoetry/virtualenvs/prepare-times-nz-abc123`

#### Step 2

1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)
1. Search for and select: Python: Select Interpreter
1. Click Enter interpreter path
1. Paste the path from step 1 and append /bin/python (or Scripts/python.exe on Windows), e.g.:

    `/home/YourName/.cache/pypoetry/virtualenvs/prepare-times-nz-abc123/bin/python`