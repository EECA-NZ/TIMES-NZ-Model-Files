"""Simply runs the app locally"""

from shiny import run_app

if __name__ == "__main__":
    run_app("app", reload=True)
