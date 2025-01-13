import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Define the drill-down hierarchy
HIERARCHY = ['Fuel', 'Subsector', 'Technology', 'TimeSlice']

# Initialize the Dash app
app = dash.Dash(__name__)

# Initialize the layout with a store component
app.layout = html.Div([
    # Store for keeping track of the current view state
    dcc.Store(id='view-state', data={
        'level': 0,  # Index into HIERARCHY
        'selections': {}  # Will store {field: value} pairs as we drill down
    }),
    
    html.H1('Energy System Analysis Dashboard', 
            style={'textAlign': 'center', 'marginBottom': '20px'}),
            
    # Header area for current filters
    html.Div(id='current-filters', style={'marginBottom': '20px', 'padding': '10px', 'backgroundColor': '#f8f9fa'}),
    
    # Current view title
    html.H2(id='view-title', style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Container for filters and navigation
    html.Div([
        # Parameter dropdown
        html.Div([
            html.Label('Select Parameter:'),
            dcc.Dropdown(
                id='parameter-dropdown',
                options=[{'label': param, 'value': param} for param in parameter_options],
                value=parameter_options[0]
            )
        ], id='param-dropdown-container', style={'width': '30%', 'display': 'inline-block'}),
        
        # Back button (initially hidden)
        html.Button(
            'Back',
            id='back-button',
            style={'display': 'none', 'marginLeft': '20px'},
        )
    ], style={'marginBottom': '20px'}),
    
    # Main graph
    html.Div([
        dcc.Graph(id='faceted-chart', style={'height': '800px'}),
    ])
])

# Callback to handle clicks and view state
@app.callback(
    [Output('view-state', 'data'),
     Output('back-button', 'style'),
     Output('param-dropdown-container', 'style'),
     Output('current-filters', 'children'),
     Output('view-title', 'children')],
    [Input('faceted-chart', 'clickAnnotationData'),
     Input('back-button', 'n_clicks')],
    [State('view-state', 'data'),
     State('parameter-dropdown', 'value')]
)
def update_view_state(annotation_click, back_clicks, current_state, selected_parameter):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Generate initial filter display
        filter_display = [html.P(f"Parameter: {selected_parameter}", style={'fontWeight': 'bold', 'marginBottom': '5px'})]
        view_title = HIERARCHY[current_state['level']] + 's'
    
        return current_state, {'display': 'none'}, {'width': '30%', 'display': 'inline-block'}, filter_display, view_title
    
    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger == 'back-button':
        # Go back one level
        new_level = max(0, current_state['level'] - 1)
        new_selections = dict(list(current_state['selections'].items())[:new_level])
        
        # Show dropdown only at top level
        dropdown_style = {'width': '30%', 'display': 'inline-block'} if new_level == 0 else {'display': 'none'}
        # Show back button except at top level
        button_style = {'display': 'none'} if new_level == 0 else {'display': 'inline-block', 'marginLeft': '20px'}
        
        # Generate filter display
        filter_display = [html.P(f"Parameter: {selected_parameter}", style={'fontWeight': 'bold', 'marginBottom': '5px'})]
        for field in HIERARCHY[:new_level]:
            if field in new_selections:
                filter_display.append(html.P(f"{field}: {new_selections[field]}", 
                                          style={'fontWeight': 'bold', 'marginBottom': '5px'}))
        
        # Generate view title
        view_title = 'Select ' + HIERARCHY[new_level] # could also pluralise but "technologies" is annoying
        
        return {
            'level': new_level,
            'selections': new_selections
        }, button_style, dropdown_style, filter_display, view_title
    
    if trigger == 'faceted-chart' and annotation_click:
        # Clean the selected value (remove arrows and whitespace)
        selected_value = annotation_click['annotation']['text'].replace('⯆', '').strip()
        
        # Get the current field we're looking at
        current_field = HIERARCHY[current_state['level']]
        
        # Update selections with the new value
        new_selections = dict(current_state['selections'])
        new_selections[current_field] = selected_value
        
        # Move to next level if not at end
        new_level = min(len(HIERARCHY) - 1, current_state['level'] + 1)
        
        # Generate filter display
        filter_display = [html.P(f"Parameter: {selected_parameter}", style={'fontWeight': 'bold', 'marginBottom': '5px'})]
        for field in HIERARCHY[:new_level + 1]:
            if field in new_selections:
                filter_display.append(html.P(f"{field}: {new_selections[field]}", 
                                          style={'fontWeight': 'bold', 'marginBottom': '5px'}))
        
        # Generate view title
        view_title = HIERARCHY[new_level] + 's'  # Pluralize
        
        return {
            'level': new_level,
            'selections': new_selections
        }, {'display': 'inline-block', 'marginLeft': '20px'}, {'display': 'none'}, filter_display, view_title
    
    return current_state, {'display': 'none'}, {'width': '30%', 'display': 'inline-block'}


# Callback to update the graph
@app.callback(
    Output('faceted-chart', 'figure'),
    [Input('parameter-dropdown', 'value'),
     Input('view-state', 'data')]
)
def update_graph(selected_parameter, view_state):
    # Start with parameter filter
    filtered_df = df[df['Parameters'] == selected_parameter]
    
    # Apply all accumulated filters
    for field, value in view_state['selections'].items():
        filtered_df = filtered_df[filtered_df[field] == value]
    
    # Get current faceting field
    facet_column = HIERARCHY[view_state['level']]
    
    # Aggregate data
    agg_df = filtered_df.groupby(['Period', facet_column, 'Scenario'])['PV'].sum().reset_index()
    
    # Get available facet values
    facet_values = sorted(agg_df[facet_column].unique())
    
    # Handle empty dataset case
    if len(facet_values) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text='No data available for the selected filters',
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14)
        )
        return fig

    # Calculate number of rows and columns for subplots
    n_facets = len(facet_values)
    n_cols = min(6, max(1, n_facets))
    n_rows = max(1, (n_facets + n_cols - 1) // n_cols)
    
    # Create subplot figure
    fig = make_subplots(
        rows=n_rows, cols=n_cols
        #vertical_spacing=0.3,
        #horizontal_spacing=0.05
    )
    
    # Color mapping for scenarios
    color_map = {run_a: 'red', run_b: 'blue'}
    
    # Add traces for each facet value
    for idx, facet_value in enumerate(facet_values):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        
        facet_data = agg_df[agg_df[facet_column] == facet_value]
        
        # Add title annotation with different styling based on whether we can drill deeper
        can_drill_deeper = view_state['level'] < len(HIERARCHY) - 1
        if can_drill_deeper:
            fig.add_annotation(
                text='⯆ ' + facet_value + ' ⯆',
                xref="x domain",
                yref="y domain",
                x=0.5,
                y=1.1,
                showarrow=False,
                xanchor="center",
                yanchor="bottom",
                row=row,
                col=col,
                font=dict(size=12, color='#0066cc'),
                bgcolor='rgba(240, 248, 255, 0.8)',
                bordercolor='#0066cc',
                borderwidth=1,
                borderpad=4,
                hovertext='Click to drill down',
            )
        else:
            fig.add_annotation(
                text=facet_value,
                xref="x domain",
                yref="y domain",
                x=0.5,
                y=1.1,
                showarrow=False,
                xanchor="center",
                yanchor="bottom",
                row=row,
                col=col,
                font=dict(size=12)
            )
        
        for scenario in [run_a, run_b]:
            scenario_data = facet_data[facet_data['Scenario'] == scenario]
            
            fig.add_trace(
                go.Bar(
                    x=scenario_data['Period'],
                    y=scenario_data['PV'],
                    name=scenario,
                    marker_color=color_map[scenario],
                    showlegend=True if idx == 0 else False,
                ),
                row=row, col=col
            )
    
    # Simple title for the graph
    title_text = f"{facet_column} Comparison"
    
    fig.update_layout(
        height=300 * n_rows,
        title_text=title_text,
        barmode='group',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Period")
    fig.update_yaxes(title_text="Value")
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)