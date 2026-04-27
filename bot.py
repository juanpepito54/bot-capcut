from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3
from datetime import datetime, timedelta

TOKEN = "8617315953:AAEkSUwUrcGG4uXY0BtKe30KIa44BNXqJLw"
ADMIN_ID = 6059358910

DB = "bot_capcut.db"
PRECIO_CAPCUT = 1.40


def conectar():
    return sqlite3.connect(DB)


def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tg_usuarios (
        telegram_id INTEGER PRIMARY KEY,
        nombre TEXT,
        username TEXT,
        saldo REAL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tg_cuentas_capcut (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        contrasena TEXT,
        url TEXT,
        estado TEXT DEFAULT 'disponible'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tg_compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        producto TEXT,
        precio REAL,
        fecha TEXT,
        vence TEXT,
        usuario_entregado TEXT
    )
    """)

    conn.commit()
    conn.close()


def menu_principal():
    botones = [
        [InlineKeyboardButton("🛒 Tienda", callback_data="tienda"), InlineKeyboardButton("📜 Reglas", callback_data="reglas")],
        [InlineKeyboardButton("👤 Perfil", callback_data="perfil"), InlineKeyboardButton("🆘 Soporte", callback_data="soporte")],
        [InlineKeyboardButton("💰 Recargar saldo", callback_data="recargar")]
    ]
    return InlineKeyboardMarkup(botones)


def menu_abajo():
    teclado = [
        ["🏠 Menú", "🛒 Tienda"],
        ["👤 Perfil", "💰 Recargar"],
        ["📜 Reglas", "🆘 Soporte"]
    ]
    return ReplyKeyboardMarkup(teclado, resize_keyboard=True)


async def registrar_usuario(user):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO tg_usuarios (telegram_id, nombre, username, saldo)
        VALUES (?, ?, ?, 0)
    """, (user.id, user.first_name, user.username))
    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await registrar_usuario(user)

    await update.message.reply_text(
        f"🎪 Bienvenido a Dxy Bot\n\nHola {user.first_name} 👋\nUsa los botones de abajo o el menú principal.",
        reply_markup=menu_abajo()
    )

    await update.message.reply_text(
        "🎪 Menú principal\n\nSelecciona una opción:",
        reply_markup=menu_principal()
    )


async def mostrar_perfil(user):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT saldo FROM tg_usuarios WHERE telegram_id = ?", (user.id,))
    resultado = cursor.fetchone()
    conn.close()

    saldo = resultado[0] if resultado else 0

    return (
        f"👤 Perfil\n\n"
        f"Nombre: {user.first_name}\n"
        f"ID: {user.id}\n"
        f"Saldo: ${saldo:.2f}"
    )


async def mostrar_tienda():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tg_cuentas_capcut WHERE estado = 'disponible'")
    stock = cursor.fetchone()[0]
    conn.close()

    texto = (
        f"🛒 Tienda\n\n"
        f"📦 Producto disponible:\n\n"
        f"🎬 CapCut Pro 30 días\n"
        f"💵 Precio: ${PRECIO_CAPCUT:.2f}\n"
        f"📊 Stock: {stock} disponibles\n\n"
        f"👇 Presiona comprar:"
    )

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Comprar CapCut Pro - ${PRECIO_CAPCUT:.2f}", callback_data="comprar_capcut")],
        [InlineKeyboardButton("⬅️ Volver", callback_data="menu")]
    ])

    return texto, teclado


async def mostrar_recarga():
    return (
        f"💰 Recargar saldo\n\n"
        f"Saldo en dólares USD.\n\n"
        f"⭐ Método recomendado: Binance Pay USDT\n\n"
        f"🟡 Datos de pago:\n"
        f"Binance Pay ID: 12036671731\n"
        f"Moneda: USDT\n\n"
        f"⚠️ IMPORTANTE:\n"
        f"• Envía solo USDT.\n"
        f"• No envíes otra moneda.\n"
        f"• Verifica bien el monto antes de enviar.\n\n"
        f"📩 Después de pagar, envía el ID de la transacción así:\n\n"
        f"/txid MONTO CODIGO\n\n"
        f"Ejemplo:\n"
        f"/txid 1.40 ABC123456\n\n"
        f"✅ Tu recarga será revisada por el administrador."
    )


async def mostrar_reglas():
    return (
        f"📜 Reglas y condiciones\n\n"
        f"1. El producto es CapCut Pro por 30 días.\n"
        f"2. No cambiar correo, contraseña ni datos de la cuenta.\n"
        f"3. La garantía aplica solo por problemas de acceso.\n"
        f"4. No se cubren bloqueos por mal uso del cliente.\n"
        f"5. Una vez entregado el acceso, no hay devolución si el producto funciona correctamente.\n"
        f"6. Si tienes problemas, contacta soporte."
    )


async def mostrar_soporte():
    return (
        f"🆘 Soporte\n\n"
        f"Escribe por este mismo chat y un administrador te responderá.\n\n"
        f"Indica:\n"
        f"• Tu problema\n"
        f"• Captura del error\n"
        f"• Producto comprado"
    )


async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data
    await registrar_usuario(user)

    if data == "menu":
        await query.edit_message_text(
            "🎪 Menú principal\n\nSelecciona una opción:",
            reply_markup=menu_principal()
        )

    elif data == "perfil":
        texto = await mostrar_perfil(user)
        await query.edit_message_text(
            texto,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )

    elif data == "tienda":
        texto, teclado = await mostrar_tienda()
        await query.edit_message_text(texto, reply_markup=teclado)

    elif data == "recargar":
        texto = await mostrar_recarga()
        await query.edit_message_text(
            texto,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )

    elif data == "reglas":
        texto = await mostrar_reglas()
        await query.edit_message_text(
            texto,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )

    elif data == "soporte":
        texto = await mostrar_soporte()
        await query.edit_message_text(
            texto,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )

    elif data == "comprar_capcut":
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT saldo FROM tg_usuarios WHERE telegram_id = ?", (user.id,))
        resultado = cursor.fetchone()
        saldo = resultado[0] if resultado else 0

        if saldo < PRECIO_CAPCUT:
            conn.close()
            await query.edit_message_text(
                f"❌ Saldo insuficiente\n\n"
                f"Tu saldo actual es: ${saldo:.2f}\n"
                f"Precio del producto: ${PRECIO_CAPCUT:.2f}\n\n"
                f"Recarga saldo para poder comprar.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Recargar saldo", callback_data="recargar")],
                    [InlineKeyboardButton("⬅️ Volver", callback_data="menu")]
                ])
            )
            return

        cursor.execute("SELECT id, usuario, contrasena, url FROM tg_cuentas_capcut WHERE estado = 'disponible' LIMIT 1")
        cuenta = cursor.fetchone()

        if not cuenta:
            conn.close()
            await query.edit_message_text(
                "❌ No hay stock disponible por el momento.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
            )
            return

        cuenta_id, usuario_cuenta, contrasena, url = cuenta
        nuevo_saldo = saldo - PRECIO_CAPCUT
        fecha = datetime.now()
        vence = fecha + timedelta(days=30)

        cursor.execute("UPDATE tg_usuarios SET saldo = ? WHERE telegram_id = ?", (nuevo_saldo, user.id))
        cursor.execute("UPDATE tg_cuentas_capcut SET estado = 'vendido' WHERE id = ?", (cuenta_id,))
        cursor.execute("""
            INSERT INTO tg_compras (telegram_id, producto, precio, fecha, vence, usuario_entregado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user.id, "CapCut Pro 30 días", PRECIO_CAPCUT, str(fecha), str(vence), usuario_cuenta))

        conn.commit()
        conn.close()

        await query.edit_message_text(
            f"✅ Compra exitosa\n\n"
            f"🛒 Producto: CapCut Pro\n"
            f"💵 Precio: ${PRECIO_CAPCUT:.2f}\n"
            f"📅 Duración: 30 días\n"
            f"🕒 Vence: {vence.strftime('%Y-%m-%d')}\n"
            f"💰 Nuevo saldo: ${nuevo_saldo:.2f}\n\n"
            f"🔐 DATOS DE ACCESO\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📧 Usuario: {usuario_cuenta}\n"
            f"🔑 Contraseña: {contrasena}\n"
            f"🌐 Acceso: {url}\n\n"
            f"⚠️ IMPORTANTE:\n"
            f"• No cambies los datos de la cuenta\n"
            f"• Uso personal\n"
            f"• Garantía solo por problemas de acceso\n"
            f"━━━━━━━━━━━━━━━"
        )


async def menu_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await registrar_usuario(user)

    texto = update.message.text.strip().lower()

    if "menú" in texto or "menu" in texto:
        await update.message.reply_text(
            "🎪 Menú principal\n\nSelecciona una opción:",
            reply_markup=menu_principal()
        )

    elif "tienda" in texto:
        texto_tienda, teclado = await mostrar_tienda()
        await update.message.reply_text(texto_tienda, reply_markup=teclado)

    elif "perfil" in texto:
        perfil = await mostrar_perfil(user)
        await update.message.reply_text(perfil)

    elif "recargar" in texto:
        recarga = await mostrar_recarga()
        await update.message.reply_text(
            recarga,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )

    elif "reglas" in texto:
        reglas = await mostrar_reglas()
        await update.message.reply_text(
            reglas,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )

    elif "soporte" in texto:
        soporte = await mostrar_soporte()
        await update.message.reply_text(
            soporte,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Volver", callback_data="menu")]])
        )


async def id_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Tu ID es: {update.effective_user.id}")


async def agregar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        telegram_id = int(context.args[0])
        monto = float(context.args[1])

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT saldo FROM tg_usuarios WHERE telegram_id = ?", (telegram_id,))
        resultado = cursor.fetchone()

        if not resultado:
            conn.close()
            await update.message.reply_text("❌ Ese usuario aún no está registrado en el bot.")
            return

        saldo_anterior = resultado[0]
        nuevo_saldo = saldo_anterior + monto

        cursor.execute("UPDATE tg_usuarios SET saldo = ? WHERE telegram_id = ?", (nuevo_saldo, telegram_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ Recarga aprobada\n\n"
            f"Usuario ID: {telegram_id}\n"
            f"Monto agregado: ${monto:.2f}\n"
            f"Nuevo saldo: ${nuevo_saldo:.2f}"
        )

        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"✅ Tu recarga fue aprobada\n\n"
                f"💰 Monto recargado: ${monto:.2f}\n"
                f"💵 Ahora tienes saldo: ${nuevo_saldo:.2f}\n\n"
                f"Ya puedes comprar en la tienda 🛒"
            )
        )

    except:
        await update.message.reply_text(
            "Uso correcto:\n/saldo ID MONTO\n\nEjemplo:\n/saldo 123456789 1.40"
        )


async def agregar_capcut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    texto = " ".join(context.args)

    try:
        usuario, contrasena, url = texto.split("|")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tg_cuentas_capcut (usuario, contrasena, url, estado)
            VALUES (?, ?, ?, 'disponible')
        """, (usuario.strip(), contrasena.strip(), url.strip()))
        conn.commit()
        conn.close()

        await update.message.reply_text("✅ Cuenta CapCut agregada al stock.")
    except:
        await update.message.reply_text(
            "Uso correcto:\n"
            "/addcapcut usuario|contraseña|url\n\n"
            "Ejemplo:\n"
            "/addcapcut prueba@gmail.com|pass1234|https://www.capcut.com"
        )


async def registrar_txid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await registrar_usuario(user)

    try:
        monto = float(context.args[0])
        txid = " ".join(context.args[1:]).strip()

        if not txid:
            await update.message.reply_text(
                "Uso correcto:\n/txid MONTO CODIGO\n\nEjemplo:\n/txid 1.40 ABC123456"
            )
            return

        await update.message.reply_text(
            "✅ ID de transacción recibido.\n\n"
            "Tu recarga será revisada por el administrador."
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 NUEVA RECARGA PENDIENTE\n\n"
                f"👤 Usuario: {user.first_name}\n"
                f"🆔 ID Telegram: {user.id}\n"
                f"💰 Monto indicado: ${monto:.2f}\n"
                f"💳 ID de transacción: {txid}\n\n"
                f"Cuando verifiques el pago, aprueba con:\n"
                f"/saldo {user.id} {monto:.2f}"
            )
        )

    except:
        await update.message.reply_text(
            "Uso correcto:\n/txid MONTO CODIGO\n\nEjemplo:\n/txid 1.40 ABC123456"
        )


crear_tablas()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", id_usuario))
app.add_handler(CommandHandler("saldo", agregar_saldo))
app.add_handler(CommandHandler("addcapcut", agregar_capcut))
app.add_handler(CommandHandler("txid", registrar_txid))
app.add_handler(CallbackQueryHandler(botones))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_texto))

print("✅ Dxy Bot encendido...")
app.run_polling()