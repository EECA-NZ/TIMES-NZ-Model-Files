import csv
import json
import os 


# File paths 
# it is expected that the relevant input files are in the same directory as this script 
CONCORDANCE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# inputs 
concordance_file = f"{CONCORDANCE_DIRECTORY}/attribute_process_commodity_concordance.csv"
template_file = f"{CONCORDANCE_DIRECTORY}/template.html"
# output
output_file = f"{CONCORDANCE_DIRECTORY}/times_concordance_lookup.html"

# Functions 

def check_file_exists(filename, filepath): 
    """
    File name parameter just for verbose outputs
    """
    if not os.path.exists(filepath):
        print(f"Warning: cannot find '{filename}' at {filepath}. Please review!")   

def create_html_with_data(concordance_file, template_file, output_file):
    # Read CSV and convert to JSON
    with open(concordance_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # Read the HTML template
    with open(template_file, 'r') as f:
        html_template = f.read()
    
    # Convert data to JSON string
    json_data = json.dumps(data)
    
    # Insert the data into the HTML template
    html_with_data = html_template.replace('const data = [];', f'const data = {json_data};')
    
    # Write the complete HTML file
    with open(output_file, 'w') as f:
        f.write(html_with_data)


# Main

if __name__ == "__main__":    
    check_file_exists("concordance data", concordance_file)
    check_file_exists("HTML template", template_file)   

    create_html_with_data(concordance_file, template_file, output_file)    

