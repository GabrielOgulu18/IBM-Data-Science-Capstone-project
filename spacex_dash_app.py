from pathlib import Path

import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px


# Read the provided dataset from the same folder as this script.
DATA_PATH = Path(__file__).resolve().parent / "spacex_launch_dash.csv"
spacex_df = pd.read_csv(DATA_PATH)
max_payload = spacex_df["Payload Mass (kg)"].max()
min_payload = spacex_df["Payload Mass (kg)"].min()

app = dash.Dash(__name__)

# TASK 1: Dropdown with 'ALL' plus the launch sites found in the CSV.
site_options = [{"label": "All Sites", "value": "ALL"}] + [
    {"label": site, "value": site}
    for site in sorted(spacex_df["Launch Site"].unique())
]

app.layout = html.Div(
    children=[
        html.H1(
            "SpaceX Launch Records Dashboard",
            style={"textAlign": "center", "color": "#503D36", "fontSize": 40},
        ),
        dcc.Dropdown(
            id="site-dropdown",
            options=site_options,
            value="ALL",
            placeholder="Select a Launch Site here",
            searchable=True,
            clearable=False,
        ),
        html.Br(),
        # TASK 2: Placeholder chart. The callback below supplies its figure.
        html.Div(dcc.Graph(id="success-pie-chart")),
        html.Br(),
        html.P("Payload range (Kg):"),
        # TASK 3: Range slider from 0 to 10,000 kg in steps of 1,000 kg.
        dcc.RangeSlider(
            id="payload-slider",
            min=0,
            max=10000,
            step=1000,
            marks={i: f"{i:,}" for i in range(0, 10001, 2000)},
            value=[min_payload, max_payload],
            allowCross=False,
        ),
        html.Br(),
        # TASK 4: The scatter plot is updated by its own callback below.
        html.Div(dcc.Graph(id="success-payload-scatter-chart")),
    ],
    style={"maxWidth": "1100px", "margin": "auto", "padding": "24px"},
)


# TASK 2: Pie chart responds to the site-dropdown.
@app.callback(
    Output("success-pie-chart", "figure"),
    Input("site-dropdown", "value"),
)
def get_pie_chart(entered_site):
    if entered_site == "ALL":
        # Count only successful (class=1) launches for each site.
        successes = (
            spacex_df[spacex_df["class"] == 1]
            .groupby("Launch Site")
            .size()
            .reset_index(name="Successful Launches")
        )
        fig = px.pie(
            successes,
            values="Successful Launches",
            names="Launch Site",
            title="Successful launches by site (all sites)",
        )
    else:
        # For one site, include both failures (0) and successes (1).
        filtered_df = spacex_df[spacex_df["Launch Site"] == entered_site]
        counts = filtered_df["class"].value_counts().reindex([0, 1], fill_value=0)
        outcome_df = pd.DataFrame(
            {"Outcome": ["Failed", "Successful"], "Launches": counts.to_numpy()}
        )
        fig = px.pie(
            outcome_df,
            values="Launches",
            names="Outcome",
            title=f"Landing outcomes at {entered_site}",
            color="Outcome",
            color_discrete_map={"Failed": "#D9534F", "Successful": "#2CA02C"},
        )
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


# TASK 4: Scatter plot responds to both the site and payload-range inputs.
@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    [Input("site-dropdown", "value"), Input("payload-slider", "value")],
)
def get_scatter_chart(entered_site, payload_range):
    low, high = payload_range
    if entered_site == "ALL":
        filtered_df = spacex_df
        title = "Payload mass vs. landing outcome — all sites"
    else:
        filtered_df = spacex_df[spacex_df["Launch Site"] == entered_site]
        title = f"Payload mass vs. landing outcome — {entered_site}"

    # Keep only launches with payload mass inside the selected range.
    filtered_df = filtered_df[
        filtered_df["Payload Mass (kg)"].between(low, high)
    ]

    fig = px.scatter(
        filtered_df,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        hover_data=["Launch Site", "Flight Number", "Booster Version"],
        title=title,
        labels={"class": "Landing outcome"},
    )
    fig.update_traces(marker=dict(size=10, opacity=0.75))
    fig.update_yaxes(
        tickvals=[0, 1],
        ticktext=["Failed (0)", "Successful (1)"],
        range=[-0.2, 1.2],
    )
    fig.update_layout(margin=dict(l=30, r=20, t=60, b=30))
    return fig


if __name__ == "__main__":
    app.run(debug=True)
