#!/usr/bin/env python3
"""
neo.py — Punto de entrada único del agente NEO

Uso:
    python neo.py             → solo terminal (por defecto)
    python neo.py terminal    → solo terminal
    python neo.py telegram    → solo Telegram
    python neo.py ambos       → terminal + Telegram simultáneamente
"""

import asyncio
import logging
import os
import sys
import threading
from pathlib import Path

# ── Cargar .env solo si existe (la config principal va en start.sh) ────────
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES COMUNES
# ══════════════════════════════════════════════════════════════════════════════

def check_dependencies():
    """Verifica que las dependencias críticas estén instaladas."""
    missing = []
    for pkg in ["langchain", "langchain_core", "langgraph"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-"))

    provider = os.getenv("LLM_PROVIDER", "lmstudio")
    provider_pkg = {
        "lmstudio": "langchain_openai",
        "openai":   "langchain_openai",
        "anthropic": "langchain_anthropic",
        "google":   "langchain_google_genai",
    }.get(provider)
    if provider_pkg:
        try:
            __import__(provider_pkg)
        except ImportError:
            missing.append(provider_pkg.replace("_", "-"))

    if missing:
        print(f"\n❌ Faltan dependencias: {', '.join(missing)}")
        print("   Instálalas con: bash setup.sh\n")
        sys.exit(1)


def init_agent():
    """Carga e inicializa el agente. Muestra error claro si falla."""
    print("⏳ Inicializando NEO...")
    try:
        from core.agent import create_agent
        agent = create_agent()
        print("✅ Agente listo.\n")
        return agent
    except Exception as e:
        print(f"\n❌ Error al inicializar el agente: {e}")
        if os.getenv("AGENT_DEBUG", "false").lower() == "true":
            import traceback
            traceback.print_exc()
        print("\n💡 Comprueba que LM Studio está abierto con el servidor local activo.")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# MODO TERMINAL
# ══════════════════════════════════════════════════════════════════════════════

def run_terminal():
    check_dependencies()
    _print_banner()
    _terminal_loop()


def _terminal_loop(stop_event: threading.Event = None):
    """Bucle de conversación por terminal. Usado solo o en modo dual."""
    agent = init_agent()

    # Rich para output bonito (opcional)
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        def print_response(text):
            try:
                console.print(Markdown(text))
            except Exception:
                print(text)
    except ImportError:
        def print_response(text):
            print(text)

    from core.agent import save_session
    session_messages = []
    session_dir = ROOT / "memory" / "sessions"

    while True:
        # En modo dual, salir si Telegram ya se detuvo
        if stop_event and stop_event.is_set():
            break

        try:
            user_input = input("\n👤 Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 ¡Hasta luego!")
            save_session(session_messages, session_dir)
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("salir", "exit", "quit", "q"):
            print("\n👋 ¡Hasta luego!")
            save_session(session_messages, session_dir)
            if stop_event:
                stop_event.set()
            break

        if cmd == "ayuda":
            print(_help_text())
            continue

        if cmd == "config":
            print_response(_config_text())
            continue

        if cmd == "limpiar":
            os.system("clear" if os.name != "nt" else "cls")
            _print_banner()
            continue

        if cmd in ("nueva sesión", "nueva sesion", "reset"):
            save_session(session_messages, session_dir)
            agent = init_agent()
            session_messages = []
            print("🔄 Sesión reiniciada.\n")
            continue

        if cmd == "memoria":
            user_input = "lista todos mis recuerdos guardados en memoria"

        session_messages.append({"role": "user", "content": user_input})

        print("\n🤖 Neo: ", end="", flush=True)
        try:
            response = agent.invoke({"input": user_input})
            output = response.get("output", "")
            steps = response.get("intermediate_steps", [])
            if steps:
                tools_used = "\n".join(f"  🔧 {a.tool}" for a, _ in steps)
                output = f"{tools_used}\n\n{output}"
            print()
            print_response(output)
            session_messages.append({"role": "assistant", "content": output})

        except KeyboardInterrupt:
            print("\n[Respuesta interrumpida]")
        except Exception as e:
            msg = f"❌ Error: {e}"
            print(f"\n{msg}")
            if os.getenv("AGENT_DEBUG", "false").lower() == "true":
                import traceback
                traceback.print_exc()
            session_messages.append({"role": "error", "content": msg})


def _print_banner():
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        c = Console()
        title = Text("NEO", style="bold cyan", justify="center")
        sub = Text(
            "Agente de Ejecución Orgánica\n"
            "Powered by LangChain · Escribe 'ayuda' para ver comandos",
            style="dim", justify="center",
        )
        c.print(Panel(Text.assemble(title, "\n", sub), border_style="cyan", padding=(1, 4)))
    except ImportError:
        print("\n" + "═" * 50)
        print("  NEO — Agente de Ejecución Orgánica")
        print("  Escribe 'ayuda' para ver comandos")
        print("═" * 50 + "\n")


def _help_text():
    return """
╔═══════════════════════════════════════════╗
║           COMANDOS ESPECIALES             ║
╠═══════════════════════════════════════════╣
║  ayuda          → Muestra esta ayuda      ║
║  salir / exit   → Termina el agente       ║
║  limpiar        → Limpia la pantalla      ║
║  memoria        → Ver recuerdos guardados ║
║  nueva sesión   → Reinicia conversación   ║
║  config         → Ver configuración       ║
╚═══════════════════════════════════════════╝
También puedes pedir:
  "busca información sobre X"
  "lee el archivo X.txt"
  "ejecuta este código Python: ..."
  "¿cuánto es [expresión matemática]?"
"""


def _config_text():
    return (
        f"**Configuración actual:**\n"
        f"  - Proveedor : {os.getenv('LLM_PROVIDER', 'lmstudio')}\n"
        f"  - Modelo    : {os.getenv('LLM_MODEL', 'local-model')}\n"
        f"  - Servidor  : {os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')}\n"
        f"  - Workspace : {os.getenv('AGENT_WORKSPACE', str(ROOT / 'workspace'))}\n"
        f"  - Memoria   : {ROOT / 'memory'}\n"
        f"  - Verbose   : {os.getenv('AGENT_VERBOSE', 'false')}\n"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MODO TELEGRAM
# ══════════════════════════════════════════════════════════════════════════════

def run_telegram():
    check_dependencies()

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
        from telegram.constants import ChatAction, ParseMode
    except ImportError:
        print("\n❌ python-telegram-bot no está instalado.")
        print("   Instálalo con: pip install python-telegram-bot\n")
        sys.exit(1)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("\n❌ TELEGRAM_BOT_TOKEN está vacío.")
        print("   Edita start.sh y añade el token de @BotFather.\n")
        sys.exit(1)

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
    logger = logging.getLogger("neo.telegram")

    # Whitelist
    allowed_ids: set = set()
    raw = os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
    if raw:
        try:
            allowed_ids = {int(x.strip()) for x in raw.split(",") if x.strip()}
        except ValueError:
            logger.warning("TELEGRAM_ALLOWED_USERS mal formateado, ignorando whitelist")

    # Un agente y sesión por usuario
    user_agents: dict = {}
    user_sessions: dict = {}

    def get_agent(user_id: int):
        if user_id not in user_agents:
            logger.info(f"Creando agente para usuario {user_id}")
            from core.agent import create_agent
            user_agents[user_id] = create_agent()
            user_sessions[user_id] = []
        return user_agents[user_id]

    # ── Handlers ──────────────────────────────────────────────────────────────

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = update.effective_user.first_name or "usuario"
        await update.message.reply_text(
            f"👋 Hola <b>{name}</b>, soy <b>NEO</b> — tu agente de IA local.\n\n"
            "Puedo buscar en internet, leer y escribir archivos, ejecutar código, "
            "consultar APIs y recordar cosas entre sesiones.\n\n"
            "<b>Comandos:</b>\n"
            "/ayuda — Qué puedo hacer\n"
            "/memoria — Ver recuerdos\n"
            "/estado — Estado del sistema\n"
            "/reset — Nueva conversación\n\n"
            "Escríbeme lo que necesitas 🚀",
            parse_mode=ParseMode.HTML,
        )

    async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        user_agents.pop(uid, None)
        user_sessions[uid] = []
        await update.message.reply_text(
            "🔄 Conversación reiniciada. Los recuerdos a largo plazo se mantienen."
        )

    async def cmd_memoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.chat.send_action(ChatAction.TYPING)
        agent = get_agent(update.effective_user.id)
        try:
            result = agent.invoke({"input": "lista todos mis recuerdos guardados en memoria"})
            text = _md_to_html(result.get("output", "No hay recuerdos guardados."))
            await _send_long(update, text, ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        await update.message.reply_text(
            f"<b>🤖 Estado de NEO</b>\n\n"
            f"<b>Proveedor:</b> <code>{os.getenv('LLM_PROVIDER', 'lmstudio')}</code>\n"
            f"<b>Modelo:</b> <code>{os.getenv('LLM_MODEL', 'local-model')}</code>\n"
            f"<b>Servidor:</b> <code>{os.getenv('LMSTUDIO_BASE_URL', 'http://localhost:1234/v1')}</code>\n"
            f"<b>Agente activo:</b> {'✅' if uid in user_agents else '❌'}\n"
            f"<b>Mensajes en sesión:</b> {len(user_sessions.get(uid, []))}\n"
            f"<b>Usuarios activos:</b> {len(user_agents)}",
            parse_mode=ParseMode.HTML,
        )

    async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "<b>🛠️ Qué puede hacer NEO</b>\n\n"
            "<b>Búsqueda web:</b> «busca noticias sobre Python 3.14»\n"
            "<b>Archivos:</b> «lee config.json» / «guarda esto en notas.txt»\n"
            "<b>Cálculos:</b> «¿cuánto es el 21% IVA sobre 3.450€?»\n"
            "<b>Código:</b> «ejecuta: print([x**2 for x in range(10)])»\n"
            "<b>APIs:</b> «consulta wttr.in para Madrid»\n"
            "<b>Memoria:</b> «recuerda que uso Python 3.12»",
            parse_mode=ParseMode.HTML,
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id

        if allowed_ids and uid not in allowed_ids:
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        user_input = update.message.text.strip()
        if not user_input:
            return

        await update.message.chat.send_action(ChatAction.TYPING)
        agent = get_agent(uid)
        user_sessions[uid].append({"role": "user", "content": user_input})

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: agent.invoke({"input": user_input})
            )
            output = result.get("output", "Sin respuesta.")
            steps = result.get("intermediate_steps", [])
            header = ""
            if steps:
                tools_used = ", ".join(a.tool for a, _ in steps)
                header = f"<i>🔧 {tools_used}</i>\n\n"

            await _send_long(update, header + _md_to_html(output), ParseMode.HTML)
            user_sessions[uid].append({"role": "assistant", "content": output})

        except Exception as e:
            logger.error(f"Error usuario {uid}: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ <b>Error:</b> <code>{str(e)[:400]}</code>\n\n"
                "¿Está LM Studio activo con el servidor local encendido?",
                parse_mode=ParseMode.HTML,
            )

    # ── Arrancar bot ──────────────────────────────────────────────────────────

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("reset",   cmd_reset))
    app.add_handler(CommandHandler("memoria", cmd_memoria))
    app.add_handler(CommandHandler("estado",  cmd_estado))
    app.add_handler(CommandHandler("ayuda",   cmd_ayuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info(f"🤖 NEO Telegram Bot activo · modelo: {os.getenv('LLM_MODEL', 'local-model')}")
    if allowed_ids:
        logger.info(f"   Whitelist: {allowed_ids}")
    print("\n✅ NEO Bot activo en Telegram. Ctrl+C para detener.\n")

    return app


def _telegram_run(stop_event: threading.Event = None):
    """Construye y arranca el bot de Telegram en el hilo actual (debe ser el principal)."""
    try:
        from telegram import Update as TelegramUpdate
    except ImportError:
        print("\n❌ python-telegram-bot no está instalado. Ejecuta: pip install python-telegram-bot\n")
        return
    app = run_telegram()
    if app is None:
        return
    app.run_polling(allowed_updates=TelegramUpdate.ALL_TYPES)


# ── Helpers Telegram ──────────────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """Convierte Markdown básico a HTML para Telegram."""
    import re
    text = re.sub(r"```(?:\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{_esc(m.group(1).strip())}</code></pre>",
        text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{_esc(m.group(1))}</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"^#{1,3}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"^---+$", "─────────────", text, flags=re.MULTILINE)
    return text.strip()


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def _send_long(update, text: str, parse_mode: str):
    MAX = 4096
    while text:
        if len(text) <= MAX:
            await update.message.reply_text(text, parse_mode=parse_mode)
            break
        cut = text.rfind("\n", 0, MAX)
        if cut == -1:
            cut = MAX
        await update.message.reply_text(text[:cut], parse_mode=parse_mode)
        text = text[cut:].lstrip()


# ══════════════════════════════════════════════════════════════════════════════
# MODO AMBOS — terminal + Telegram simultáneamente
# ══════════════════════════════════════════════════════════════════════════════

def run_ambos():
    """
    Telegram necesita correr en el hilo principal (por las señales del sistema).
    El terminal corre en un hilo secundario leyendo stdin.
    Ambos comparten la memoria a largo plazo en disco.
    Ctrl+C detiene todo.
    """
    check_dependencies()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("\n⚠️  TELEGRAM_BOT_TOKEN vacío — arrancando solo en modo terminal.\n")
        run_terminal()
        return

    print("🚀 Arrancando NEO en modo dual (terminal + Telegram)...")
    print("   Ctrl+C para detener ambos.\n")

    stop_event = threading.Event()

    def terminal_thread():
        """Hilo secundario: bucle de terminal."""
        try:
            _terminal_loop(stop_event)
        except Exception as e:
            if not stop_event.is_set():
                print(f"\n⚠️  Terminal se detuvo: {e}")
        finally:
            stop_event.set()

    t = threading.Thread(target=terminal_thread, daemon=True, name="neo-terminal")
    t.start()

    # Telegram en el hilo principal (necesario para set_wakeup_fd / señales)
    try:
        _telegram_run(stop_event)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        stop_event.set()
        print("\n🛑 Deteniendo NEO...")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "terminal"

    if mode in ("terminal", "consola"):
        run_terminal()
    elif mode == "telegram":
        _telegram_run()
    elif mode in ("ambos", "both", "dual"):
        run_ambos()
    else:
        print(f"\n❌ Modo desconocido: '{mode}'")
        print("   Uso: python neo.py [terminal|telegram|ambos]\n")
        sys.exit(1)
