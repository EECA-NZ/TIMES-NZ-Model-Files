# basics
import pandas as pd 
# app functionality
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State, ClientsideFunction

# charts
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# custom
from qa_functions import check_missing_concordance_entries, check_scenario_differences
from qa_data_retrieval import get_all_veda_attributes, complete_periods, get_veda_data_no_concordance
from config import qa_runs



"""

This app shows a high level comparison of various components of the TIMES outputs 
It's designed to be really easy to add new comparison charts, just be specifying new input data and drilldown hierarchy. See `chart_configs`.

This assumes the concordance file has been filled out fully and correctly. It includes a check to ensure that this has happened, 
or provides a list of missing details that will need to be added if not. 

Things still to add: 

A contents view 

Electricity generation output
Electricity generation capacity 

Energy Service Demand (needs different handling for each sector)

The objective functions up top 


Technical things to tweak: 

Grey out bars where the data matches
If the data matches perfectly, add a flag up top? 
Add Unit to the y axis 








"""

# Parameters
run_a = qa_runs[0]
run_b = qa_runs[1]
# Data
df = get_all_veda_attributes(qa_runs)
df_no_concordance = check_missing_concordance_entries(qa_runs)
differences_exist = check_scenario_differences(df, run_a, run_b)
df_objective_function = get_veda_data_no_concordance("ObjZ")[["Scenario", "PV"]]


# Period list
period_list = sorted(pd.to_numeric(df['Period'].unique()))
period_list = [str(period) for period in period_list]
# Color mapping for scenarios
color_map = {run_a: 'green', run_b: 'blue'}


# Specific Table Data
#Emissions 
emissions_df = df[df['Parameters'] == "Emissions"]
# Energy Consumption (fuel consumption minus electricity)
fuel_df = df[df['Parameters'] == "Fuel Consumption"]
fuel_df = fuel_df[fuel_df["Enduse"] != 'Electricity Production']
# Electricity generation 
ele_gen_df = df[df["Sector"] == "Electricity"]
ele_gen_df = ele_gen_df[ele_gen_df["Parameters"].isin(['Electricity Generation'])]
ele_gen_df["PV"] = ele_gen_df["PV"] * 277.777778
ele_gen_df["Unit"] = "GWh"
# Electricity consumption 

ele_use_df = df[df["Fuel"] == "Electricity"]
ele_use_df = ele_use_df[ele_use_df ["Parameters"] == "Fuel Consumption"]
ele_use_df["PV"] = ele_use_df["PV"] * 277.777778
ele_use_df["Unit"] = "GWh"


# Electricity Generation Capacity 

ele_gen_processes = df[df["Parameters"] == 'Electricity Generation']["Process"].unique()
ele_cap_df = df[df["Process"].isin(ele_gen_processes)]
ele_cap_df = ele_cap_df[ele_cap_df["Parameters"] == "Technology Capacity"]




chart_configs = {
        'emissions': {
            'title_prefix': 'Emissions',
            'hierarchy': ['Sector', 'Fuel'],
            'df': emissions_df  
        },
        'fuel': {
            'title_prefix': 'Energy Consumption',
            'hierarchy': ['Fuel', 'Sector'],
            'df': fuel_df  
        },
        'ele_gen': {
            'title_prefix': 'Electricity Generation',
            'hierarchy': ['Fuel', 'Technology'],
            'df': ele_gen_df  
        },
        'ele_use': {
            'title_prefix': 'Electricity Consumption',
            'hierarchy': ['Sector', 'Technology'],
            'df': ele_use_df  
        },
        'ele_cap': {
            'title_prefix': 'Electricity Capacity',
            'hierarchy': ['Fuel', 'Technology'],
            'df': ele_cap_df  
        },

    }

# App building: 

def create_chart_containers(chart_configs):
    containers = []
    for chart_id, config in chart_configs.items():
        containers.append(html.Div([
            html.Div(id=chart_id, style={'position': 'relative', 'top': '-100px', 'visibility': 'hidden'}),  # Scroll anchor
            html.H2(id=f'view-title-{chart_id}'),
            html.Button(
                'Back',
                id=f'back-button-{chart_id}',
                style={'display': 'none', 'marginBottom': '10px'}
            ),               
            html.Div([
                dcc.Graph(
                    id=f'{chart_id}-chart',
                    style={'height': '100%', 'width': '100%'}
                ),
            ], style={
                'overflowY': 'auto',
                'overflowX': 'hidden',
                'paddingRight': '20px'
            })
        ], style={'marginBottom': '40px'}))
    return containers

def create_stores(chart_configs):
    return [
        dcc.Store(
            id=f'view-state-{chart_id}',
            data={'level': 'total', 'selections': {}}
        )
        for chart_id in chart_configs
    ]

# Chart creation functions 

def create_total_chart(df, run_a, run_b, color_map, name=None):

    unique_units = df["Unit"].unique().tolist()
    units_str = f"{', '.join(unique_units)}"

    # Aggregate emissions data with debugging
    agg_df = df.groupby(['Period', 'Scenario'])['PV'].sum().reset_index()    
    # Convert and sort periods
    agg_df['Period'] = pd.to_numeric(agg_df['Period'])
    agg_df = agg_df.sort_values('Period')
    agg_df['Period'] = agg_df['Period'].astype(str)    

    # Create figure
    fig = go.Figure()
    for scenario in [run_a, run_b]:
        scenario_data = agg_df[agg_df['Scenario'] == scenario]
        fig.add_trace(
            go.Bar(
                x=scenario_data['Period'],
                y=scenario_data['PV'],
                name=scenario,
                marker_color=color_map[scenario],
                showlegend=False
            )
        )

    # Add a clickable annotation with the same styling as in delta_app
    fig.add_annotation(
        text=f'Total {name} ⯆',
        x=0.5,
        y=1.1,
        xref='paper',
        yref='paper',
        showarrow=False,
        font=dict(size=12, color='#0066cc'),
        bgcolor='rgba(240, 248, 255, 0.8)',
        bordercolor='#0066cc',
        borderwidth=1,
        borderpad=4,
        xanchor='center',
        yanchor='bottom',
        hovertext='Click to drill down'
    )

    fig.update_layout(
        xaxis_title='Year',
        yaxis_title=units_str,
        height=500,
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
    
    return fig

def create_faceted_chart(agg_df, facet_column, run_a, run_b,
                         color_map, period_list,
                         can_drill=True, n_cols=4, units_str=None):
    
    """Creates a faceted chart showing multiple sub-charts based on facet values.
    
    Args:
        agg_df (pd.DataFrame): Aggregated dataframe with Period, facet_column, Scenario and PV
        facet_column (str): Column name to facet by
        run_a (str): Name of first scenario
        run_b (str): Name of second scenario
        color_map (dict): Mapping of scenarios to colors
        period_list (list): List of periods in order
        can_drill (bool): Whether this level can drill deeper
        n_cols (int): Maximum number of columns in the grid
        units_str (str): Units for y-axis label
    
    Returns:
        go.Figure: Plotly figure with faceted charts
    """
    # Get facet values
    facet_values = sorted(agg_df[facet_column].unique())
    
    # Calculate layout
    n_facets = len(facet_values)
    n_cols = min(n_cols, max(1, n_facets))
    n_rows = max(1, (n_facets + n_cols - 1) // n_cols)

    # Calculate heights and spacing
    subplot_height = 400
    spacing = 150
    total_height = (subplot_height * n_rows) + (spacing * (n_rows - 1))

    # Create subplots
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[''] * (n_rows * n_cols),
        vertical_spacing=spacing/total_height
    )

    # Add traces for each facet value
    for idx, facet_value in enumerate(facet_values):
        row = idx // n_cols + 1
        col = idx % n_cols + 1

        facet_data = agg_df[agg_df[facet_column] == facet_value]

        # Add clickable title
        title_text = f"{facet_value} ⯆" if can_drill else facet_value
        
        fig.add_annotation(
            text=title_text,
            xref=f"x{idx + 1 if idx > 0 else ''} domain",
            yref=f"y{idx + 1 if idx > 0 else ''} domain",
            x=0.5,
            y=1.1,
            showarrow=False,
            font=dict(
                size=12,
                color='#0066cc' if can_drill else 'black'
            ),
            bgcolor='rgba(240, 248, 255, 0.8)' if can_drill else None,
            bordercolor='#0066cc' if can_drill else None,
            borderwidth=1 if can_drill else 0,
            borderpad=4 if can_drill else 0,
            xanchor='center',
            yanchor='bottom',
            hovertext='Click to drill down' if can_drill else None,
            row=row,
            col=col
        )

        for scenario in [run_a, run_b]:
            scenario_data = facet_data[facet_data['Scenario'] == scenario]
            
            fig.add_trace(
                go.Bar(
                    x=scenario_data['Period'],
                    y=scenario_data['PV'],
                    name=scenario,
                    marker_color=color_map[scenario],
                    showlegend=False
                ),
                row=row,
                col=col
            )

        # Ensure correct x-axis order
        fig.update_xaxes(
            categoryorder='array',
            categoryarray=period_list,
            row=row,
            col=col
        )

        if units_str:
            fig.update_yaxes(
                title_text=units_str,
                row=row,
                col=col
            )

    # Update layout
    fig.update_layout(
        height=400 * n_rows,
        showlegend=False,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig



# Interaction helpers 

def handle_back_button(current_state, title_prefix):
    """Handle back button clicks"""
    # If we're at level 0, go back to total view
    if current_state['level'] == 0:
        return {'level': 'total', 'selections': {}}
    
    # Otherwise go back one level
    new_level = max(0, current_state['level'] - 1)
    new_selections = dict(list(current_state['selections'].items())[:new_level])

    return {
        'level': new_level,
        'selections': new_selections
    }

def handle_chart_click(click_data, current_state, title_prefix, hierarchy):
    """Handle chart annotation clicks"""
    selected_value = click_data['annotation']['text'].replace('⯆', '').strip()
    
    # If we're at total level, move to first hierarchy level
    if current_state['level'] == 'total':
        return {'level': 0, 'selections': {}}
    
    # Otherwise drill down one level
    current_field = hierarchy[current_state['level']]
    new_selections = dict(current_state['selections'])
    new_selections[current_field] = selected_value

    new_level = min(len(hierarchy) - 1, current_state['level'] + 1)

    return {
        'level': new_level,
        'selections': new_selections
    }

def get_button_style(state):
    """Get button display style based on state"""
    if state['level'] == 'total':
        return {'display': 'none', 'marginBottom': '10px'}
    return {'display': 'inline-block', 'marginBottom': '10px'}

def get_title(state, prefix, hierarchy):    
    """Get title based on state and prefix"""
    if state['level'] == 'total':
        return f"Total {prefix}"
    elif state['level'] == 1:
        selected_sector = state['selections'].get(hierarchy[0], '')
        return f"{selected_sector} {prefix} by {hierarchy[state['level']]}"
    else:
        return f"{prefix} by {hierarchy[state['level']]}"

def process_chart_interaction(trigger, click_data, back_clicks, current_state, title_prefix, hierarchy):
    """Helper function to process chart interactions"""
    if 'back-button' in trigger:
        return handle_back_button(current_state, title_prefix)
    elif 'chart' in trigger and click_data:
        return handle_chart_click(click_data, current_state, title_prefix, hierarchy)
    return current_state

# Callbacks

def create_view_callbacks(app, chart_id, title_prefix, hierarchy, df):
    @app.callback(
        [Output(f'view-state-{chart_id}', 'data'),
         Output(f'back-button-{chart_id}', 'style'),
         Output(f'view-title-{chart_id}', 'children')],
        [Input(f'{chart_id}-chart', 'clickAnnotationData'),
         Input(f'back-button-{chart_id}', 'n_clicks')],
        [State(f'view-state-{chart_id}', 'data')]
    )
    def update_view_state(click_data, back_clicks, current_state):
        # Initialize context and defaults
        ctx = dash.callback_context
        if not ctx.triggered:
            return (
                current_state,
                {'display': 'none', 'marginBottom': '10px'},
                f"Total {title_prefix}"
            )

        # Identify which input triggered the callback
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Initialize new state as copy of current
        new_state = current_state.copy()
        
        # Handle back button click
        if 'back-button' in trigger and back_clicks:
            if current_state['level'] == 0:
                # If at first level, go back to total view
                new_state = {'level': 'total', 'selections': {}}
            else:
                # Go back one level
                new_level = max(0, current_state['level'] - 1)
                new_state = {
                    'level': new_level,
                    'selections': dict(list(current_state['selections'].items())[:new_level])
                }
                
        # Handle chart click
        elif click_data:
            selected_value = click_data['annotation']['text'].replace('⯆', '').strip()
            
            if current_state['level'] == 'total':
                # If at total view, move to first level
                new_state = {'level': 0, 'selections': {}}
            else:
                # Add selection and move to next level
                current_field = hierarchy[current_state['level']]
                new_selections = dict(current_state['selections'])
                new_selections[current_field] = selected_value
                new_level = min(len(hierarchy) - 1, current_state['level'] + 1)
                new_state = {
                    'level': new_level,
                    'selections': new_selections
                }

        # Determine button visibility
        button_style = {
            'display': 'none' if new_state['level'] == 'total' else 'inline-block',
            'marginBottom': '10px'
        }

        # Generate title
        if new_state['level'] == 'total':
            title = f"Total {title_prefix}"
        elif new_state['level'] == 1:
            selected = new_state['selections'].get(hierarchy[0], '')
            title = f"{selected} {title_prefix} by {hierarchy[new_state['level']]}"
        else:
            title = f"{title_prefix} by {hierarchy[new_state['level']]}"

        return new_state, button_style, title

        pass


    @app.callback(
        Output(f'{chart_id}-chart', 'figure'),
        Input(f'view-state-{chart_id}', 'data')
    )
    def update_chart(view_state):
        # Handle total view case
        if view_state['level'] == 'total':
            return create_total_chart(
                df=df,
                run_a=run_a,
                run_b=run_b,
                color_map=color_map,
                name=title_prefix
            )   

        # Apply selections to filter data
        filtered_df = df.copy()
        for field, value in view_state['selections'].items():
            filtered_df = filtered_df[filtered_df[field] == value]  

        # Get units
        unique_units = filtered_df["Unit"].unique().tolist()
        units_str = f"{', '.join(unique_units)}"

        # Get current faceting dimension
        facet_column = hierarchy[view_state['level']]

        # Aggregate data
        agg_df = filtered_df.groupby(
            ['Period', facet_column, 'Scenario']
        )['PV'].sum().reset_index()

        # Convert and sort periods
        agg_df['Period'] = pd.to_numeric(agg_df['Period'])
        agg_df = agg_df.sort_values('Period')
        agg_df['Period'] = agg_df['Period'].astype(str)

        # Get period list for x-axis ordering
        period_list = sorted(agg_df['Period'].unique())

        # Complete periods for any missing values
        agg_df = complete_periods(
            agg_df,
            period_list,
            [facet_column, 'Scenario']
        )   

        # Determine if we can drill deeper
        can_drill_deeper = view_state['level'] < len(hierarchy) - 1 

        # Create and return faceted chart
        return create_faceted_chart(
            agg_df=agg_df,
            facet_column=facet_column,
            run_a=run_a,
            run_b=run_b,
            color_map=color_map,
            period_list=period_list,
            can_drill=can_drill_deeper,
            units_str=units_str
        )

def register_callbacks(app, chart_configs):
    # Register concordance callback
    create_concordance_cb(app)
    create_obj_cb(app)
    
    # Register callbacks for each chart
    for chart_id, config in chart_configs.items():
        create_view_callbacks(
            app,
            chart_id=chart_id,
            title_prefix=config['title_prefix'],
            hierarchy=config['hierarchy'],
            df=config['df']
        )


# Concordance Div and Callback
def create_concordance_div():
    """Create the concordance container div based on DataFrame content"""    
    base_div = html.Div([         
        # Content changes based on whether DataFrame is empty
        html.Div([
            # No entries message
            html.Div([
                html.P("Every combination of Attribute/Process/Commodity has an equivalent entry in the concordance table.",
                       style={
                           'textAlign': 'center',
                           'fontSize': '16px',
                           'color': '#666',
                           'backgroundColor': '#f8f9fa',
                           'padding': '20px',
                           'borderRadius': '8px',
                           'marginTop': '20px'
                       })
            ])
        ]) if df_no_concordance.empty else html.Div([
            html.H3("Missing concordances", style={'display': 'inline'}),       
            # Table with entries
            html.P("These categories exist in the data, but not in the concordance file! Please consider adding them."),
            dash_table.DataTable(
                id='data-table',
                columns=[{"name": i, "id": i} for i in df_no_concordance.columns],
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
                page_size=25,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
            )
        ])
    ], id="missing-concordances-container", 
       style={'display': 'none', 'marginTop': '30px'})
    
    return base_div

def create_concordance_cb(app):
    @app.callback(
        [Output('missing-concordances-container', 'style'),
         Output('concordance-button', 'children')],
        [Input('concordance-button', 'n_clicks')],
        [State('missing-concordances-container', 'style')]
    )
    def toggle_concordances(n_clicks, current_style):
        if n_clicks is None:
            return {'display': 'none', 'marginTop': '30px'}, 'Show missing concordances ▼'
        
        if current_style is None or current_style.get('display') == 'none':
            return {'display': 'block', 'marginTop': '30px'}, 'Hide missing concordances ▲'
        else:
            return {'display': 'none', 'marginTop': '30px'}, 'Show missing concordances ▼'

# Objective Function Div and Callback

def create_obj_div():
    # Write out the objective functions 
    def get_obj_for_run(run, df = df_objective_function):
        """Uses the objective function data, filters it for the run, and returns the result"""
        obj = df[df["Scenario"] == run]        
        # pull value
        obj_value = obj.iloc[0,1]
        return f"{obj_value:,.2f}"
          
        
    
    base_div = html.Div([         
        # Content changes based on whether DataFrame is empty        
            html.H3("Objective Functions", style={'display': 'inline'}),       
            # Table with entries
            html.P("The resulting objective function for each run:"),
            html.Ul([
                html.Li(f"{run_a}: {get_obj_for_run(run_a)}"),
                html.Li(f"{run_b}: {get_obj_for_run(run_b)}"),
                ])
            ], 
        id="objective-function-container", 
        style={'display': 'none', 'marginTop': '30px'}
        )
    
    return base_div

def create_obj_cb(app):
    @app.callback(
        [Output('objective-function-container', 'style'),
         Output('objective-function-button', 'children')],
        [Input('objective-function-button', 'n_clicks')],
        [State('objective-function-container', 'style')]
    )
    def toggle_objective_function(n_clicks, current_style):
        if n_clicks is None:
            return {'display': 'none', 'marginTop': '30px'}, 'Show objective functions ▼'
        
        if current_style is None or current_style.get('display') == 'none':
            return {'display': 'block', 'marginTop': '30px'}, 'Hide objective functions ▲'
        else:
            return {'display': 'none', 'marginTop': '30px'}, 'Show objective functions ▼'


# Define Layout

def create_sidebar_layout(chart_configs):
    return html.Div([
        html.H3("Contents", style={'marginBottom': '20px'}),
        html.Ul([
            html.Li([
                html.A(
                    config['title_prefix'],
                    href=f'#{chart_id}',
                    id=f'link-{chart_id}',
                    style={
                        'color': '#0066cc',
                        'textDecoration': 'none',
                        'cursor': 'pointer'
                    }
                )
            ]) for chart_id, config in chart_configs.items()
        ], style={'listStyleType': 'none', 'padding': 0})
    ], style={
        'position': 'fixed',
        'top': '20px',
        'left': '20px',
        'width': '160px',
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'zIndex': 1000
    })

def create_header_layout():
    return html.Div([
        #Title and buttons
        html.Div([
            html.H1('TIMES at a glance', 
                   style={'textAlign': 'left', 'marginBottom': '20px'}),
            # Buttons
            html.Div([
                html.Button('Show missing concordances ▼',
                        id='concordance-button',
                        style={'backgroundColor': '#f0f0f0',
                               'border': '1px solid #ddd',
                               'borderRadius': '4px',
                               'padding': '8px 15px',
                               'cursor': 'pointer',
                               'marginTop': '5px',
                               'marginBottom': '5px',                               
                               'text-align': 'left',
                               'minWidth': 'fit-content'

                             }),
                html.Button('Show objective functions ▼',
                            id='objective-function-button',
                            style={'backgroundColor': '#f0f0f0',
                                   'border': '1px solid #ddd',
                                   'borderRadius': '4px',
                                   'padding': '8px 15px',
                                   'cursor': 'pointer',
                                   'marginTop': '5px',
                                   'marginBottom': '5px',                                   
                                   'text-align': 'left',
                                   'minWidth': 'fit-content'
                                   }),

                ], style={'position': 'absolute',
                          'right' : '20px',
                          'top' : '40px',                                                    
                          'display': 'flex', 
                          'flexDirection': 'column',  
                          'width': '220px',
                          'alignItems': 'flex-end',
                          'zIndex': 1
                    })
            
        ]),
        # Subtitle
        html.Div([
            html.H3(f"Comparisons between ", 
                       style={'display': 'inline'}),
                html.Span(run_a, style={'backgroundColor': color_map[run_a], 'color': 'white', 'padding': '5px 10px', 'borderRadius': '3px'}),
                html.H3(" and ", style={'display': 'inline'}),
                html.Span(run_b, style={'backgroundColor': color_map[run_b], 'color': 'white', 'padding': '5px 10px', 'borderRadius': '3px'}),
        ]),
        # Missing concordances (hidden div)
        create_concordance_div(),
        create_obj_div()
        
        ])

def create_chart_layouts(chart_configs):
    
    # Create chart configs
    return html.Div([
        *create_stores(chart_configs),  
        *create_chart_containers(chart_configs)
    ])


# Create App
def run_glance_app():
    # Initialize app
    app = dash.Dash(__name__, suppress_callback_exceptions=True)

    # Define all charts    

    # Set up layout
    app.layout = html.Div([
        dcc.Store(id='dummy-output'),  # For the clientside callback
        
        # Two-column layout
        html.Div([
            # Sidebar
            create_sidebar_layout(chart_configs),
            # Main content
            html.Div([
                create_header_layout(),
                create_chart_layouts(chart_configs)
            ], style={
                'marginLeft': '240px',  # Leave space for sidebar
                'width': 'calc(100% - 240px)',  # Take remaining width
                'paddingTop': '20px'
            })
        ]),
    ], style={'fontFamily': 'Calibri'})

    app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <script>
                    window.dash_clientside = Object.assign({}, window.dash_clientside, {
                        clientside: {
                            scrollToSection: function(n_clicks, ...hrefs) {
                                if (n_clicks) {
                                    const clickedIndex = hrefs.findIndex((_, i) => arguments[i] > 0);
                                    if (clickedIndex >= 0 && hrefs[clickedIndex]) {  // Check if href exists
                                        const href = hrefs[clickedIndex];
                                        if (href && typeof href === 'string') {  // Verify href is a valid string
                                            const targetId = href.substring(1);
                                            const element = document.getElementById(targetId);
                                            if (element) {
                                                element.scrollIntoView({ behavior: 'smooth' });
                                            }
                                        }
                                    }
                                }
                                return {};
                            }
                        }
                    });
                </script>
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
    
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='scrollToSection'
        ),
        Output('dummy-output', 'data'),
        [Input(f'link-{chart_id}', 'n_clicks') for chart_id in chart_configs.keys()],
        [State(f'link-{chart_id}', 'href') for chart_id in chart_configs.keys()]
    )
    # Register all chart and button callbacks
    register_callbacks(app, chart_configs)
    
    return app