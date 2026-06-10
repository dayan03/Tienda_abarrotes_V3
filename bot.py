import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)
import config
import clientes
import carrito as carrito_module
import pedidos as pedidos_module
import sheets

load_dotenv()
TOKEN = os.environ.get("TOKEN")

# ───── LOGGING ─────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ───── ESTADOS DE CONVERSACIÓN ─────
REG_NOMBRE, REG_TELEFONO, REG_DIRECCION = 1, 2, 3
CANTIDAD = 4

# ───── TECLADO PRINCIPAL ─────
def teclado_principal():
    return ReplyKeyboardMarkup([
        ["🛍️ Ver Productos", "🛒 Mi Carrito"],
        ["📋 Mis Pedidos",   "📞 Contacto"],
        ["👤 Registrarme"]
    ], resize_keyboard=True)

# ══════════════════════════════════════
#              INICIO
# ══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre_usuario = update.message.from_user.first_name
    nombre = config.nombre_tienda()
    await update.message.reply_text(
        f"👋 ¡Hola *{nombre_usuario}*! Bienvenido a *{nombre}* 🛒\n\n"
        f"Estoy aquí para ayudarte con tus compras.\n"
        f"Usa los botones para navegar 👇",
        parse_mode='Markdown',
        reply_markup=teclado_principal()
    )

# ══════════════════════════════════════
#           VER PRODUCTOS
# ══════════════════════════════════════
async def ver_productos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ Cargando productos...",
    )
    productos = sheets.leer_todos("Productos")

    if not productos:
        await update.message.reply_text(
            "😕 No hay productos disponibles por ahora.",
            reply_markup=teclado_principal()
        )
        return

    await update.message.reply_text(
        "🛍️ *Nuestros productos disponibles:*\n\nSelecciona uno para agregarlo al carrito 👇",
        parse_mode='Markdown'
    )

    for p in productos:
        stock = int(str(p.get('Stock', 0)).replace(',', ''))
        if stock <= 0:
            continue

        texto = (
            f"📦 *{p['Nombre']}*\n"
            f"💰 Precio: ${float(str(p['Precio']).replace(',','').replace('$','')):,.0f}\n"
            f"📊 Stock disponible: {stock} unidades\n"
            f"⚖️ Peso/Contenido: {p.get('Peso_Contenido', 'N/A')}\n"
            f"📝 {p.get('Descripcion', '')}\n"
        )

        botones = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"🛒 Agregar al carrito",
                callback_data=f"agregar|{p['Nombre']}"
            )]
        ])

        # Si tiene imagen válida
        imagen = str(p.get('Imagen_URL', '')).strip()
        if imagen.startswith('http'):
            try:
                await update.message.reply_photo(
                    photo=imagen,
                    caption=texto,
                    parse_mode='Markdown',
                    reply_markup=botones
                )
                continue
            except Exception:
                pass

        await update.message.reply_text(
            texto,
            parse_mode='Markdown',
            reply_markup=botones
        )

# ══════════════════════════════════════
#         AGREGAR AL CARRITO
# ══════════════════════════════════════
async def callback_agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nombre_producto = query.data.split("|")[1]
    context.user_data['producto_seleccionado'] = nombre_producto

    await query.message.reply_text(
        f"¿Cuántas unidades de *{nombre_producto}* deseas agregar?\n\n"
        f"Escribe solo el número 👇",
        parse_mode='Markdown'
    )
    return CANTIDAD

async def recibir_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    if not texto.isdigit() or int(texto) <= 0:
        await update.message.reply_text(
            "⚠️ Por favor escribe un número válido mayor a 0."
        )
        return CANTIDAD

    cantidad = int(texto)
    nombre = context.user_data.get('producto_seleccionado')
    productos = sheets.leer_todos("Productos")
    producto = next((p for p in productos if p['Nombre'] == nombre), None)

    if not producto:
        await update.message.reply_text("❌ Producto no encontrado.")
        return ConversationHandler.END

    stock = int(str(producto.get('Stock', 0)).replace(',', ''))
    if cantidad > stock:
        await update.message.reply_text(
            f"⚠️ Solo hay *{stock}* unidades disponibles de *{nombre}*.\n"
            f"Por favor escribe una cantidad menor.",
            parse_mode='Markdown'
        )
        return CANTIDAD

    telegram_id = update.message.from_user.id
    carrito_module.agregar_producto(telegram_id, producto, cantidad)

    await update.message.reply_text(
        f"✅ *{nombre}* x{cantidad} agregado al carrito.\n\n"
        f"¿Qué deseas hacer ahora?",
        parse_mode='Markdown',
        reply_markup=teclado_principal()
    )
    return ConversationHandler.END

# ══════════════════════════════════════
#            MI CARRITO
# ══════════════════════════════════════
async def ver_carrito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    if carrito_module.carrito_vacio(telegram_id):
        await update.message.reply_text(
            "🛒 Tu carrito está vacío.\n\n"
            "Usa *🛍️ Ver Productos* para agregar productos.",
            parse_mode='Markdown',
            reply_markup=teclado_principal()
        )
        return

    resumen = carrito_module.resumen_carrito(telegram_id)
    carrito = carrito_module.obtener_carrito(telegram_id)

    # Botones para cada producto
    botones = []
    for item in carrito:
        botones.append([
            InlineKeyboardButton(
                f"❌ Quitar {item['nombre']}",
                callback_data=f"quitar|{item['nombre']}"
            )
        ])

    botones.append([
        InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_pedido")
    ])
    botones.append([
        InlineKeyboardButton("🗑️ Vaciar Carrito", callback_data="vaciar_carrito")
    ])

    await update.message.reply_text(
        resumen,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(botones)
    )

async def callback_carrito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    data = query.data

    # ── Quitar producto ──
    if data.startswith("quitar|"):
        nombre = data.split("|")[1]
        carrito_module.eliminar_producto(telegram_id, nombre)

        if carrito_module.carrito_vacio(telegram_id):
            await query.edit_message_text("🛒 Tu carrito está vacío.")
            return

        carrito = carrito_module.obtener_carrito(telegram_id)
        botones = []
        for item in carrito:
            botones.append([
                InlineKeyboardButton(
                    f"❌ Quitar {item['nombre']}",
                    callback_data=f"quitar|{item['nombre']}"
                )
            ])
        botones.append([InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_pedido")])
        botones.append([InlineKeyboardButton("🗑️ Vaciar Carrito", callback_data="vaciar_carrito")])

        await query.edit_message_text(
            f"🗑️ *{nombre}* eliminado.\n\n" + carrito_module.resumen_carrito(telegram_id),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(botones)
        )

    # ── Vaciar carrito ──
    elif data == "vaciar_carrito":
        carrito_module.vaciar_carrito(telegram_id)
        await query.edit_message_text(
            "🗑️ Carrito vaciado correctamente.\n\n"
            "Usa *🛍️ Ver Productos* para seguir comprando.",
            parse_mode='Markdown'
        )

    # ── Confirmar pedido ──
    elif data == "confirmar_pedido":
        if not clientes.existe_cliente(telegram_id):
            await query.message.reply_text(
                "⚠️ Para confirmar tu pedido primero debes registrarte.\n\n"
                "Usa el botón 👤 *Registrarme* y luego vuelve a tu carrito.",
                parse_mode='Markdown',
                reply_markup=teclado_principal()
            )
            return

        # Crear pedido en Google Sheets
        id_pedido, total = pedidos_module.crear_pedido(telegram_id)

        if not id_pedido:
            await query.message.reply_text("❌ Error al crear el pedido. Intenta de nuevo.")
            return

        # Actualizar stock
        pedidos_module.actualizar_stock_productos(telegram_id)

        # Vaciar carrito
        carrito_module.vaciar_carrito(telegram_id)

        cliente = clientes.obtener_cliente(telegram_id)
        await query.edit_message_text(
            f"🎉 *¡Pedido confirmado!*\n\n"
            f"📋 Número de pedido: *#{id_pedido}*\n"
            f"👤 Cliente: {cliente.get('Nombre', 'N/A')}\n"
            f"📍 Entrega en: {cliente.get('Direccion', 'N/A')}\n"
            f"💰 Total: *${total:,.0f}*\n\n"
            f"📌 Estado: *Pendiente*\n\n"
            f"Nos comunicaremos contigo pronto. ¡Gracias por tu compra! 🛒",
            parse_mode='Markdown'
        )

# ══════════════════════════════════════
#           MIS PEDIDOS
# ══════════════════════════════════════
async def mis_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    if not clientes.existe_cliente(telegram_id):
        await update.message.reply_text(
            "⚠️ No estás registrado aún.\n\n"
            "Usa el botón 👤 *Registrarme* primero.",
            parse_mode='Markdown',
            reply_markup=teclado_principal()
        )
        return

    resumen = pedidos_module.resumen_pedidos_cliente(telegram_id)
    await update.message.reply_text(
        resumen,
        parse_mode='Markdown',
        reply_markup=teclado_principal()
    )

# ══════════════════════════════════════
#         CONTACTO Y UBICACIÓN
# ══════════════════════════════════════
async def contacto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = config.info_completa()
    await update.message.reply_text(
        f"📞 *Contacto y Ubicación*\n\n{info}",
        parse_mode='Markdown',
        reply_markup=teclado_principal()
    )

# ══════════════════════════════════════
#           REGISTRAR CLIENTE
# ══════════════════════════════════════
async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    if clientes.existe_cliente(telegram_id):
        resumen = clientes.resumen_cliente(telegram_id)
        botones = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ Eliminar mi registro", callback_data="eliminar_registro")]
        ])
        await update.message.reply_text(
            f"✅ ¡Ya estás registrado!\n\n{resumen}\n\n"
            f"¿Deseas eliminar tu registro?",
            parse_mode='Markdown',
            reply_markup=botones
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👤 *Vamos a registrarte*\n\n"
        "¿Cuál es tu *nombre completo*?",
        parse_mode='Markdown'
    )
    return REG_NOMBRE

async def reg_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_nombre'] = update.message.text.strip()
    await update.message.reply_text(
        "📱 ¿Cuál es tu *número de teléfono*?",
        parse_mode='Markdown'
    )
    return REG_TELEFONO

async def reg_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reg_telefono'] = update.message.text.strip()
    await update.message.reply_text(
        "📍 ¿Cuál es tu *dirección de entrega*?",
        parse_mode='Markdown'
    )
    return REG_DIRECCION

async def reg_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    nombre = context.user_data['reg_nombre']
    telefono = context.user_data['reg_telefono']
    direccion = update.message.text.strip()

    clientes.registrar_cliente(telegram_id, nombre, telefono, direccion)

    await update.message.reply_text(
        f"🎉 *¡Registro exitoso!*\n\n"
        f"👤 *Nombre:* {nombre}\n"
        f"📱 *Teléfono:* {telefono}\n"
        f"📍 *Dirección:* {direccion}\n\n"
        f"¡Ya puedes hacer tus compras! 🛒",
        parse_mode='Markdown',
        reply_markup=teclado_principal()
    )
    return ConversationHandler.END

async def mensaje_desconocido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Usa los botones del menú para navegar 👇",
        reply_markup=teclado_principal()
    )

async def callback_eliminar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    telegram_id = query.from_user.id
    data = query.data

    if data == "eliminar_registro":
        # Pedir confirmación
        botones = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Sí, eliminar", callback_data="confirmar_eliminar")],
            [InlineKeyboardButton("❌ No, cancelar", callback_data="cancelar_eliminar")]
        ])
        await query.edit_message_text(
            "⚠️ *¿Estás seguro que deseas eliminar tu registro?*\n\n"
            "Esta acción no se puede deshacer.",
            parse_mode='Markdown',
            reply_markup=botones
        )

    elif data == "confirmar_eliminar":
        clientes.eliminar_cliente(telegram_id)
        await query.edit_message_text(
            "🗑️ Tu registro ha sido eliminado correctamente.\n\n"
            "Puedes volver a registrarte cuando quieras con el botón 👤 *Registrarme*",
            parse_mode='Markdown'
        )

    elif data == "cancelar_eliminar":
        await query.edit_message_text(
            "✅ Operación cancelada. Tu registro sigue activo.",
            parse_mode='Markdown'
        )

  
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Operación cancelada.",
        reply_markup=teclado_principal()
    )
    return ConversationHandler.END

async def eliminar_cliente(telegram_id):
    """Elimina el registro de un cliente"""
    sheet = sheets.obtener_hoja("Clientes")
    _, num_fila = sheets.buscar_fila("Clientes", "Telegram_ID", telegram_id)
    if num_fila:
        sheet.delete_rows(num_fila)
        return True
    return False

# ══════════════════════════════════════
#              MAIN
# ══════════════════════════════════════
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Content-Length', '14')
        self.end_headers()
        self.wfile.write(b"Bot corriendo OK")
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Content-Length', '14')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

def iniciar_servidor():
    puerto = int(os.environ.get("PORT", 8080))
    servidor = HTTPServer(("0.0.0.0", puerto), PingHandler)
    servidor.serve_forever()

def main():
    # Iniciar servidor web en hilo separado
    hilo = threading.Thread(target=iniciar_servidor, daemon=True)
    hilo.start()
    print(f"✅ Servidor web iniciado")

    app = ApplicationBuilder().token(TOKEN).build()

    # Conversación: Registro de cliente
    conv_registro = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^👤 Registrarme$"), registrar)
        ],
        states={
            REG_NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_nombre)],
            REG_TELEFONO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_telefono)],
            REG_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_direccion)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Conversación: Agregar cantidad al carrito
    conv_cantidad = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_agregar, pattern="^agregar\\|")
        ],
        states={
            CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Registrar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_registro)
    app.add_handler(conv_cantidad)
    app.add_handler(MessageHandler(filters.Regex("^🛍️ Ver Productos$"), ver_productos))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Mi Carrito$"), ver_carrito))
    app.add_handler(MessageHandler(filters.Regex("^📋 Mis Pedidos$"), mis_pedidos))
    app.add_handler(MessageHandler(filters.Regex("^📞 Contacto$"), contacto))
    app.add_handler(CallbackQueryHandler(
        callback_carrito,
        pattern="^(quitar\\||vaciar_carrito|confirmar_pedido)"
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_desconocido))

    print("✅ El bot está encendido y escuchando mensajes...")
    app.run_polling()

if __name__ == "__main__":
    main()   
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversación: Registro de cliente
    conv_registro = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^👤 Registrarme$"), registrar)
        ],
        states={
            REG_NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_nombre)],
            REG_TELEFONO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_telefono)],
            REG_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_direccion)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Conversación: Agregar cantidad al carrito
    conv_cantidad = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_agregar, pattern="^agregar\\|")
        ],
        states={
            CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_cantidad)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Registrar handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_registro)
    app.add_handler(conv_cantidad)
    app.add_handler(MessageHandler(filters.Regex("^🛍️ Ver Productos$"), ver_productos))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Mi Carrito$"), ver_carrito))
    app.add_handler(MessageHandler(filters.Regex("^📋 Mis Pedidos$"), mis_pedidos))
    app.add_handler(MessageHandler(filters.Regex("^📞 Contacto$"), contacto))
    app.add_handler(CallbackQueryHandler(
        callback_carrito,
        pattern="^(quitar\\||vaciar_carrito|confirmar_pedido)"
    ))

    print("✅ El bot está encendido y escuchando mensajes...")
    app.run_polling()

if __name__ == "__main__":
    print("✅ El bot está encendido y escuchando mensajes...")
 
    main()
