# libraries 
import os 
import sys

# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from delta_app import run_delta_app

# Main

def run_dashboard():
    app = run_delta_app("VAR_FOut")
    app.run_server(debug=True, port=8050) 
    
run_dashboard()

# open http://127.0.0.1:8050/





