import csv
import json
import os 

def create_html_with_data(csv_file, output_file):
    # Read CSV and convert to JSON
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # Read the HTML template
    with open('template.html', 'r') as f:
        html_template = f.read()
    
    # Convert data to JSON string
    json_data = json.dumps(data)
    
    # Insert the data into the HTML template
    html_with_data = html_template.replace('const data = [];', f'const data = {json_data};')
    
    # Write the complete HTML file
    with open(output_file, 'w') as f:
        f.write(html_with_data)



if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    create_html_with_data('attribute_process_commodity_concordance.csv', 'times_concordance_lookup.html')

