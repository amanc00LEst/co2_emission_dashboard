import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


co2 = pd.read_csv("co2_emission.csv")
co2 = co2.rename(columns={
    'Entity': 'country',
    'Code': 'code',
    'Year': 'year',
    'Annual CO₂ emissions (tonnes )': 'co2_tonnes'
})

# Clean data
co2 = co2.dropna(subset=['co2_tonnes', 'code'])
co2['country'] = co2['country'].str.strip()
co2['year'] = co2['year'].astype(int)
co2['co2_tonnes'] = pd.to_numeric(co2['co2_tonnes'], errors='coerce')
co2['co2_million'] = co2['co2_tonnes'] / 1_000_000
co2 = co2.dropna(subset=['co2_million'])
co2 = co2[co2['year'] >= 1950]


valid_countries = sorted(co2['country'].unique())
available_years = sorted(co2['year'].unique())
latest_year = max(available_years)

# Initialize app
app = dash.Dash(__name__)
app.title = "CO2 Emissions Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Global CO₂ Emissions Dashboard", style={'textAlign': 'center'}),

    html.H3("World Map of CO₂ Emissions (1950-2017)", style={'textAlign': 'center'}),
    dcc.Graph(id='animated-world-map', style={"height": "600px"}),

    html.Div([
        html.Div([
            html.Label("Select Year for Comparison:"),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': str(y), 'value': y} for y in available_years],
                value=latest_year,
                clearable=False
            )
        ], style={'width': '45%', 'display': 'inline-block'})
    ], style={'padding': '20px'}),

    html.H3("Top 20 Countries by CO₂ Emissions in Selected Year", style={'textAlign': 'center'}),
    dcc.Graph(id='bar-chart', style={"height": "700px"}),

    html.Div([
        html.Div([
            html.Label("Number of Countries to Compare:"),
            dcc.Input(id='num-countries', type='number', min=1, max=10, value=1)
        ], style={'marginBottom': '20px'})
    ], style={'padding': '20px'}),

    html.Div(id='country-inputs', style={'padding': '20px'}),

    html.H3("CO₂ Emissions Comparison of Selected Countries", style={'textAlign': 'center'}),
    dcc.Graph(id='country-comparison', style={"height": "500px"})
])

# Animated World Map
@app.callback(
    Output('animated-world-map', 'figure'),
    Input('num-countries', 'value')
)
def animated_map(_):
    fig = px.choropleth(
        co2,
        locations="code",
        locationmode="ISO-3",
        color="co2_million",
        hover_name="country",
        animation_frame="year",
        color_continuous_scale="Reds",
        labels={'co2_million': 'CO₂ Emissions (Million tonnes)'}
    )
    fig.update_layout(
        title="Animated CO₂ Emissions by Country (1950-2017)",
        geo=dict(showframe=False, showcoastlines=True),
        margin={"r": 0, "t": 50, "l": 0, "b": 0}
    )
    return fig

# Dynamic Country Input Fields
@app.callback(
    Output('country-inputs', 'children'),
    Input('num-countries', 'value')
)
def render_country_inputs(n):
    return html.Div([
        html.Div([
            html.Label(f"Select Country {i+1}:", style={'marginRight': '10px'}),
            dcc.Dropdown(
                id={'type': 'country-dropdown', 'index': i},
                options=[{'label': c, 'value': c} for c in valid_countries],
                value=valid_countries[i % len(valid_countries)]
            )
        ], style={'marginBottom': '10px'}) for i in range(n)
    ])

# Bar Chart Callback
@app.callback(
    Output('bar-chart', 'figure'),
    Input('year-dropdown', 'value')
)
def update_bar_chart(selected_year):
    df_year = co2[(co2['year'] == selected_year) & (co2['country'] != 'World')]
    df_sorted = df_year.sort_values('co2_million', ascending=False).head(20)

    fig = px.bar(
        df_sorted,
        x='country',
        y='co2_million',
        text='co2_million',
        labels={'co2_million': 'CO₂ Emissions (Million tonnes)', 'country': 'Country'},
        title=f"Top 20 CO₂ Emitters in {selected_year}",
        log_y=True
    )

    fig.update_traces(marker_color='indianred', textposition='outside')
    fig.update_layout(xaxis_tickangle=-45, margin=dict(l=20, r=20, t=60, b=150))

    return fig

# Country Comparison Callback
@app.callback(
    Output('country-comparison', 'figure'),
    Input({'type': 'country-dropdown', 'index': dash.dependencies.ALL}, 'value')
)
def compare_countries(selected_countries):
    if not selected_countries:
        return go.Figure()

    df_filtered = co2[co2['country'].isin(selected_countries)]
    fig = px.line(
        df_filtered,
        x="year",
        y="co2_million",
        color="country",
        labels={'co2_million': 'CO₂ Emissions (Million tonnes)', 'year': 'Year'},
        title="CO₂ Emissions Comparison"
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=50, b=50),
        plot_bgcolor='rgba(240,240,240,0.5)'
    )

    return fig

# Run
server = app.server

if __name__ == '__main__':
    app.run(debug=True)
