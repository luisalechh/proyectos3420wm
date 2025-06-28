import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from datetime import datetime, timedelta
from dash import Dash, dcc, html
import plotly.graph_objs as go

# Configuración
email = "lchanquetti@3420wm.com"
api_token = "ATATT3xFfGF0a_WlAhmi1Of468OoqgdRso7nVA2HT7bYYiCmUC8aYfralmYuO5WZYHDPrNNweb7xvTVpiGsA-HB-Y_l-C5AvTStvgp15MUZWEKXkuQFL27fyK5qh3pAOEeRVmH8XJoBCLV3DUBJOfpLCWc2ViAaEujyKfAjXkGMcecSie9Y55LA=74B793B1"
domain = "proyectos3420wm.atlassian.net"
project_key = "PW"
auth = HTTPBasicAuth(email, api_token)
headers = {"Accept": "application/json"}

# 1. Obtener board del proyecto
board_url = f"https://{domain}/rest/agile/1.0/board"
params = {'projectKeyOrId': project_key}
board_resp = requests.get(board_url, headers=headers, auth=auth, params=params)
board_id = board_resp.json()["values"][0]["id"]

# 2. Obtener sprint activo
sprint_url = f"https://{domain}/rest/agile/1.0/board/{board_id}/sprint"
sprints_resp = requests.get(sprint_url, headers=headers, auth=auth)
active_sprint = next(s for s in sprints_resp.json()["values"] if s["state"] == "active")
sprint_id = active_sprint["id"]

# Fechas del sprint
fecha_inicio = datetime.strptime(active_sprint["startDate"][:10], "%Y-%m-%d")
fecha_fin = datetime.strptime(active_sprint["endDate"][:10], "%Y-%m-%d")
fechas = [fecha_inicio + timedelta(days=i) for i in range((fecha_fin - fecha_inicio).days + 1)]

# 3. Obtener issues del sprint
issues_url = f"https://{domain}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=100"
issues_resp = requests.get(issues_url, headers=headers, auth=auth)
issues = issues_resp.json()["issues"]

# 4. Estado por fecha
estado_por_fecha = {fecha: 0 for fecha in fechas}

for issue in issues:
    key = issue["key"]
    estado_inicial = issue["fields"]["status"]["name"]
    creado = datetime.strptime(issue["fields"]["created"][:10], "%Y-%m-%d")
    issue_url = f"https://{domain}/rest/api/3/issue/{key}?expand=changelog"
    detail = requests.get(issue_url, headers=headers, auth=auth).json()
    cambios = detail.get("changelog", {}).get("histories", [])
    
    historial = []
    for h in cambios:
        fecha = datetime.strptime(h["created"][:10], "%Y-%m-%d")
        for item in h["items"]:
            if item["field"] == "status":
                historial.append((fecha, item["fromString"], item["toString"]))

    historial.sort()
    estado_actual = estado_inicial

    for fecha in fechas:
        for cambio_fecha, _, nuevo_estado in historial:
            if cambio_fecha <= fecha:
                estado_actual = nuevo_estado
            else:
                break

        if estado_actual != "PRODUCCION":
            estado_por_fecha[fecha] += 1

# Datos para la gráfica
valores = list(estado_por_fecha.values())
linea_ideal = [valores[0] - i * (valores[0] / (len(fechas) - 1)) for i in range(len(fechas))]

# Crear app Dash
app = Dash(__name__)
app = app.server
app.layout = html.Div([
    html.H1("Gráfica de trabajo pendiente (Burndown Jira)"),
    dcc.Graph(
        figure={
            'data': [
                go.Scatter(x=fechas, y=valores, mode='lines+markers', name='Trabajo pendiente', line=dict(color='red')),
                go.Scatter(x=fechas, y=linea_ideal, mode='lines', name='Línea ideal', line=dict(dash='dash', color='gray'))
            ],
            'layout': go.Layout(
                title="Burndown Chart del Sprint Activo",
                xaxis=dict(title='Fecha'),
                yaxis=dict(title='Número de Tareas'),
                hovermode='closest'
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)


