from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

app = Dash()
server = app.server

JIRA_URL = "https://proyectos3420wm.atlassian.net"
EMAIL = "lchanquetti@3420wm.com"
API_TOKEN = "ATATT3xFfGF0_3EuG7gG9kftFKTQWkMGT8j8Lr2dF3T5GWZbfee23kUU_5oj_AuB3hHNUvXSeIhS0rdMrXygiNAU-8tQ9-DR8PIAfmZYfvtpK7lTACQu7giG-m1dz3ev2IAkgjDrBp7d6cSMrwlhfYDRc9HYMgTtKx7QLLV29Vi_y-wH9G_SV4I=2EFB6C49"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {
    "Accept": "application/json"
}

# Obtener los tableros del proyecto PW
def obtener_boards():
    url = f"{JIRA_URL}/rest/agile/1.0/board"
    response = requests.get(url, headers=headers, auth=auth)
    return response.json()["values"]

def obtener_id_board(project_key):
    for e in obtener_boards():
        if e["location"]["projectKey"] == project_key:
            return e["id"]

def obtener_sprints(board_id):
    url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint"
    response = requests.get(url, headers=headers, auth=auth)
    return response.json()["values"]

def obtener_id_sprint_activo(board_id):
    for e in obtener_sprints(board_id):
        if e["state"] == "active":
            return e["id"]

     

def obtener_issues_sprint(sprint_id):
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
    response = requests.get(url, headers=headers, auth=auth)
    return response.json()["issues"] #[1]["fields"]


board_id = obtener_id_board("UR")
id_sprint_activo = obtener_id_sprint_activo(board_id)
lista_issues = obtener_issues_sprint(id_sprint_activo)

cant_tareas_por_hacer = 0
cant_en_curso = 0
cant_finalizada = 0
cant_qa = 0
cant_aprob_qa = 0
cant_prod = 0
cant_aprob_prod = 0

for issue in lista_issues:
    nombre_estado = issue["fields"]["status"]["name"] 
    if nombre_estado == "Tareas por hacer": cant_tareas_por_hacer += 1
    elif nombre_estado == "En curso": cant_en_curso += 1
    elif nombre_estado == "Finalizada": cant_finalizada += 1
    elif nombre_estado == "Control de calidad": cant_qa += 1
    elif nombre_estado == "APROBADO QA": cant_aprob_qa += 1
    elif nombre_estado == "PRODUCCION": cant_prod += 1
    elif nombre_estado == "APROBADO PRODUCCION": cant_aprob_prod += 1

cant_estados = [cant_tareas_por_hacer, cant_en_curso, cant_finalizada, cant_qa, cant_aprob_qa, cant_prod, cant_aprob_prod]   



df = pd.DataFrame({
    "Fruit": ["Tareas por hacer", "En curso", "Listo", "QA", "Aprobado QA", "Produccion", "Aprobado produccion"],
    "Amount": cant_estados,
})

fig = px.bar(df, x="Estados", y="Cantidad de issues", title="Estados vs Cantidad - Issues")

# Layout de la aplicación
app.layout = html.Div(children=[
    html.H1('Ejemplo con Dash'),
    dcc.Graph(id='grafico-frutas', figure=fig)
])

if __name__ == '__main__':
    app.run(debug=True)


