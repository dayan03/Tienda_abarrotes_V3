import gspread
from google.oauth2.service_account import Credentials
import os
import json
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def conectar():
    """Conecta con Google Sheets leyendo credenciales desde variable de entorno o archivo"""
    
    # En Render lee desde variable de entorno
    creds_json = os.environ.get("GOOGLE_CREDS")
    
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # En tu PC local lee desde el archivo
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CRED_PATH = os.path.join(BASE_DIR, 'credencials.json')
        creds = Credentials.from_service_account_file(CRED_PATH, scopes=SCOPES)
    
    client = gspread.authorize(creds)
    libro = client.open("Base_Datos_Abarrotes")
    return libro

def obtener_hoja(nombre_hoja):
    """Retorna una pestaña específica del libro"""
    libro = conectar()
    return libro.worksheet(nombre_hoja)

def leer_todos(nombre_hoja):
    """Lee todos los registros de una pestaña"""
    hoja = obtener_hoja(nombre_hoja)
    return hoja.get_all_records()

def agregar_fila(nombre_hoja, fila):
    """Agrega una fila nueva al final de una pestaña"""
    hoja = obtener_hoja(nombre_hoja)
    hoja.append_row(fila)

def actualizar_celda(nombre_hoja, fila, columna, valor):
    """Actualiza una celda específica"""
    hoja = obtener_hoja(nombre_hoja)
    hoja.update_cell(fila, columna, valor)

def buscar_fila(nombre_hoja, columna_nombre, valor_buscar):
    """
    Busca una fila donde columna_nombre == valor_buscar
    Retorna el registro y el número de fila (base 2)
    """
    registros = leer_todos(nombre_hoja)
    for i, registro in enumerate(registros, start=2):
        if str(registro.get(columna_nombre, '')) == str(valor_buscar):
            return registro, i
    return None, None