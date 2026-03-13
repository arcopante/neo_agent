#!/usr/bin/env python3
"""
telegram_bot.py — Interfaz Telegram para el agente NEO

Arranca un bot de Telegram que conecta con el mismo agente y memoria
que main.py. Cada usuario de Telegram tiene su propia instancia del agente
con memoria de conversación independiente.

Uso:
    python telegram_bot.py

Requisitos:
    - TELEGRAM_BOT_TOKEN en .env
    - pip install python-telegram-bot
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Cargar .env
try:
    from dotenv import load_dotenv
    from pathlib import Path as _Path
    _env = _Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("neo.telegram")

# ── Verificar dependencias ─────────────────────────────────────────────────

try:
    from telegram import Update, BotCommand
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    )
    from telegram.constants import ChatAction, ParseMode
except ImportError:
    print("\n❌ python-telegram-bot no está instalado.")
    print("   Instálalo con: pip install python-telegram-bot\n")
    sys.exit(1)

# ── Estado global: un agente por usuario ──────────────────────────────────

user_agents: dict = {}  # { user_id: AgentExecutor }
user_sessions: dict = {}  # { user_id: [messages] }


def get_or_create_agent(user_id: int):
    """Devuelve el agente del usuario o crea uno nuevo."""
    if user_id not in user_agents:
        logger.info(f"Creando agente para usuario {user_id}")
        from core.agent import create_agent
        user_agents[user_id] = create_agent()
        user_sessions[user_id] = []
    return user_agents[user_id]


# ── Helpers de formato ─────────────────────────────────────────────────────

def format_for_telegram(text: str) -> str:
    """
    Convierte Markdown del agente a formato compatible con Telegram.
    Telegram soporta un subconjunto de Markdown (MarkdownV2).
    Usamos HTML que es más predecible.
    """
    import re

    # Convertir bloques de código ```lang\n...\n``` → <pre><code>
    text = re.sub(
        r"```(?:\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{_escape_html(m.group(1).strip())}</code></pre>",
        text,
        flags=re.DOTALL,
    )
    # Código inline `...` → <code>
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{_escape_html(m.group(1))}</code>", text)
    # **negrita** → <b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # *cursiva* → <i>
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # ### Encabezados → <b>
    text = re.sub(r"^#{1,3}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    # Líneas horizontales
    text = re.sub(r"^---+$", "─────────────", text, flags=re.MULTILINE)

    return text.strip()


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def send_long_message(update: Update, text: str, parse_mode: str = ParseMode.HTML):
    """Envía mensajes largos partiéndolos en chunks de 4096 chars."""
    MAX = 4096
    if len(text) <= MAX:
        await update.message.reply_text(text, parse_mode=parse_mode)
        return

    chunks = []
    while text:
        if len(text) <= MAX:
            chunks.append(text)
            break
        # Partir en salto de línea más cercano al límite
        split_at = text.rfind("\n", 0, MAX)
        if split_at == -1:
            split_at = MAX
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode=parse_mode)


# ── Handlers de Telegram ───────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start"""
    user = update.effective_user
    name = user.first_name or "usuario"

    welcome = (
        f"👋 Hola <b>{name}</b>, soy <b>NEO</b> — tu agente de IA local.\n\n"
        "Puedo buscar en internet, leer y escribir archivos, ejecutar código, "
        "consultar APIs y recordar cosas entre sesiones.\n\n"
        "<b>Comandos disponibles:</b>\n"
        "/start — Este mensaje\n"
        "/reset — Reiniciar conversación\n"
        "/memoria — Ver mis recuerdos sobre ti\n"
        "/estado — Estado del agente\n"
        "/ayuda — Ayuda detallada\n\n"
        "Escríbeme lo que necesitas en lenguaje natural 🚀"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.HTML)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /reset — reinicia la conversación del usuario."""
    user_id = update.effective_user.id
    if user_id in user_agents:
        del user_agents[user_id]
        user_sessions[user_id] = []
    await update.message.reply_text(
        "🔄 Conversación reiniciada. ¡Empezamos de cero! "
        "(Los recuerdos a largo plazo se mantienen)"
    )


async def cmd_salir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /salir — apaga el bot. Solo para usuarios autorizados."""
    await update.message.reply_text("🛑 Apagando NEO... hasta pronto.")
    logger.info(f"Apagado solicitado por usuario {update.effective_user.id}")
    # Detener el bot limpiamente desde dentro del loop
    asyncio.get_event_loop().call_later(1, context.application.stop)


async def cmd_memoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /memoria — muestra los recuerdos del agente."""
    await update.message.chat.send_action(ChatAction.TYPING)
    agent = get_or_create_agent(update.effective_user.id)
    try:
        result = agent.invoke({"input": "lista todos mis recuerdos guardados en memoria"})
        text = format_for_telegram(result.get("output", "No hay recuerdos guardados."))
        await send_long_message(update, text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /estado — muestra estado del agente."""
    user_id = update.effective_user.id
    tiene_agente = user_id in user_agents
    n_mensajes = len(user_sessions.get(user_id, []))
    provider = os.getenv("LLM_PROVIDER", "lmstudio")
    model = os.getenv("LLM_MODEL", "local-model")
    base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")

    status = (
        f"<b>🤖 Estado de NEO</b>\n\n"
        f"<b>Proveedor:</b> <code>{provider}</code>\n"
        f"<b>Modelo:</b> <code>{model}</code>\n"
        f"<b>Servidor:</b> <code>{base_url}</code>\n"
        f"<b>Agente activo:</b> {'✅' if tiene_agente else '❌ (se crea al primer mensaje)'}\n"
        f"<b>Mensajes en sesión:</b> {n_mensajes}\n"
        f"<b>Usuarios activos:</b> {len(user_agents)}"
    )
    await update.message.reply_text(status, parse_mode=ParseMode.HTML)


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /ayuda"""
    ayuda = (
        "<b>🛠️ Qué puede hacer NEO</b>\n\n"
        "<b>Búsqueda web:</b>\n"
        "  «busca las últimas noticias sobre Python 3.14»\n\n"
        "<b>Archivos:</b>\n"
        "  «lee el archivo config.json»\n"
        "  «guarda esto en un archivo llamado notas.txt»\n\n"
        "<b>Cálculos:</b>\n"
        "  «¿cuánto es el 21% de IVA sobre 3.450€?»\n\n"
        "<b>Código Python:</b>\n"
        "  «ejecuta: print([x**2 for x in range(10)])»\n\n"
        "<b>APIs:</b>\n"
        "  «consulta wttr.in y dime el tiempo en Madrid»\n\n"
        "<b>Memoria:</b>\n"
        "  «recuerda que trabajo con Python 3.12»\n"
        "  «¿qué recuerdas de mis preferencias?»\n\n"
        "<b>Comandos:</b>\n"
        "  /reset — Nueva conversación\n"
        "  /memoria — Ver recuerdos\n"
        "  /estado — Estado del sistema"
    )
    await update.message.reply_text(ayuda, parse_mode=ParseMode.HTML)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal — procesa mensajes de texto."""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    if not user_input:
        return

    # Mostrar "escribiendo..." mientras el agente procesa
    await update.message.chat.send_action(ChatAction.TYPING)

    # Obtener o crear agente para este usuario
    agent = get_or_create_agent(user_id)

    # Registrar mensaje
    user_sessions[user_id].append({"role": "user", "content": user_input})

    try:
        # Invocar al agente (puede tardar varios segundos con modelos locales)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: agent.invoke({"input": user_input})
        )

        output = result.get("output", "No obtuve respuesta del agente.")

        # Mostrar herramientas usadas si hay pasos intermedios
        steps = result.get("intermediate_steps", [])
        tool_header = ""
        if steps:
            tools_used = [action.tool for action, _ in steps]
            tool_header = f"<i>🔧 Usé: {', '.join(tools_used)}</i>\n\n"

        formatted = format_for_telegram(output)
        full_response = tool_header + formatted

        await send_long_message(update, full_response)

        # Registrar respuesta
        user_sessions[user_id].append({"role": "assistant", "content": output})

    except Exception as e:
        logger.error(f"Error procesando mensaje de {user_id}: {e}", exc_info=True)
        error_msg = (
            f"❌ <b>Error del agente:</b>\n<code>{str(e)[:500]}</code>\n\n"
            "Revisa que la API key y el modelo en config/settings.cfg son correctos."
        )
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)


# ── Punto de entrada ───────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("\n❌ TELEGRAM_BOT_TOKEN no está definido en .env")
        print("   1. Habla con @BotFather en Telegram")
        print("   2. Crea un bot con /newbot")
        print("   3. Copia el token en tu .env\n")
        sys.exit(1)

    # Whitelist de usuarios (opcional)
    allowed_raw = os.getenv("TELEGRAM_ALLOWED_USERS", "")
    allowed_ids = set()
    if allowed_raw.strip():
        try:
            allowed_ids = {int(x.strip()) for x in allowed_raw.split(",") if x.strip()}
            logger.info(f"Whitelist activa: {allowed_ids}")
        except ValueError:
            logger.warning("TELEGRAM_ALLOWED_USERS mal formateado, ignorando whitelist")

    # Si hay whitelist, envolver los handlers
    if allowed_ids:
        original_salir = cmd_salir

        async def guarded_salir(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in allowed_ids:
                await update.message.reply_text("⛔ No tienes acceso a este bot.")
                return
            await original_salir(update, context)

        cmd_salir = guarded_salir
        original_handle = handle_message

        async def guarded_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in allowed_ids:
                await update.message.reply_text("⛔ No tienes acceso a este bot.")
                logger.warning(f"Acceso denegado a usuario {update.effective_user.id}")
                return
            await original_handle(update, context)

        message_handler = guarded_handle
    else:
        message_handler = handle_message

    # Construir la aplicación
    app = Application.builder().token(token).build()

    # Registrar handlers
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("reset",   cmd_reset))
    app.add_handler(CommandHandler("memoria", cmd_memoria))
    app.add_handler(CommandHandler("estado",  cmd_estado))
    app.add_handler(CommandHandler("ayuda",   cmd_ayuda))
    app.add_handler(CommandHandler("salir",  cmd_salir))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Sincronizar el menú "/" de Telegram con los comandos reales del bot
    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start",   "Bienvenida"),
            BotCommand("ayuda",   "Qué puede hacer NEO"),
            BotCommand("memoria", "Ver recuerdos guardados"),
            BotCommand("estado",  "Estado del agente y modelo activo"),
            BotCommand("reset",   "Reiniciar conversación"),
            BotCommand("salir",   "Apagar el agente"),
        ])

    app.post_init = post_init

    logger.info("🤖 NEO Bot arrancando...")
    logger.info(f"   LLM: {os.getenv('LLM_PROVIDER', '?')} / {os.getenv('LLM_MODEL', '?')}")
    if allowed_ids:
        logger.info(f"   Whitelist: {allowed_ids}")
    else:
        logger.info("   Whitelist: desactivada (bot público)")

    print("\n✅ NEO Bot activo. Ctrl+C para detener.\n")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
