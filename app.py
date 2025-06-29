from dash import Dash, html, dcc, Output, Input
import plotly.express as px
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

# Cargar variables de entorno (.env o Render)
load_dotenv()

# Configuración de Jira
JIRA_URL = "https://proyectos3420wm.atlassian.net"
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

# Inicializar la aplicación Dash
app = Dash()
server = app.server

# Funciones para consultar Jira API
def obtener_projects_keys():
    url = f"{JIRA_URL}/rest/api/3/project"
    response = requests.get(url,headers=headers,auth=auth)
    lista_projects = response.json()
    lista_projects_keys = []
    for project in lista_projects:
        lista_projects_keys.append(project["key"])
    return lista_projects_keys
    
def obtener_boards():
    url = f"{JIRA_URL}/rest/agile/1.0/board"
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code != 200:
        print("Error al obtener tableros:", response.status_code, response.text)
        return []
    return response.json().get("values", [])

def obtener_id_board(project_key):
    for e in obtener_boards():
        if e.get("location", {}).get("projectKey") == project_key:
            return e["id"]
    return None

def obtener_sprints(board_id):
    url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint"
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        return response.json().get("values", [])
    return []

def obtener_id_sprint_activo(board_id):
    for e in obtener_sprints(board_id):
        if e.get("state") == "active":
            return e["id"]
    return None

def obtener_issues_sprint(sprint_id):
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        return response.json().get("issues", [])
    return []

# Layout de la app
app.layout = html.Div([
    html.H1("Estados de tareas en Sprint Activo"),
    dcc.Dropdown(
        id="proyecto-dropdown",
        options=[{"label": key, "value": key} for key in obtener_projects_keys()],
        placeholder="Seleccione un proyecto"
    ),
    dcc.Graph(id="grafico-estados"),
    dcc.Interval(id="intervalo", interval=30*1000, n_intervals=0)  # 30 segundos
])

# Callback que actualiza la gráfica cada 30 segundos
@app.callback(
    Output("grafico-estados", "figure"),
    [Input("proyecto-dropdown", "value"), Input("intervalo", "n_intervals")]
)
def actualizar_grafico(project_key, n_intervals):
    if not project_key:
        return px.bar(title="Seleccione un proyecto")
        
    estados = [
        "Tareas por hacer", "En curso", "Finalizada",
        "Control de calidad", "APROBADO QA", "PRODUCCION", "APROBADO PRODUCCION"
    ]
    conteo = {estado: 0 for estado in estados}

    board_id = obtener_id_board("UR")
    if not board_id:
        return px.bar(title="Error: no se encontró el board")

    id_sprint_activo = obtener_id_sprint_activo(board_id)
    if not id_sprint_activo:
        return px.bar(title="Error: no hay sprint activo")

    lista_issues = obtener_issues_sprint(id_sprint_activo)
    for issue in lista_issues:
        nombre_estado = issue["fields"]["status"]["name"]
        if nombre_estado in conteo:
            conteo[nombre_estado] += 1

    df = pd.DataFrame({
        "Estados": estados,
        "Cantidad de issues": [conteo[estado] for estado in estados]
    })

    fig = px.bar(df, x="Estados", y="Cantidad de issues", title=f"Estados de issues en Sprint Activo - Proyecto {project_key}")
    return fig

if __name__ == "__main__":
    app.run(debug=True)



