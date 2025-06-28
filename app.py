import requests
import pandas as pd
from datetime import datetime
from dash import Dash, dcc, html
import plotly.graph_objs as go

# --------------------------
# CONFIGURACIÓN DE JIRA API
# --------------------------
JIRA_DOMAIN = "proyectos3420wm.atlassian.net"
API_USER = "lchanquetti@3420wm.com"
API_TOKEN = "ATATT3xFfGF0a_WlAhmi1Of468OoqgdRso7nVA2HT7bYYiCmUC8aYfralmYuO5WZYHDPrNNweb7xvTVpiGsA-HB-Y_l-C5AvTStvgp15MUZWEKXkuQFL27fyK5qh3pAOEeRVmH8XJoBCLV3DUBJOfpLCWc2ViAaEujyKfAjXkGMcecSie9Y55LA=74B793B1"
PROJECT_KEY = "PW"  # ← Aquí tu clave de proyecto

auth = (API_USER, API_TOKEN)
headers = {"Accept": "application/json"}

# --------------------------
# FUNCIONES PARA LA API
# --------------------------

def obtener_board_id(project_key):
    url = f"{JIRA_DOMAIN}/rest/agile/1.0/board"
    params = {"projectKeyOrId": project_key}
    response = requests.get(url, auth=auth, headers=headers, params=params)
    data = response.json()
    if data["values"]:
        return data["values"][0]["id"]
    else:
        raise Exception("No se encontró un board para el proyecto.")

def obtener_sprint_id(board_id):
    url = f"{JIRA_DOMAIN}/rest/agile/1.0/board/{board_id}/sprint"
    response = requests.get(url, auth=auth, headers=headers)
    data = response.json()
    for sprint in data["values"]:
        if sprint["state"] == "active":  # puedes cambiar a 'future' o 'closed'
            return sprint["id"]
    raise Exception("No se encontró un sprint activo.")

def obtener_fechas_sprint(sprint_id):
    url = f"{JIRA_DOMAIN}/rest/agile/1.0/sprint/{sprint_id}"
    response = requests.get(url, auth=auth, headers=headers)
    data = response.json()
    fecha_inicio = datetime.strptime(data["startDate"][:10], "%Y-%m-%d")
    fecha_fin = datetime.strptime(data["endDate"][:10], "%Y-%m-%d")
    return fecha_inicio, fecha_fin

def obtener_issues_sprint(sprint_id):
    url = f"{JIRA_DOMAIN}/rest/agile/1.0/sprint/{sprint_id}/issue"
    issues = []
    start_at = 0
    max_results = 50

    while True:
        params = {"startAt": start_at, "maxResults": max_results}
        response = requests.get(url, auth=auth, headers=headers, params=params)
        data = response.json()
        issues += data["issues"]
        if start_at + max_results >= data["total"]:
            break
        start_at += max_results

    return issues

def procesar_burndown(issues, fecha_inicio, fecha_fin):
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin)
    pendientes_por_dia = []

    for fecha in fechas:
        pendientes = 0
        for issue in issues:
            creado = datetime.strptime(issue["fields"]["created"][:10], "%Y-%m-%d")
            resuelto = issue["fields"]["resolutiondate"]
            resuelto = datetime.strptime(resuelto[:10], "%Y-%m-%d") if resuelto else None

            if creado <= fecha and (resuelto is None or resuelto > fecha):
                pendientes += 1

        pendientes_por_dia.append({"fecha": fecha, "pendientes": pendientes})

    return pd.DataFrame(pendientes_por_dia)

# --------------------------
# FLUJO COMPLETO
# --------------------------

board_id = obtener_board_id(PROJECT_KEY)
sprint_id = obtener_sprint_id(board_id)
fecha_inicio, fecha_fin = obtener_fechas_sprint(sprint_id)
issues = obtener_issues_sprint(sprint_id)
df_burndown = procesar_burndown(issues, fecha_inicio, fecha_fin)

# --------------------------
# CREAR DASH APP
# --------------------------

app = Dash(__name__)
server = app.server
app.layout = html.Div([
    html.H1("Gráfico de Trabajo Pendiente (Burndown)"),
    dcc.Graph(
        id='burndown-chart',
        figure={
            'data': [
                go.Scatter(
                    x=df_burndown["fecha"],
                    y=df_burndown["pendientes"],
                    mode='lines+markers',
                    name='Pendientes'
                )
            ],
            'layout': go.Layout(
                title='Burndown Chart del Sprint',
                xaxis={'title': 'Fecha'},
                yaxis={'title': 'Incidencias Pendientes'},
                hovermode='closest'
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

