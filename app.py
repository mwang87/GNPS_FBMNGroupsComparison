# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
from dash.dependencies import Input, Output
import os
from zipfile import ZipFile
import urllib.parse
from flask import Flask, send_from_directory

import pandas as pd
import requests
from upsetplot import from_memberships
from upsetplot import plot
from matplotlib import pyplot
import uuid

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS FBMN Group Comparison Dashboard", href="#")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DASHBOARD = [
    dbc.CardHeader(html.H5("GNPS FBMN Group Comparison Dashboard")),
    dbc.CardBody(
        [   
            dcc.Location(id='url', refresh=False),

            html.Div(id='version', children="Version - 0.1"),

            html.Br(),
            html.H3(children='GNPS Task Selection'),
            dbc.Input(className="mb-3", id='gnps_task', placeholder="Enter GNPS FBMN Task ID"),
            html.Br(),
            
            html.H3(children='Metadata Selection'),
            dcc.Dropdown(
                id="metadata_columns",
                options=[{"label" : "Default", "value": "Default"}],
                multi=False
            ),
            html.Br(),
            html.H3(children='Term Selection'),
            dcc.Dropdown(
                id="metadata_terms",
                options=[{"label" : "Default", "value": "Default"}],
                multi=True
            ),
            html.Br(),
            html.H3(children='Intensity Threshold'),
            dbc.Input(className="mb-3", id='intensity_threshold', placeholder="Intensity Threshold for Presence/Abscence", value=1000),
            html.Br(),
            html.H3(children='Plots'),
            dcc.Loading(
                id="upset_plot",
                children=[html.Div([html.Div(id="loading-output-4")])],
                type="default",
            )
        ]
    )
]

BODY = dbc.Container(
    [
        dbc.Row([dbc.Col(dbc.Card(DASHBOARD)),], style={"marginTop": 30}),
    ],
    className="mt-12",
)

app.layout = html.Div(children=[NAVBAR, BODY])


def _get_task_df(task):
    remote_url = "https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task={}&file=feature_statistics/data_long.csv".format(task)
    df = pd.read_csv(remote_url, sep=",")
    return df

# This enables parsing the URL to shove a task into the qemistree id
@app.callback(Output('gnps_task', 'value'),
              [Input('url', 'pathname')])
def determine_task(pathname):
    # Otherwise, lets use the url
    if pathname is not None and len(pathname) > 1:
        return pathname[1:]
    else:
        return dash.no_update

@app.callback([Output('metadata_columns', 'options'), Output('metadata_columns', 'value')],
              [Input('gnps_task', 'value')])
def determine_columns(gnps_task):
    # Otherwise, lets use the url
    if gnps_task is not None and len(gnps_task) > 1:
        df = _get_task_df(gnps_task)
        acceptable_columns = [column for column in df.columns if "ATTRIBUTE_" in column]
        output_options = []
        for column in acceptable_columns:
            output_options.append({"label" : column, "value": column})
        return [output_options, acceptable_columns[0]]
    else:
        return [{"label" : "X", "value": "Y"}, dash.no_update]

@app.callback([Output('metadata_terms', 'options'), Output('metadata_terms', 'value')],
              [Input('gnps_task', 'value'), Input('metadata_columns', 'value')])
def determine_terms(gnps_task, metadata_columns):
    df = _get_task_df(gnps_task)
    merged_terms = list(set(df[metadata_columns].dropna()))

    terms_to_consider = set()
    for term in merged_terms:
        terms_to_consider = terms_to_consider | set(term.split(","))

    terms_to_consider = list(terms_to_consider)
    
    output_options = []
    for term in terms_to_consider:
        output_options.append({"label" : term, "value": term})

    return [output_options, terms_to_consider]

# This function will rerun at any time that the selection is updated for column
@app.callback(
    [Output('upset_plot', 'children')],
    [Input('gnps_task', 'value'), Input('metadata_columns', 'value'), Input('metadata_terms', 'value'), Input("intensity_threshold", "value")],
)
def create_plot(gnps_task, metadata_column, metadata_terms, intensity_threshold):
    data_df = _get_task_df(gnps_task)

    metadata_terms = set(metadata_terms)

    INTENSITY_THRESHOLD = float(intensity_threshold)

    data_df = data_df[data_df["featurearea"] > INTENSITY_THRESHOLD]

    membership = []
    grouped_df = data_df.groupby("featureid")
    for group_df in grouped_df:
        try:
            groups = set(group_df[1][metadata_column])
            groups = list(groups & metadata_terms)
            
            membership.append(groups)
        except:
            print("ERROR")
            raise
    
    upset_data_df = from_memberships(membership)

    plotting_object = plot(upset_data_df,
                            subset_size="count",
                            sort_by="cardinality",
                            orientation="horizontal",
                            show_counts=True)

    uuid_save = str(uuid.uuid4())
    pyplot.savefig("./output/{}.png".format(uuid_save))
    
    return [html.Img(src="/plot/{}".format(uuid_save))]

@server.route("/plot/<uuid_save>")
def download(uuid_save):
    """Serve a file from the upload directory."""
    return send_from_directory("./output", uuid_save + ".png")


if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
