def export_dash_app(app, output_path='delta_app.html'):
    """
    Export a Dash app to a static HTML file
    """
    # Define custom HTML template with CDN resources
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <title>TIMES QA - Scenario Differences</title>
            {%metas%}
            {%favicon%}
            {%css%}
            <!-- Add Dash and Plotly from CDN -->
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    # Run the server briefly to generate the HTML
    app.run_server(debug=False, port=8050)
    
    # Access the index page
    import requests
    html_content = requests.get('http://localhost:8050').text
    
    # Stop the server
    import os
    import signal
    os.kill(os.getpid(), signal.SIGINT)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Static HTML file generated at: {output_path}")
    return output_path