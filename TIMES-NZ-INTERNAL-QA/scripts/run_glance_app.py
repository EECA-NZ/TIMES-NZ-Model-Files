# libraries 
import os 
import sys

# get custom libraries
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "library"))
from delta_app_glance import run_glance_app

# Main

def run_dashboard():
    app = run_glance_app()
    app.run_server(debug=True, port=8050) 
    
run_dashboard()

# open http://127.0.0.1:8050/