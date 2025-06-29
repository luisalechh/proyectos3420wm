from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

app = Dash()
server = app.server

df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas"],
    "Amount": [6, 5, 7],
})

fig = px.bar(df, x="Fruit", y="Amount", title="Cantidad de Frutas")

# Layout de la aplicación
app.layout = html.Div(children=[
    html.H1('Ejemplo con Dash'),
    dcc.Graph(id='grafico-frutas', figure=fig)
])

if __name__ == '__main__':
    app.run(debug=True)


