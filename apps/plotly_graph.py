import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
from pyjstat import pyjstat
import requests
import pandas as pd # primary data structure library
import numpy as np  # scientific computing in Python
import json # import geographical borders files
from json_creator import create_json
import pathlib
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../datasets").resolve()
mun_loc = json.load(open(DATA_PATH.joinpath('kommuner_2020_low_res.json'),'r'))

old_year_codes = ["1997K4","1998K1","1998K2","1998K3","1998K4","1999K1","1999K2","1999K3","1999K4","2000K1","2000K2","2000K3","2000K4","2001K1","2001K2","2001K3","2001K4","2002K1","2002K2","2002K3","2002K4","2003K1","2003K2","2003K3","2003K4","2004K1","2004K2","2004K3","2004K4","2005K1","2005K2","2005K3","2005K4","2006K1","2006K2","2006K3","2006K4","2007K1","2007K2","2007K3","2007K4","2008K1","2008K2","2008K3","2008K4","2009K1","2009K2","2009K3","2009K4","2010K1","2010K2","2010K3","2010K4","2011K1","2011K2","2011K3","2011K4","2012K1","2012K2","2012K3","2012K4","2013K1","2013K2","2013K3","2013K4","2014K1","2014K2","2014K3","2014K4","2015K1","2015K2","2015K3","2015K4","2016K1","2016K2","2016K3","2016K4","2017K1","2017K2","2017K3","2017K4","2018K1","2018K2","2018K3","2018K4","2019K1","2019K2","2019K3","2019K4"]
year_code = ["2020K1","2020K2","2020K3","2020K4","2021K1","2021K2","2021K3"]
population_columns = ['Befolkning ved inngangen av kvartalet', 'Døde', 'Fødde','Fødselsoverskot', 'Innflytting, innalandsk', 'Innvandring','Utflytting, innalandsk', 'Utvandring']
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1('Data in a map', style={"textAlign": "center"}),

    html.Div([
        html.Div([
            html.Pre(children="Statistic", style={"fontSize":"150%"}),
            dcc.Dropdown(
                id='dropdown-select', value='2021K3', clearable=False,
                persistence=True, persistence_type='session',
                options=[{'label': x, 'value': x} for x in year_code]
                #options=[{'label':'2021 Third quarter', 'value': '2021K3'}]
                
            )
        ], className='six columns'),
        html.Div([
            html.Pre(children="Statistic", style={"fontSize":"150%"}),
            dcc.Dropdown(
                id='stat', value='Døde', clearable=False,
                persistence=True, persistence_type='session',
                options=[{'label': x, 'value': x} for x in population_columns]
                #options=[{'label': "Døde", 'value': "Døde"}]
                
            )
        ], className='six columns'),

        html.Div([
            html.Pre(children="Total or per capita", style={"fontSize": "150%"}),
            dcc.RadioItems(
                id='total-percap', value='Total', 
                options=[{'label': 'Per Capita', 'value': 'percap'},
                {'label':'Total', 'value' : 'total'}],
                inline=True 
            )
            ], className='six columns'),
    ], className='row'),
    dcc.Store(id='intermediate-value'),

    dcc.Graph(id='my-map', figure={}),
])

@app.callback(
    Output('intermediate-value','data'), Input('dropdown-select', 'value'))
def get_data(value):
  json2 = create_json(value)
  from pyjstat import pyjstat
  import requests
  POST_URL = 'https://data.ssb.no/api/v0/no/table/01222/'
  payload = json2
  result = requests.post(POST_URL, json = payload)
  dataset = pyjstat.Dataset.read(result.text)
  df = dataset.write('dataframe')
  df_pivot=df.pivot(index='region', columns='statistikkvariabel',values=['value'])
  df_pivot.columns = df_pivot.columns.droplevel()
  modified_df=df_pivot.rename_axis(None,axis=1)
  modified_df=modified_df.reset_index()
  return modified_df.to_json(date_format='iso', orient='split')


@app.callback(
    Output(component_id='my-map', component_property='figure'),
    [Input(component_id='stat', component_property='value'),
     Input(component_id='total-percap', component_property='value'),
     Input('intermediate-value', 'data')]
)
def display_value(stat, total_percap, intermediate_value):
    modified_df = pd.read_json(intermediate_value, orient='split')
    if total_percap == 'percap':
      modified_df['column1'] = modified_df[stat]/modified_df['Befolkning ved inngangen av kvartalet']
      fig = px.choropleth_mapbox(modified_df, locations='region', geojson= mun_loc, color='column1',hover_name = 'region',
                   hover_data = [stat],
                    mapbox_style="carto-positron",
                    center={"lat": 65, "lon": 10},
                     zoom=3,
                     opacity=0.5)
    elif total_percap == 'total':
      fig = px.choropleth_mapbox(modified_df, locations='region', geojson= mun_loc, color=stat, hover_name = 'region',
                   hover_data = [stat],
                    mapbox_style="carto-positron",
                    center={"lat": 65, "lon": 10},
                     zoom=3,
                     opacity=0.5)

    return fig
if __name__ == '__main__':
    app.run_server(debug=True)