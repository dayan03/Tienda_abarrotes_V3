import sheets

def obtener_config():
    """Lee la configuración de la tienda desde Google Sheets"""
    try:
        registros = sheets.leer_todos("Configuracion")
        if registros:
            return registros[0]
        return {}
    except Exception as e:
        print(f"Error al leer configuración: {e}")
        return {}

def nombre_tienda():
    config = obtener_config()
    return config.get('nombre_tienda', 'Tienda Abarrotes')

def telefono_tienda():
    config = obtener_config()
    return config.get('telefono', 'No disponible')

def direccion_tienda():
    config = obtener_config()
    return config.get('direccion', 'No disponible')

def horario_tienda():
    config = obtener_config()
    return config.get('horario', 'No disponible')

def ubicacion_maps():
    config = obtener_config()
    return config.get('ubicacion_maps', 'No disponible')

def info_completa():
    """Retorna toda la info de la tienda en un solo texto"""
    config = obtener_config()
    return (
        f"🏪 *{config.get('nombre_tienda', 'Tienda Abarrotes')}*\n\n"
        f"📱 *Teléfono:* {config.get('telefono', 'N/A')}\n"
        f"📍 *Dirección:* {config.get('direccion', 'N/A')}\n"
        f"🕐 *Horario:* {config.get('horario', 'N/A')}\n"
        f"🗺️ *Ubicación:* {config.get('ubicacion_maps', 'N/A')}"
    )