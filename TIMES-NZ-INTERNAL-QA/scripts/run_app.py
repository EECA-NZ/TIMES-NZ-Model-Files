# libraries 
import os 
import sys
from pathlib import Path
# get custom libraries
current_dir = Path(__file__).resolve().parent
sys.path.append(os.path.join(current_dir, "..", "library"))
from delta_app import run_delta_app
# from config import qa_runs
# from qa_functions import get_delta_data
# Main


# f = get_delta_data("VAR_FIn", qa_runs)


# print(df)



def run_dashboard():
    app = run_delta_app("VAR_FOut")
    # Open the browser after a 1-second delay to ensure the server is running
    # Timer(1, open_browser).start()  
    app.run_server(debug=True, port=8050) 
    
run_dashboard()

# open http://127.0.0.1:8050/





