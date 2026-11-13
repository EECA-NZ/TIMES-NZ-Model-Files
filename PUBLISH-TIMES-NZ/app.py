"""
Orchestrates the app
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from shiny import App

# Shinyapps.io does not install the workspace package, so expose ``src`` here.
# will need to do some pylint disabling here
# there might be more robust options....
sys.path.append(str(Path(__file__).parent / "src"))
load_dotenv(Path(__file__).parent / ".env")
# pylint:disable = wrong-import-position
from publish_times_nz.app.server import server
from publish_times_nz.app.ui import app_ui

app = App(
    app_ui,
    server,
    static_assets={
        "/assets": Path(__file__).parent / "assets",
        "/": Path(__file__).parent / "www",
    },
)
