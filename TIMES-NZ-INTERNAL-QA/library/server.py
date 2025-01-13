from flask import Flask
from dash import Dash
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from delta_app import run_delta_app  # your existing app

def create_flask_app(attribute):
    # Create Flask app
    server = Flask(__name__)
    
    # Basic Flask route for home page
    @server.route('/')
    def index():
        return """
        <h1>TIMES QA Dashboard</h1>
        <ul>
            <li><a href="/dash/">View Delta Analysis Dashboard</a></li>
        </ul>
        """
    
    # Create Dash app with a specific route
    dash_app = run_delta_app(attribute)  
    dash_app.server.name = 'dash_app'  
    
    # Create dispatcher to handle both Flask and Dash
    app = DispatcherMiddleware(
        server,  # Main Flask app
        {
            '/dash': dash_app.server  # Mount Dash app at /dash
        }
    )
    
    return app

if __name__ == '__main__':
    app = create_flask_app('Your Attribute')
    # Run the server
    run_simple('0.0.0.0', 8050, app, use_reloader=True, use_debugger=True)