import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


from qa_functions import get_delta_data, check_category_mismatch
from config import qa_runs



def run_delta_app(attribute):

    # get data 
    df = get_delta_data(attribute)
    run_a = qa_runs[0]
    run_b = qa_runs[1]

    # find parameter list
    parameter_options = df["Parameters"].unique()

    # Define the drill-down hierarchy
    HIERARCHY = ['Fuel', 'Subsector', 'Technology', 'Process', 'Commodity', 'Region', 'TimeSlice']

    # Color mapping for scenarios
    color_map = {run_a: 'green', run_b: 'blue'}

    # Initialize the Dash app
    app = dash.Dash(
        __name__,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
        assets_folder='assets'  
    )

    # store data as app properties so available to callbacks in portable version       
    app.df = df  
    app.run_a = run_a
    app.run_b = run_b

    # Initialize the layout with a store component
    app.layout = html.Div([
        # Store for keeping track of the current view state
        dcc.Store(id='view-state', data={
            'level': 0,  # Index into HIERARCHY
            'selections': {}  # Will store {field: value} pairs as we drill down
        }),

        # Title and help button

        html.Div([
            html.H1('TIMES QA - Scenario differences', 
                   style={'textAlign': 'left', 'marginBottom': '20px', 'display': 'inline-block'}),
            html.Button(
                'Help ▼',
                id='help-button',
                style={
                    'float': 'right',
                    'backgroundColor': '#f0f0f0',
                    'border': '1px solid #ddd',
                    'borderRadius': '4px',
                    'padding': '8px 15px',
                    'cursor': 'pointer',
                    'marginTop': '10px'
                }
            ),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),

        # Help section (called by button in callback below)

        html.Div(
            [html.Div([
                    html.H3('How it works', style={'marginBottom': '15px'}),
                    html.Div([
                        html.P([
                            "This app is designed to show only the differences between two TIMES scenarios (and these scenarios are defined in  `config.py`). ",
                            html.Br(),
                            "It will display any data changes within groups defined by Attribute, Process, Commodity, Period, and Region. ",
                            "Put another way, it holds those variables constant between scenarios, and then displays which ones have had values change. ",
                            "Note that group definition variables are defined as `constant_variables` in `qa_functions.py`, and can be changed there if desired. ",
                            html.Br(),
                            html.Br(),
                            "The app displays aggregated data, and allows you to drill down to find further detail. ",
                            "Note that at this aggregated level, data might match. For example, LPG emissions might be the same in both scenarios across each Period. ",
                            "However, if some of this LPG use shifts to a different Region in one scenario, then it will show up here as a difference in regional LPG emissions between scenarios. ",
                            html.Br(),
                            html.Br(),
                            "The data is filtered for only those categories which show differences between the scenarios. ",
                            "It uses the raw .vd outputs and adds metadata from the main TIMES concordance table, ",
                            "which defines groupings like Technology or Sector.",
                            html.Br(),
                            "The .vd file is defined by the combination of Attribute, Process, and Commodity (the APC key). ",
                            "Within each instance of an APC key, data values can vary across Period, Region, Vintage, and TimeSlice.",
                            html.Br(),
                            html.Br(),
                            "This app only displays data which:"],
                            style={'marginBottom': '10px'}),
                        html.Ol([                            
                            html.Li('Has a matching APC key in both scenarios'),
                            html.Li('Within the matching APC key, has different data within a Period or Region')                          
                        ], style={'marginLeft': '20px', 'marginTop': '10px'}),   
                        html.P([
                            "Note that currently, TimeSlice is excluded from the delta checking. ",
                            "This means that if a category only differs by distribution across Timeslices, it will not be included. ",
                            "Again, this behaviour can be changed by adding TimeSlice to `constant_variables`. ",
                            html.Br(), 
                            html.Br()                            
                            ],
                            style={'marginBottom': '10px'}),        
                        html.H3('How to use', style={'marginBottom': '15px'}),
                        html.Ol([                            
                            html.Li('Select the initial parameter from the dropdown list.'),
                            html.Li('Click on any blue category title to drill down into more detailed views.'),
                            html.Li('Use the "Back" button to return to previous levels.'),
                            html.Li('The current filters are always displayed at the top of the page.'),
                            html.Li('Each chart shows a comparison between the two scenarios using grouped bars.')
                        ], style={'marginLeft': '20px', 'marginTop': '10px'}),                        
                    ])
                ], style={
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                })
            ],
            id='help-content',
            style={'display': 'none'}
        ),
        


        # Header and legend

        html.Div([
            html.H3(f"Differences in '{attribute}' between ", 
                   style={'display': 'inline'}),
            html.Span(run_a, style={'backgroundColor': color_map[run_a], 'color': 'white', 'padding': '5px 10px', 'borderRadius': '3px'}),
            html.H3(" and ", style={'display': 'inline'}),
            html.Span(run_b, style={'backgroundColor': color_map[run_b], 'color': 'white', 'padding': '5px 10px', 'borderRadius': '3px'}),


            html.Button(
                'Category Mismatches ▼',
                id='mismatch-button',
                style={
                    'float': 'right',
                    'backgroundColor': '#f0f0f0',
                    'border': '1px solid #ddd',
                    'borderRadius': '4px',
                    'padding': '8px 15px',
                    'cursor': 'pointer',
                    'marginTop': '10px'
                }
            ),
        ], style={'marginBottom': '20px'}),

        # Mismatch section 
        html.Div([
            html.H3(f"Category mismatches", style={'display': 'inline'}),        
            html.Br(),
            html.P(f"Within '{attribute}', these categories do not align between scenarios:"),                    
            # return the outputs   
            html.P("Process", style = {'font-weight': 'bold'}),
            html.P(f"{check_category_mismatch(attribute, "Process", run_a, run_b)}",
                   style = {'white-space' : 'pre-wrap'}
                   ),
            html.P("Commodity", style = {'font-weight': 'bold'}),
            html.P(f"{check_category_mismatch(attribute, "Commodity", run_a, run_b)}",
                   style = {'white-space' : 'pre-wrap'}
                   )],
        id = 'mismatch-content',
        style={'marginBottom': '20px'}),

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

            # Header area for list of current filters
            html.Div(id='current-filters', style={'marginBottom': '20px', 'padding': '10px', 'backgroundColor': '#f8f9fa'}),

            # Back button (initially hidden)
            html.Button(
                'Back',
                id='back-button',
                style={'display': 'none', 'marginLeft': '20px'},
            ),

            # Current view title
            html.H2(id='view-title', style={'textAlign': 'center', 'marginBottom': '20px'}),
        ], style={'marginBottom': '20px'}),

        # Main graph
        html.Div([
            dcc.Graph(id='faceted-chart', style={'height': '800px'}),
        ])
    ], style={'fontFamily': 'Calibri'})


    @app.callback(
        [Output('mismatch-content', 'style'),
         Output('mismatch-button', 'children')],
        [Input('mismatch-button', 'n_clicks')],
        [State('mismatch-content', 'style')]
    )

    def toggle_mismatch(n_clicks, current_style):
        if n_clicks is None:
            return {'display': 'none'}, 'Category Mismatches ▼'
        
        if current_style is None or current_style.get('display') == 'none':
            return {'display': 'block'}, 'Category Mismatches ▲'
        else:
            return {'display': 'none'}, 'Category Mismatches ▼'


    @app.callback(
        [Output('help-content', 'style'),
         Output('help-button', 'children')],
        [Input('help-button', 'n_clicks')],
        [State('help-content', 'style')]
    )

    def toggle_help(n_clicks, current_style):
        if n_clicks is None:
            return {'display': 'none'}, 'Help ▼'
        
        if current_style is None or current_style.get('display') == 'none':
            return {'display': 'block'}, 'Help ▲'
        else:
            return {'display': 'none'}, 'Help ▼'


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
            filter_display = []
            view_title = "Select " + HIERARCHY[current_state['level']]

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

            filter_display = []
            if new_level > 0:  # Only show filters after first level
                filter_display = [
                    html.P(
                        f"Parameter: {selected_parameter}", 
                        style={'fontWeight': 'bold', 'marginBottom': '5px'}
                        )]
                # Add each selected filter to the display
                for field in HIERARCHY[:new_level]:
                    if field in new_selections:
                        filter_display.append(
                            html.P(
                                f"{field}: {new_selections[field]}", 
                                style={'fontWeight': 'bold', 'marginBottom': '5px'}
                                ))

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
            view_title = "Select " + HIERARCHY[new_level]

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
        filtered_df = app.df[app.df['Parameters'] == selected_parameter]

        # Apply all accumulated filters
        for field, value in view_state['selections'].items():
            filtered_df = filtered_df[filtered_df[field] == value]

        # Get current faceting field
        facet_column = HIERARCHY[view_state['level']]

        # Aggregate data
        agg_df = filtered_df.groupby(['Period', facet_column, 'Scenario'])['PV'].sum().reset_index()
        # Convert Period to numeric, sort, and get unique sorted periods
        agg_df['Period'] = pd.to_numeric(agg_df['Period'])
        sorted_periods = sorted(agg_df['Period'].unique())
        # Convert periods back to string but maintain sorted order
        sorted_periods = [str(period) for period in sorted_periods]
        agg_df['Period'] = agg_df['Period'].astype(str)


        # get list of units
        # we don't want to mess with the grain of agg_df, so we'll just get everything from the filtered_df
        unique_units = filtered_df["Unit"].unique().tolist()
        units_str = f"{', '.join(unique_units)}"

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
        n_cols = min(5, max(1, n_facets))
        n_rows = max(1, (n_facets + n_cols - 1) // n_cols)

        # Create subplot figure
        fig = make_subplots(
            rows=n_rows, cols=n_cols
            #vertical_spacing=0.3,
            #horizontal_spacing=0.05
        )

        

        # Add traces for each facet value
        for idx, facet_value in enumerate(facet_values):
            row = idx // n_cols + 1
            col = idx % n_cols + 1

            facet_data = agg_df[agg_df[facet_column] == facet_value]

            # Add title annotation with different styling based on whether we can drill deeper
            can_drill_deeper = view_state['level'] < len(HIERARCHY) - 1
            if can_drill_deeper:
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
                        showlegend=False,
                    ),
                    row=row, col=col
                )
            
            # ensure correct xaxis order
            fig.update_xaxes(categoryorder='array',
                             categoryarray=sorted_periods,
                             row=row,
                             col=col)

              

        fig.update_layout(
            height=300 * n_rows,
            # title_text=title_text,
            barmode='group',
            showlegend=False,
            # legend=dict(
            #     orientation="h",
            #     yanchor="bottom",
            #     y=1.02,
            #     xanchor="right",
            #     x=1
            # )
        )

        
        # y axis unit titles
        fig.update_yaxes(title_text=f"{units_str}")

        return fig

    return app