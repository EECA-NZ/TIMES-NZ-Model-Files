"""
Orchestrates the app
"""

import sys
from pathlib import Path

from shiny import App

# this is currently required for shinyapps to read src since it doesnt use poetry
# will need to do some pylint disabling here
# there might be more robust options....
sys.path.append(str(Path(__file__).parent / "src"))
# pylint:disable = wrong-import-position
from times_nz_internal_qa.app.server import server
from times_nz_internal_qa.app.ui import app_ui

app = App(app_ui, server)


"""
# from TIMES-NZ-INTERNAL-QA:

refresh requirements.txt with: 
poetry export -f requirements.txt -o requirements.txt --without-hashes

deploy with: 
poetry run rsconnect deploy shiny . \
  --entrypoint app \
  --title times-nz-3-alpha
"""
