
# This script: 

# 1) Runs the sphinx build command for docx based on the settings in conf.py


# That's it. It does not send these to window or update any fields. This is a dev option. 


# Set each location
WSL_OUT="build/docx"
sphinx-build -b docx source "$WSL_OUT"

