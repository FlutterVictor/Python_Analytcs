# app.py
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table
import plotly.graph_objs as go

# Inicializa app
app = Dash(__name__)
server = app.server

# Leitura padrão do CSV
df = pd.read_csv('STD_Geral.csv', parse_dates=['Data'], dayfirst=True)

# Layout
app.layout = html.Div([
    html.H1("Dashboard Andaime e Pintura", style={'textAlign':'center'}),
    
    # Filtros de data
    html.Div([
        html.Label("Data Início:"),
        dcc.DatePickerSingle(id='dataInicio', date=df['Data'].min()),
        html.Label("Data Fim:"),
        dcc.DatePickerSingle(id='dataFim', date=df['Data'].max()),
        html.Button("Aplicar filtro", id='btnApplyFilter'),
        html.Button("Voltar ao Menu", id='btnVoltarMenu')
    ], style={'marginBottom':'20px'}),

    # Indicadores
    html.Div([
        html.Div([html.H3("HH Total"), html.P(id='hhTotal')], style={'display':'inline-block','width':'20%'}),
        html.Div([html.H3("ML Montados"), html.P(id='mlMontados')], style={'display':'inline-block','width':'20%'}),
        html.Div([html.H3("Mont Presente"), html.P(id='montPresente')], style={'display':'inline-block','width':'20%'}),
        html.Div([html.H3("STD Semanal"), html.P(id='stdSemanal')], style={'display':'inline-block','width':'20%'}),
        html.Div([html.H3("Meta Atingida"), html.P(id='metaAtingida')], style={'display':'inline-block','width':'20%'})
    ], style={'textAlign':'center','marginBottom':'20px'}),

    # Gráfico de linha
    dcc.Graph(id='graficoLinha'),

    # Ranking
    dash_table.DataTable(
        id='rankingTable',
        columns=[{"name": "Encarregado", "id": "nome"},
                 {"name": "% Meta", "id": "pctMeta"},
                 {"name": "Indicador", "id": "indicador"}],
        style_cell={'textAlign': 'center'}
    ),

    # Tabela de amostra
    dash_table.DataTable(
        id='tabelaDados',
        columns=[{"name": i, "id": i} for i in df.columns],
        page_size=5,
        style_cell={'textAlign': 'center'}
    ),

    # Upload CSV
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload CSV'),
        multiple=False
    )
])

# Callbacks
@app.callback(
    Output('hhTotal','children'),
    Output('mlMontados','children'),
    Output('montPresente','children'),
    Output('stdSemanal','children'),
    Output('metaAtingida','children'),
    Output('graficoLinha','figure'),
    Output('rankingTable','data'),
    Output('tabelaDados','data'),
    Input('btnApplyFilter','n_clicks'),
    State('dataInicio','date'),
    State('dataFim','date'),
    State('upload-data','contents')
)
def atualizar_dashboard(n_clicks, dataInicio, dataFim, upload):
    dff = df.copy()

    if dataInicio:
        dff = dff[dff['Data'] >= pd.to_datetime(dataInicio)]
    if dataFim:
        dff = dff[dff['Data'] <= pd.to_datetime(dataFim)]

    # Métricas
    somaHH = dff['HH Total'].sum()
    somaML = dff['ML Montados'].sum()
    somaMont = dff['Mont.Presente'].mean()
    somaMLPrev = dff['ML PREVISTO'].sum()
    std = somaHH / somaML if somaML>0 else 0
    meta = (somaML / somaMLPrev * 100) if somaMLPrev>0 else 0

    # Gráfico linha
    mlPorDia = dff.groupby(dff['Data'].dt.dayofweek)['ML Montados'].sum()
    dias = ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']
    mlPorDia = [mlPorDia.get(i,0) for i in range(7)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dias, y=mlPorDia, mode='lines+markers', line=dict(color='#0b63d6')))
    fig.update_layout(margin=dict(l=20,r=20,t=20,b=20), height=300)

    # Ranking
    ranking = dff.groupby('Encarregado Responsavel').agg({'ML Montados':'sum','ML PREVISTO':'sum','HH Total':'sum'})
    ranking['pctMeta'] = (ranking['ML Montados']/ranking['ML PREVISTO']*100).fillna(0)
    ranking['indicador'] = ['↑' if h/ml <=0.22 else '↓' for h,ml in zip(ranking['HH Total'], ranking['ML Montados'])]
    ranking = ranking.sort_values('pctMeta', ascending=False).reset_index()
    ranking_data = ranking.head(5)[['Encarregado Responsavel','pctMeta','indicador']].to_dict('records')

    # Tabela dados
    tabela_data = dff.head(5).to_dict('records')

    return f"{somaHH:.1f}", f"{somaML:.0f} m", f"{somaMont:.1f}", f"{std:.2f}", f"{meta:.0f}%", fig, ranking_data, tabela_data

if __name__ == '__main__':
    app.run_server(debug=True)
