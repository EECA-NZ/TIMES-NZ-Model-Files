
# Environment setup with uv 




From the repository root, install the shared workspace environment:

```bash
uv sync --all-groups 
```

This creates one `.venv` at the repository root for both Python modules. Run
commands with `uv run`; no environment activation is required. 

It's optional and sometimes convenient to activate the environment in your shell, meaning `uv run` prefixes are not required to run commands. You can do this with: 

```
source .venv/bin/activate
```

### uv and VSCode

uv creates the shared environment at the repository root. Configure VSCode to
use that interpreter if it is not detected automatically:

1. From the repository root, use `.venv/bin/python` (or `.venv\\Scripts\\python.exe` on Windows).
1. Press Ctrl+Shift+P (or Cmd+Shift+P on Mac)
1. Search for and select: Python: Select Interpreter
1. Click Enter interpreter path
1. Select that interpreter path.