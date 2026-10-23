"""07 - SpaceX Launch Records Dashboard (Plotly Dash)

Run:   python 07_dash_app.py      then open http://127.0.0.1:8050
Data:  ../data/spacex_launch_dash.csv (IBM course file, 56 launches)
"""
import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "data", "spacex_launch_dash.csv")
if not os.path.exists(CSV):  # download the course file once
    url = ("https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
           "IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_dash.csv")
    pd.read_csv(url).to_csv(CSV, index=False)

spacex_df = pd.read_csv(CSV)
max_payload = spacex_df["Payload Mass (kg)"].max()
min_payload = spacex_df["Payload Mass (kg)"].min()

# dropdown options: "All Sites" + every launch site
sites = sorted(spacex_df["Launch Site"].unique())
site_options = [{"label": "All Sites", "value": "ALL"}] + [{"label": s, "value": s} for s in sites]

# one fixed color per booster version, so every chart uses the same colors
BOOSTER_COLORS = {"v1.0": "#8c8c8c", "v1.1": "#e05252", "FT": "#2a9d8f", "B4": "#7b61ff", "B5": "#f4a261"}

app = Dash(__name__)
app.layout = html.Div([
    html.H1("SpaceX Launch Records Dashboard",
            style={"textAlign": "center", "color": "#503D36", "font-size": 40}),

    # TASK 1: launch site dropdown
    dcc.Dropdown(id="site-dropdown", options=site_options, value="ALL",
                 placeholder="Select a Launch Site here", searchable=True),
    html.Br(),

    # TASK 2: pie chart with successful launches
    html.Div(dcc.Graph(id="success-pie-chart")),
    html.Br(),

    html.P("Payload range (Kg):"),
    # TASK 3: payload range slider
    dcc.RangeSlider(id="payload-slider", min=0, max=10000, step=1000,
                    marks={i: str(i) for i in range(0, 10001, 2500)},
                    value=[min_payload, max_payload]),

    # TASK 4: scatter chart payload vs. launch outcome
    html.Div(dcc.Graph(id="success-payload-scatter-chart")),
])


# TASK 2: callback for the pie chart
@app.callback(Output("success-pie-chart", "figure"), Input("site-dropdown", "value"))
def get_pie_chart(entered_site):
    if entered_site == "ALL":
        # share of all successful launches that came from each site
        fig = px.pie(spacex_df, values="class", names="Launch Site",
                     title="Total Successful Launches by Site")
    else:
        # success (1) vs. failure (0) for the chosen site
        site_df = spacex_df[spacex_df["Launch Site"] == entered_site]
        counts = site_df["class"].value_counts().rename({1: "Success", 0: "Failure"}).reset_index()
        counts.columns = ["Outcome", "Count"]
        fig = px.pie(counts, values="Count", names="Outcome", color="Outcome",
                     color_discrete_map={"Success": "#2a9d8f", "Failure": "#e05252"},
                     title=f"Total Success vs. Failure Launches for site {entered_site}")
    fig.update_layout(font=dict(size=16))
    return fig


# TASK 4: callback for the scatter chart
@app.callback(Output("success-payload-scatter-chart", "figure"),
              [Input("site-dropdown", "value"), Input("payload-slider", "value")])
def get_scatter_chart(entered_site, payload_range):
    low, high = payload_range
    df = spacex_df[spacex_df["Payload Mass (kg)"].between(low, high)]
    if entered_site != "ALL":
        df = df[df["Launch Site"] == entered_site]
    title = "Correlation between Payload and Success for " + ("all Sites" if entered_site == "ALL" else entered_site)
    fig = px.scatter(df, x="Payload Mass (kg)", y="class", color="Booster Version Category",
                     color_discrete_map=BOOSTER_COLORS,
                     category_orders={"Booster Version Category": list(BOOSTER_COLORS)},
                     title=title + f" (payload {low:,.0f}–{high:,.0f} kg)")
    fig.update_traces(marker=dict(size=12, opacity=0.8))
    fig.update_layout(font=dict(size=16))
    return fig


if __name__ == "__main__":
    app.run(debug=False, port=8050)
