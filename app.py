import json
import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
from datetime import datetime

# ---------------------------
# 1. Read JSON from file
# ---------------------------

with open("data.json") as f:
    data = json.load(f)

# ---------------------------
# 2. Process the data
# ---------------------------

df = pd.DataFrame(data)

# Convert the 'date' column to datetime
df['date'] = pd.to_datetime(df['date'])

# get time dimensions
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day

# Convert the 'rate' column to numeric
df['rate'] = pd.to_numeric(df['rate'])

# Calculate the rate percentage: 1 = 25% , 2 = 50% , 3 = 75% , 4 = 100%
df['rate_percent'] = df['rate'] * 100/4

df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str)

# Sort by date
df = df.sort_values('date')

# calculate the average of rate_percent by mail
df_avg = df.groupby(['year_month','year','month', 'mail'])['rate_percent'].mean().reset_index()
df_avg = df_avg.sort_values(['year','month']) 

# ---------------------------
# 3. Create the Dash app
# ---------------------------

app = Dash(__name__)

app.layout = html.Div([
    html.Hr(),
    html.H1(children="Customer satisfaction", style={'textAlign': 'center'}),
    html.Hr(),
    
    dcc.Dropdown(
        df_avg['mail'].unique(),
        id='mail-dropdown',
        style={'width': '48%'}
    ),

    dcc.Graph(id="graph"),

    html.Div([
        html.H3("Raw data"),
        html.Pre(df.to_string())
    ], style={'marginTop': 20})
])

# ---------------------------
# 4. Callback to update the graph
# ---------------------------

@app.callback(
    Output("graph", "figure"),
    Input("mail-dropdown", "value"),
)
def update_graph(selected_mail):
    # If no mail is selected, show all
    if selected_mail is None:
        filtered_df = df_avg
    else:
        # Ensure that selected_mail is a list
        if not isinstance(selected_mail, list):
            selected_mail = [selected_mail]
        
        # Filter the dataframe by the selected mail
        filtered_df = df_avg[df_avg['mail'].isin(selected_mail)]
    
    # Create the figure with the filtered data
    fig = go.Figure()
    
    # Add a bar for each mail
    for mail in filtered_df['mail'].unique():
        mail_data = filtered_df[filtered_df['mail'] == mail]
        fig.add_trace(go.Bar(
            x=mail_data['year_month'],
            y=mail_data['rate_percent'],
            name=mail,
            text=mail_data['rate_percent'].round(1).astype(str) + '%',
            textposition='auto'
        ))
    
    # Improve the graph layout
    fig.update_layout(
        title="Customer Satisfaction Over Time",
        xaxis_title='Date',
        yaxis_title='Satisfaction (%)',
        yaxis=dict(
            tickmode='array',
            tickvals=[0, 25, 50, 75, 100],
            ticktext=['0%', '25% (1)', '50% (2)', '75% (3)', '100% (4)'],
            range=[0, 105]  # Ensure that 100% is visible
        ),
        hovermode='x unified',
        barmode='group',  # Group the bars by date
        legend_title_text='Email',
        height=600
    )
    
    # Improve the tooltip
    fig.update_traces(
        hovertemplate='<br>'.join([
            'Date: %{x}',
            'Satisfaction: %{y:.1f}%',
            '<extra></extra>'
        ])
    )
    
    return fig

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)