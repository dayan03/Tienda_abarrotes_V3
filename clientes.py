import sheets
from datetime import datetime

def existe_cliente(telegram_id):
    """Verifica si un cliente ya está registrado"""
    registro, _ = sheets.buscar_fila("Clientes", "Telegram_ID", telegram_id)
    return registro is not None

def obtener_cliente(telegram_id):
    """Retorna los datos de un cliente por su Telegram ID"""
    registro, _ = sheets.buscar_fila("Clientes", "Telegram_ID", telegram_id)
    return registro

def registrar_cliente(telegram_id, nombre, telefono, direccion):
    """
    Registra un cliente nuevo en Google Sheets
    Retorna True si se registró, False si ya existía
    """
    if existe_cliente(telegram_id):
        return False
    
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    sheets.agregar_fila("Clientes", [
        telegram_id,
        nombre,
        telefono,
        direccion,
        fecha
    ])
    return True

def actualizar_cliente(telegram_id, campo, valor):
    """Actualiza un campo específico de un cliente"""
    columnas = {
        'Nombre': 2,
        'Telefono': 3,
        'Direccion': 4
    }
    if campo not in columnas:
        return False
    
    _, num_fila = sheets.buscar_fila("Clientes", "Telegram_ID", telegram_id)
    if num_fila:
        sheets.actualizar_celda("Clientes", num_fila, columnas[campo], valor)
        return True
    return False

def resumen_cliente(telegram_id):
    """Retorna un texto con los datos del cliente"""
    cliente = obtener_cliente(telegram_id)
    if not cliente:
        return "❌ Cliente no encontrado."
    return (
        f"👤 *Tus datos registrados:*\n\n"
        f"📛 *Nombre:* {cliente.get('Nombre', 'N/A')}\n"
        f"📱 *Teléfono:* {cliente.get('Telefono', 'N/A')}\n"
        f"📍 *Dirección:* {cliente.get('Direccion', 'N/A')}\n"
        f"📅 *Registro:* {cliente.get('Fecha_Registro', 'N/A')}"
    )