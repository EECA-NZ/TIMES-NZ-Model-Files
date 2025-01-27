import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import dash_draggable


from qa_functions import get_delta_data, check_category_mismatch, check_scenario_differences, check_missing_concordance_entries
from qa_data_retrieval import get_veda_data
from config import qa_runs


# Decide whether to even bother running the app - needs some differences 


def run_delta_app(attribute):

    run_a = qa_runs[0]
    run_b = qa_runs[1]

    # Check if data matches 
    original_df = get_veda_data(attribute)
    has_differences = check_scenario_differences(original_df, run_a, run_b)


    if has_differences:
        app = run_delta_app_with_differences(attribute)
    else: 
        app = run_delta_app_no_differences(attribute)
    
    return app





# If no differences, we don't do anything and instead just run this lightweight version 
def run_delta_app_no_differences(attribute): 

    run_a = qa_runs[0]
    run_b = qa_runs[1]
    app = dash.Dash(__name__)


    app.layout = html.Div([
            html.H1('TIMES QA - Scenario differences',
                   style={'textAlign': 'left', 'marginBottom': '20px'}),
            html.Div([
                html.H2('No differences found',
                       style={'textAlign': 'center', 'color': '#666'}),
                html.P(
                    f"The scenarios '{run_a}' and '{run_b}' are identical for the attribute '{attribute}'.",
                    style={'textAlign': 'center', 'fontSize': '16px', 'marginTop': '20px'}
                ),
                html.P(
                    "Please select a different attribute or scenario combination to compare.",
                    style={'textAlign': 'center', 'fontSize': '16px', 'marginTop': '10px'}
                )
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '40px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginTop': '50px'
            })
        ], style={'fontFamily': 'Calibri'})
    
    return app


# This is the main app which shows more detailed stuff 


# App if differences exist 
def run_delta_app_with_differences(attribute):    

    # Setup    
    run_a = qa_runs[0]
    run_b = qa_runs[1]
    df = get_delta_data(attribute)
    # we'll just take the concordance mismatches for this attribute, which we make a size-1 list so it all works.
    # Means we can also remove the attribute column since it is no longer needed.
    df_no_concordance = check_missing_concordance_entries(qa_runs, [attribute]).drop("Attribute", axis = 1)
    # find parameter list
    parameter_options = df["Parameters"].unique()

    # Define the drill-down hierarchy
    HIERARCHY = ['Fuel', 'Subsector', 'Technology', 'Process', 'Commodity', 'Region', 'TimeSlice']

    # Color mapping for scenarios
    color_map = {run_a: 'green', run_b: 'blue'}

    # Initialize the Dash app
    app = dash.Dash(__name__, suppress_callback_exceptions=True)

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
                            html.Br()                            
                            ],
                            style={'marginBottom': '10px'}),   
                        # How to use 
                        html.H3('How to use', style={'marginBottom': '15px'}),
                        html.Ol([                            
                            html.Li('Select the initial parameter from the dropdown list.'),
                            html.Li('Re-arrange the categories as desired by clicking and dragging these from left to right. This will change the order that the app drills down.'),
                            html.Li('Click on any blue category title to drill down into more detailed views.'),
                            html.Li('Use the "Back" button to return to previous levels.'),
                            html.Li('The current filters will be displayed at the top of the page.'),
                            
                        ], style={'marginLeft': '20px', 'marginTop': '10px'}),   
                        # Mismatching categories           
                        html.H3('Mismatching categories', style={'marginBottom': '15px'}),
                        html.P([
                            "While the app only considers categories with differences between the two scenarios, ",
                            "there may be some categories that cannot be compared because they only exist in one scenario or the other. "
                            "These are listed in the 'Category Mismatches' section, which can be accessed in the button to the lower right of this help section.",
                            html.Br()                            
                            ],
                            style={'marginBottom': '10px'}),           
                        # Matching data 
                        html.H3('Matching data', style={'marginBottom': '15px'}),
                        html.P([
                            "If the data for these scenarios matches perfectly, then the app will not load and instead take you to a different page.",                            
                            html.Br()                            
                            ],
                            style={'marginBottom': '10px'}),  
                        # Known issues
                        html.H3('Known issues', style={'marginBottom': '15px'}),
                        html.P([
                            "Sometimes the buttons to click down further don't work. A refresh usually fixes this. Alternatively, you can select a different category, drilling down the wrong way, then clicking 'Back' and trying your original category again.",
                            html.Br()                            
                            ],
                            style={'marginBottom': '10px'}),          
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
                   ),
            html.Div([
                html.H3(f"Missing concordances", style={'display': 'inline'}), 
                html.P(f"These categories exist in the data for '{attribute}', but not in the concordance file!"),
                dash_table.DataTable(
                    id='data-table',
                    columns=[
                        {"name": i, "id": i} for i in df_no_concordance.columns
                    ],
                    data=df_no_concordance.to_dict('records'),
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '2px',
                        'font-family': 'Calibri'
                    },
                    style_header={
                        'backgroundColor': 'rgb(240, 240, 240)',
                        'fontWeight': 'bold',
                        'border': '1px solid black'
                    },
                    style_data={
                        'border': '1px solid grey'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    page_size=10,  # Number of rows per page
                    filter_action="native",  # Enables filtering
                    sort_action="native",   # Enables sorting
                    sort_mode="multi",     # Enable multi-column sorting
                )
            ], style={'marginTop': '30px'}),
        ], 
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
            # Hierarchy Manager
            html.Div([
                html.P("Arrange drill-down categories:", style={"margin-bottom": "0px"}),   
                dash_draggable.GridLayout(
                    id='hierarchy-grid',
                    children=[
                        html.Div(
                            name,
                            style={
                                'padding': '0px',
                                'margin': '0px',                              
                                'backgroundColor': '#f0f0f0',
                                'border': '1px solid #ddd',
                                'borderRadius': '4px',
                                'text-align': 'centre',
                                'cursor': 'move',
                                'userSelect': 'none'
                            },
                            id=f'hierarchy-item-{name}',
                            key=name,
                            className="draggable-container"                         
                        )
                        for name in HIERARCHY
                    ],
                    layout=[
                        {'i': f'hierarchy-item-{name}', 'x': i, 'y': 0, 'w': 1, 'h': 1}
                        for i, name in enumerate(HIERARCHY)
                    ],
                    gridCols=7,
                    height=45,
                    width=900,
                    preventCollision=False,
                    isDraggable=True,                    
                    isDroppable=True,
                    compactType="horizontal",
                    isResizable=False,
                    nrows=1
                )               
            ]),

            # Back button (initially hidden)
            html.Button(
                'Back',
                id='back-button',
                style={'display': 'none', 'marginLeft': '20px'},
            ),

            # Current view title
            html.H2(id='view-title', style={'textAlign': 'center', 'marginBottom': '20px'}),
        ], style={'marginBottom': '20px'}),
                # Hierarchy manager 
        
        

        # Main graph
        html.Div([
            dcc.Graph(
                id='faceted-chart',
                style={'height': 'auto', 'min-height': '500px'},
                config={'scrollZoom': False}
            ),
        ], style={
            'overflow-y': 'auto',
            'overflow-x': 'hidden',
        })
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
     Input('back-button', 'n_clicks'),
     Input('hierarchy-grid', 'layout'),
     Input('parameter-dropdown', 'value')],
    [State('view-state', 'data')]
)
    def update_view_state(annotation_click, back_clicks, hierarchy_layout, selected_parameter,current_state):
        """
        Main callback for handling view state updates and hierarchy management.
        Returns exactly 5 outputs for all code paths.
        """
        ctx = dash.callback_context
        
        # Initialize default values for all outputs
        view_state = current_state
        back_button_style = {'display': 'none'}
        dropdown_style = {'width': '30%', 'display': 'inline-block'}
        filter_display = []
        view_title = f"Select {HIERARCHY[current_state['level']]}"
    
        # Handle initial load
        if not ctx.triggered:
            return (
                view_state,
                back_button_style,
                dropdown_style,
                filter_display,
                view_title
            )
    
        # Determine which input triggered the callback
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]

        # Hierarchy updates     
        if trigger == 'hierarchy-grid' and hierarchy_layout:
            try:
                # Extract the hierarchy names from the layout data
                sorted_items = sorted(hierarchy_layout, key=lambda x: (x['y'], x['x']))
                new_hierarchy = []
                for item in sorted_items:
                    name = item['i']
                    if name.startswith('hierarchy-item-'):
                        name = name.replace('hierarchy-item-', '')
                    new_hierarchy.append(name)

                if new_hierarchy:  # Only update if we got valid data
                    HIERARCHY[:] = new_hierarchy

                # Reset view state when hierarchy changes
                view_state = {
                    'level': 0,
                    'selections': {}
                }
                return (
                    view_state,
                    {'display': 'none'},
                    {'width': '30%', 'display': 'inline-block'},
                    [],
                    f"Select {HIERARCHY[0]}"
                )
            except Exception as e:
                print(f"Error updating hierarchy: {e}")
    
        # Handle back button clicks
        elif trigger == 'back-button':
            # Calculate new level and selections
            new_level = max(0, current_state['level'] - 1)
            new_selections = dict(list(current_state['selections'].items())[:new_level])
    
            # Update view state
            view_state = {
                'level': new_level,
                'selections': new_selections
            }
    
            # Update styles based on level
            back_button_style = {'display': 'none'} if new_level == 0 else {'display': 'inline-block', 'marginLeft': '20px'}
            dropdown_style = {'width': '30%', 'display': 'inline-block'} if new_level == 0 else {'display': 'none'}
            
            # Build filter display
            filter_display = []
            if new_level > 0:
                filter_display = [
                    html.P(
                        f"Parameter: {selected_parameter}", 
                        style={'fontWeight': 'bold', 'marginBottom': '5px'}
                    )
                ]
                for field in HIERARCHY[:new_level]:
                    if field in new_selections:
                        filter_display.append(
                            html.P(
                                f"{field}: {new_selections[field]}", 
                                style={'fontWeight': 'bold', 'marginBottom': '5px'}
                            )
                        )
    
            # Update title
            view_title = f"Select {HIERARCHY[new_level]}"
    
            return (
                view_state,
                back_button_style,
                dropdown_style,
                filter_display,
                view_title
            )
    
        # Handle chart annotation clicks
        elif trigger == 'faceted-chart' and annotation_click:
            # Get selected value from chart click
            selected_value = annotation_click['annotation']['text'].replace('⯆', '').strip()
            current_field = HIERARCHY[current_state['level']]
    
            # Update selections with new value
            new_selections = dict(current_state['selections'])
            new_selections[current_field] = selected_value
    
            # Calculate new level
            new_level = min(len(HIERARCHY) - 1, current_state['level'] + 1)
    
            # Update view state
            view_state = {
                'level': new_level,
                'selections': new_selections
            }
    
            # Update styles
            back_button_style = {'display': 'inline-block', 'marginLeft': '20px'}
            dropdown_style = {'display': 'none'}
    
            # Build filter display
            filter_display = [
                html.P(
                    f"Parameter: {selected_parameter}", 
                    style={'fontWeight': 'bold', 'marginBottom': '5px'}
                )
            ]
            for field in HIERARCHY[:new_level + 1]:
                if field in new_selections:
                    filter_display.append(
                        html.P(
                            f"{field}: {new_selections[field]}", 
                            style={'fontWeight': 'bold', 'marginBottom': '5px'}
                        )
                    )
    
            # Update title
            view_title = f"Select {HIERARCHY[new_level]}"
    
            return (
                view_state,
                back_button_style,
                dropdown_style,
                filter_display,
                view_title
            )
    
        # Default return - ensure all 5 outputs are returned
        return (
            view_state,
            back_button_style,
            dropdown_style,
            filter_display,
            view_title
        )


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

        # Define standard sizes
        SUBPLOT_HEIGHT = 200  # Fixed height for each subplot
        SPACING_BETWEEN_PLOTS = 100  # Fixed pixel spacing between plots
        MARGIN_TOP = 50  # Top margin for the figure
        MARGIN_BOTTOM = 50  # Bottom margin for the figure         

        # Calculate total figure height based on number of rows
        total_height = (SUBPLOT_HEIGHT * n_rows) + (SPACING_BETWEEN_PLOTS * (n_rows - 1)) + MARGIN_TOP + MARGIN_BOTTOM        

        # Calculate vertical spacing as a proportion of total height
        # The formula is: spacing = spacing_pixels / (total_height - margins)
        vertical_spacing = SPACING_BETWEEN_PLOTS / (total_height - MARGIN_TOP - MARGIN_BOTTOM)

        # Create subplot figure
        fig = make_subplots(
            rows=n_rows, cols=n_cols,
            vertical_spacing=vertical_spacing,
            # horizontal_spacing = 0.1,
            subplot_titles=[''] * (n_rows * n_cols),
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

              
        chart_height = max(500, 400 * n_rows)  # Minimum height of 500px
        fig.update_layout(
            height=total_height,
            # title_text=title_text,
            barmode='group',
            margin=dict(t=MARGIN_TOP, b=MARGIN_BOTTOM, l=50, r=50),
            showlegend=False,
            autosize = True,
            # legend=dict(
            #     orientation="h",
            #     yanchor="bottom",
            #     y=1.02,
            #     xanchor="right",
            #     x=1
            # )
        )

        
        # y axis unit titles
        fig.update_yaxes(title_text=f"{units_str}",
                         title_standoff=0)

        return fig

    return app