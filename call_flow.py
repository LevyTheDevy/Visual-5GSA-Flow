import json

import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash.dependencies import Input, Output, State

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Available flows and their corresponding JSON files
flows = {
    '5G Registration': 'flows/5G_Registration_Flow.json',
    'SIP Call': 'flows/SIP_Voice_Call.json',
    'Handover': 'flows/hand_over_flow.json',
    'NAS Authentication': 'flows/steps_authentication_nas_security.json',
    'Deregistration Flow': 'flows/steps_deregistration.json',
    'E911 Call': 'flows/steps_e911_call.json',
    'Inital RRC Access': 'flows/steps_initial_access_rrc.json',
    'Inter RAT Handover': 'flows/steps_inter_rat_handover.json',
    'PDU Session': 'flows/steps_pdu_session.json',
    'SIP Registration': 'flows/steps_sip_registration.json',
    'UE Context Release': 'flows/steps_ue_context_release.json',
    'WiFI Calling Enablement': 'flows/steps_wifi_calling.json'
}


# Function to load nodes and steps from a JSON file
def load_flow(file):
    with open(file, 'r') as f:
        data = json.load(f)
    nodes = data['nodes']
    steps = data['steps']
    return nodes, steps


# Initial load with a default flow
default_flow = list(flows.values())[0]
nodes, steps = load_flow(default_flow)


# Create node elements for Cytoscape
def create_node_elements(nodes):
    return [{'data': {'id': node['id'], 'label': node['label'], 'color': node['color']}} for node in nodes]


node_elements = create_node_elements(nodes)


# Custom marks for the slider with step labels
def create_marks(steps):
    return {i: f'Step {i + 1}' for i in range(len(steps))}


marks = create_marks(steps)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("5G Flow Visualization"), className="mb-2")
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id='flow-dropdown',
            options=[{'label': key, 'value': value} for key, value in flows.items()],
            value=default_flow,
            clearable=False
        ), width=6),
        dbc.Col([
            dbc.Button("Play", id="play-button", n_clicks=0)
        ])
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col(
            cyto.Cytoscape(
                id='cytoscape',
                layout={'name': 'breadthfirst'},
                style={'width': '100%', 'height': '600px', 'background-color': '#2f2f2f'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'color': 'white',
                            'background-color': 'data(color)',
                            'shape': 'rectangle',
                            'width': 'label',
                            'height': 'label',
                            'padding': '10px',
                            'font-size': '16px',
                            'border-width': '2px',
                            'border-color': '#2f2f2f'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'label': 'data(label)',
                            'text-rotation': 'autorotate',
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle',
                            'arrow-scale': 2,
                            'line-color': 'data(color)',
                            'target-arrow-color': 'data(color)',
                            'color': 'data(color)',
                            'font-size': '12px'
                        }
                    },
                    {
                        'selector': 'edge[label]',
                        'style': {
                            'label': 'data(label)',
                            'color': 'data(color)',
                            'font-size': '12px',
                            'text-background-opacity': 1,
                            'text-background-color': '#2f2f2f',
                            'text-background-shape': 'roundrectangle'
                        }
                    }
                ],
                elements=node_elements,
                userZoomingEnabled=True,
                userPanningEnabled=True
            ),
            width=12
        )
    ], className="mb-2"),
    html.Hr(),
    dbc.Row([
        dbc.Col(
            html.Div(id='log-output',
                     style={'height': '200px', 'overflow-y': 'scroll', 'background-color': '#333', 'color': 'white',
                            'padding': '10px'}),
            width=12
        )
    ], className="mb-2"),
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Label('Step Progress:'),
            dcc.Slider(
                id='step-slider',
                min=0,
                max=len(steps) - 1,
                step=1,
                value=0,
                marks=marks
            )
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Label('Delay (ms):'),
                dbc.Input(id='delay-input', type='number', value=5000, min=100, step=100)
            ], width=2),
        ]),
        dcc.Interval(id='interval', interval=1000, n_intervals=0, disabled=True)
    ], className="mb-2")
], fluid=True)


@app.callback(
    [Output('cytoscape', 'elements'),
     Output('cytoscape', 'stylesheet'),
     Output('log-output', 'children'),
     Output('step-slider', 'max'),
     Output('step-slider', 'marks'),
     Output('step-slider', 'value'),
     Output('interval', 'disabled'),
     Output('play-button', 'children'),
     Output('interval', 'interval')],
    [Input('flow-dropdown', 'value'),
     Input('step-slider', 'value'),
     Input('play-button', 'n_clicks'),
     Input('interval', 'n_intervals'),
     Input('delay-input', 'value')],
    [State('interval', 'disabled')]
)
def update_graph(flow_file, step, play_clicks, n_intervals, delay, interval_disabled):
    nodes, steps = load_flow(flow_file)
    node_elements = create_node_elements(nodes)

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'flow-dropdown':
        step = 0
        disabled = True
        button_label = "Play"
    elif triggered_id == 'play-button':
        if interval_disabled:
            step = 0
            disabled = False
            button_label = "Pause"
        else:
            disabled = True
            button_label = "Play"
    elif triggered_id == 'interval':
        if step < len(steps) - 1:
            step += 1
            disabled = False
            button_label = "Pause"
        else:
            disabled = True
            button_label = "Play"
    else:
        disabled = interval_disabled
        button_label = "Pause" if not interval_disabled else "Play"

    current_edges = [
        {'data': {'source': steps[i]['source'], 'target': steps[i]['target'],
                  'label': f"[{i + 1}] - {steps[i]['label']}", 'color': steps[i]['color']}}
        for i in range(step + 1)
    ]

    log_output = [html.P(f"[{i + 1}] {steps[i]['source']} ---> {steps[i]['target']} | '{steps[i]['label']}'",
                         style={'color': steps[i]['color']}) for i in range(step + 1)]

    marks = create_marks(steps)

    active_node = steps[step]['source']
    updated_stylesheet = [
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'text-valign': 'center',
                'color': 'white',
                'background-color': 'data(color)',
                'shape': 'rectangle',
                'width': 'label',
                'height': 'label',
                'padding': '10px',
                'font-size': '16px',
                'border-width': '2px',
                'border-color': '#2f2f2f'
            }
        },
        {
            'selector': f'node[id = "{active_node}"]',
            'style': {
                'border-color': '#FF0000',
                'border-width': '4px'
            }
        },
        {
            'selector': 'edge',
            'style': {
                'label': 'data(label)',
                'text-rotation': 'autorotate',
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'arrow-scale': 2,
                'line-color': 'data(color)',
                'target-arrow-color': 'data(color)',
                'color': 'data(color)',
                'font-size': '12px'
            }
        },
        {
            'selector': 'edge[label]',
            'style': {
                'label': 'data(label)',
                'color': 'data(color)',
                'font-size': '12px',
                'text-background-opacity': 1,
                'text-background-color': '#2f2f2f',
                'text-background-shape': 'roundrectangle'
            }
        }
    ]

    return node_elements + current_edges, updated_stylesheet, log_output, len(
        steps) - 1, marks, step, disabled, button_label, delay


if __name__ == '__main__':
    app.run_server(debug=True)
