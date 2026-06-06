# Carrito en memoria - se guarda mientras el bot está corriendo
carritos = {}

def obtener_carrito(telegram_id):
    """Retorna el carrito actual del cliente"""
    return carritos.get(telegram_id, [])

def agregar_producto(telegram_id, producto, cantidad):
    """
    Agrega un producto al carrito
    Si ya existe, suma la cantidad
    """
    if telegram_id not in carritos:
        carritos[telegram_id] = []

    # Buscar si el producto ya está en el carrito
    for item in carritos[telegram_id]:
        if item['nombre'] == producto['Nombre']:
            item['cantidad'] += cantidad
            return

    # Si no existe, agregarlo nuevo
    carritos[telegram_id].append({
        'nombre': producto['Nombre'],
        'precio': float(str(producto['Precio']).replace(',', '').replace('$', '')),
        'cantidad': cantidad
    })

def eliminar_producto(telegram_id, nombre_producto):
    """Elimina un producto específico del carrito"""
    if telegram_id in carritos:
        carritos[telegram_id] = [
            item for item in carritos[telegram_id]
            if item['nombre'] != nombre_producto
        ]

def vaciar_carrito(telegram_id):
    """Vacía completamente el carrito"""
    carritos[telegram_id] = []

def calcular_total(telegram_id):
    """Calcula el total del carrito"""
    carrito = obtener_carrito(telegram_id)
    return sum(item['precio'] * item['cantidad'] for item in carrito)

def carrito_vacio(telegram_id):
    """Verifica si el carrito está vacío"""
    return len(obtener_carrito(telegram_id)) == 0

def resumen_carrito(telegram_id):
    """Retorna un texto con el resumen del carrito"""
    carrito = obtener_carrito(telegram_id)
    if not carrito:
        return "🛒 Tu carrito está vacío."

    texto = "🛒 *Tu carrito de compras:*\n\n"
    for item in carrito:
        subtotal = item['precio'] * item['cantidad']
        texto += f"▪️ *{item['nombre']}*\n"
        texto += f"   {item['cantidad']} unidad(es) x ${item['precio']:,.0f} = ${subtotal:,.0f}\n\n"
    texto += f"💰 *Total: ${calcular_total(telegram_id):,.0f}*"
    return texto

def cantidad_productos(telegram_id):
    """Retorna cuántos productos diferentes hay en el carrito"""
    return len(obtener_carrito(telegram_id))