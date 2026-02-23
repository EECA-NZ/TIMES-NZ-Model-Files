
# This script: 

# 1) Runs the sphinx build command for docx based on the settings in conf.py
# Note: this does almost all the work. Unfortunately we also need to update the document fields (TOC page numbers, build dates, etc)
# 2) opens the word docs in Windows and updates fields
# 3) saves these back to the build directory in your repo. 
# Then we pull them back into build/docx 



# Set each location
WSL_OUT="build/docx"
WIN_OUT="/mnt/c/tmp/sphinx-docx"


# run the full build, saving into the windows mount
sphinx-build -b docx source "$WIN_OUT"

# update windows document fields 
./scripts/update-docx-fields.sh "$WIN_OUT"

# copy files into WSL location 

rsync -a "$WIN_OUT"/ "$WSL_OUT"/

# run 

# chmod +x scripts/build-docx.sh
# ./scripts/build-docx.sh