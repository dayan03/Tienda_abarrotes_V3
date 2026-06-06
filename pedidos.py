import sheets
import carrito as carrito_module
from datetime import datetime

def generar_id_pedido():
    """Genera un ID único para el pedido"""
    pedidos = sheets.leer_todos("Pedidos")
    return len(pedidos) + 1

def crear_pedido(telegram_id):
    """
    Crea un pedido con los productos del carrito
    Retorna el ID del pedido o None si el carrito está vacío
    """
    carrito = carrito_module.obtener_carrito(telegram_id)
    if not carrito:
        return None, 0

    # Construir texto de productos comprados
    productos_texto = ", ".join([
        f"{item['nombre']} x{item['cantidad']}"
        for item in carrito
    ])

    total = carrito_module.calcular_total(telegram_id)
    id_pedido = generar_id_pedido()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Guardar en Google Sheets pestaña Pedidos
    sheets.agregar_fila("Pedidos", [
        id_pedido,
        telegram_id,
        productos_texto,
        total,
        "Pendiente",
        fecha
    ])

    return id_pedido, total

def actualizar_estado_pedido(id_pedido, nuevo_estado):
    """
    Actualiza el estado de un pedido
    Estados posibles: Pendiente, En preparación, Enviado, Entregado, Cancelado
    """
    pedidos = sheets.leer_todos("Pedidos")
    for i, pedido in enumerate(pedidos, start=2):
        if str(pedido.get('ID_Pedido')) == str(id_pedido):
            sheets.actualizar_celda("Pedidos", i, 5, nuevo_estado)
            return True
    return False

def obtener_pedidos_cliente(telegram_id):
    """Retorna todos los pedidos de un cliente"""
    pedidos = sheets.leer_todos("Pedidos")
    return [
        p for p in pedidos
        if str(p.get('Telegram_ID')) == str(telegram_id)
    ]

def resumen_pedidos_cliente(telegram_id):
    """Retorna un texto con el historial de pedidos del cliente"""
    pedidos = obtener_pedidos_cliente(telegram_id)
    if not pedidos:
        return "📋 No tienes pedidos realizados aún."

    texto = "📋 *Tu historial de pedidos:*\n\n"
    for p in pedidos:
        texto += (
            f"🧾 *Pedido #{p.get('ID_Pedido')}*\n"
            f"🛍️ {p.get('Productos_Comprados')}\n"
            f"💰 Total: ${float(str(p.get('Total_Pago', 0)).replace(',', '')):,.0f}\n"
            f"📌 Estado: {p.get('Estado')}\n"
            f"📅 Fecha: {p.get('Fecha')}\n\n"
        )
    return texto

def actualizar_stock_productos(telegram_id):
    """Descuenta el stock de los productos comprados"""
    carrito = carrito_module.obtener_carrito(telegram_id)
    productos = sheets.leer_todos("Productos")

    for item in carrito:
        for i, producto in enumerate(productos, start=2):
            if producto['Nombre'] == item['nombre']:
                stock_actual = int(str(producto['Stock']).replace(',', ''))
                nuevo_stock = max(0, stock_actual - item['cantidad'])
                sheets.actualizar_celda("Productos", i, 4, nuevo_stock)
                break