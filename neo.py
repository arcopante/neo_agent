#!/usr/bin/env python3
"""
neo.py — Punto de entrada único del agente NEO

Uso:
    python neo.py             → terminal (por defecto)
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

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Silenciar logs y warnings innecesarios ────────────────────────────────────
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

import warnings
warnings.filterwarnings("ignore", message="resource_tracker")
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES COMUNES
# ══════════════════════════════════════════════════════════════════════════════

def check_dependencies():
    missing = []
    for pkg in ["langchain", "langchain_core", "langgraph"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-"))

    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
    provider_pkg = {
        "openrouter": "langchain_openai",
        "lmstudio":   "langchain_openai",
        "openai":     "langchain_openai",
        "anthropic":  "langchain_anthropic",
        "google":     "langchain_google_genai",
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
        print("\n💡 Revisa tu API key y el modelo en config/settings.cfg")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# MODO TERMINAL
# ══════════════════════════════════════════════════════════════════════════════

def run_terminal():
    check_dependencies()
    _print_banner()
    _terminal_loop()


def _terminal_loop(stop_event: threading.Event = None):
    agent = init_agent()

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

    # Hilo vigilante: si stop_event se activa mientras input() está bloqueado,
    # os._exit() mata el proceso completo sin esperar nada
    if stop_event:
        import threading as _threading
        def _watchdog():
            stop_event.wait()
            print("\n🛑 Telegram detenido. Cerrando terminal...")
            save_session(session_messages, session_dir)
            os._exit(0)
        _threading.Thread(target=_watchdog, daemon=True, name="neo-watchdog").start()

    while True:
        try:
            user_input = input("\n👤 Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 ¡Hasta luego!")
            save_session(session_messages, session_dir)
            os._exit(0)

        if not user_input:
            continue

        # Aceptar comandos con o sin barra inicial
        cmd = user_input.lstrip("/").lower()

        if cmd in ("salir", "exit", "quit", "q"):
            print("\n👋 ¡Hasta luego!")
            save_session(session_messages, session_dir)
            if stop_event:
                stop_event.set()
            os._exit(0)

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
            "Agente de IA personal\n"
            "Escribe /ayuda para ver comandos",
            style="dim", justify="center",
        )
        c.print(Panel(Text.assemble(title, "\n", sub), border_style="cyan", padding=(1, 4)))
    except ImportError:
        print("\n" + "═" * 50)
        print("  NEO — Agente de IA personal")
        print("  Escribe /ayuda para ver comandos")
        print("═" * 50 + "\n")


def _help_text():
    return """
╔═══════════════════════════════════════════╗
║           COMANDOS ESPECIALES             ║
╠═══════════════════════════════════════════╣
║  /ayuda         → Muestra esta ayuda      ║
║  /salir         → Termina el agente       ║
║  /limpiar       → Limpia la pantalla      ║
║  /memoria       → Ver recuerdos guardados ║
║  /reset         → Reinicia conversación   ║
║  /config        → Ver configuración       ║
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
        f"  - Proveedor : {os.getenv('LLM_PROVIDER', '?')}\n"
        f"  - Modelo    : {os.getenv('LLM_MODEL', '?')}\n"
        f"  - Workspace : {os.getenv('AGENT_WORKSPACE', str(ROOT / 'workspace'))}\n"
        f"  - Memoria   : {ROOT / 'memory'}\n"
        f"  - Verbose   : {os.getenv('AGENT_VERBOSE', 'false')}\n"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MODO TELEGRAM
# ══════════════════════════════════════════════════════════════════════════════

def run_telegram(stop_event: threading.Event = None):
    check_dependencies()

    try:
        from telegram import Update, BotCommand
        from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
        from telegram.constants import ChatAction, ParseMode
    except ImportError:
        print("\n❌ python-telegram-bot no está instalado.")
        print("   Instálalo con: pip install python-telegram-bot\n")
        sys.exit(1)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("\n❌ TELEGRAM_BOT_TOKEN está vacío.")
        print("   Edita config/settings.cfg y añade el token de @BotFather.\n")
        sys.exit(1)

    logger = logging.getLogger("neo.telegram")

    # Whitelist
    allowed_ids: set = set()
    raw = os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
    if raw:
        try:
            allowed_ids = {int(x.strip()) for x in raw.split(",") if x.strip()}
        except ValueError:
            logger.warning("TELEGRAM_ALLOWED_USERS mal formateado, ignorando whitelist")

    user_agents: dict = {}
    user_sessions: dict = {}

    async def get_agent(user_id: int):
        if user_id not in user_agents:
            from core.agent import create_agent
            # Ejecutar create_agent en un hilo para no bloquear el event loop
            # (probe_tool_calling hace peticiones HTTP síncronas)
            user_agents[user_id] = await asyncio.get_event_loop().run_in_executor(
                None, create_agent
            )
            user_sessions[user_id] = []
        return user_agents[user_id]

    def is_allowed(user_id: int) -> bool:
        return not allowed_ids or user_id in allowed_ids

    # ── Handlers ──────────────────────────────────────────────────────────────

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return
        name = update.effective_user.first_name or "usuario"
        await update.message.reply_text(
            f"👋 Hola <b>{name}</b>, soy <b>NEO</b> — tu agente de IA personal.\n\n"
            "Puedo buscar en internet, leer y escribir archivos, ejecutar código, "
            "consultar APIs y recordar cosas entre sesiones.\n\n"
            "<b>Comandos:</b>\n"
            "/ayuda — Qué puedo hacer\n"
            "/memoria — Ver recuerdos\n"
            "/estado — Estado del sistema\n"
            "/reset — Nueva conversación\n"
            "/salir — Apagar el agente\n\n"
            "Escríbeme lo que necesitas 🚀",
            parse_mode=ParseMode.HTML,
        )

    async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return
        uid = update.effective_user.id
        user_agents.pop(uid, None)
        user_sessions[uid] = []
        await update.message.reply_text(
            "🔄 Conversación reiniciada. Los recuerdos a largo plazo se mantienen."
        )

    async def cmd_memoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return
        await update.message.chat.send_action(ChatAction.TYPING)
        agent = await get_agent(update.effective_user.id)
        try:
            result = agent.invoke({"input": "lista todos mis recuerdos guardados en memoria"})
            text = _md_to_html(result.get("output", "No hay recuerdos guardados."))
            await _send_long(update, text, ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return
        uid = update.effective_user.id
        await update.message.reply_text(
            f"<b>🤖 Estado de NEO</b>\n\n"
            f"<b>Proveedor:</b> <code>{os.getenv('LLM_PROVIDER', '?')}</code>\n"
            f"<b>Modelo:</b> <code>{os.getenv('LLM_MODEL', '?')}</code>\n"
            f"<b>Agente activo:</b> {'✅' if uid in user_agents else '❌'}\n"
            f"<b>Mensajes en sesión:</b> {len(user_sessions.get(uid, []))}\n"
            f"<b>Usuarios activos:</b> {len(user_agents)}",
            parse_mode=ParseMode.HTML,
        )

    async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return
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

    async def cmd_salir(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return
        await update.message.reply_text("🛑 Apagando NEO... hasta pronto.")
        logger.info(f"Apagado solicitado por usuario {update.effective_user.id}")
        if stop_event:
            stop_event.set()
        async def _stop():
            await asyncio.sleep(1)
            await context.application.stop()
        asyncio.create_task(_stop())

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not is_allowed(uid):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        user_input = update.message.text.strip()
        if not user_input:
            return

        # Mostrar "Pensando..." inmediatamente y mantener typing activo
        thinking_msg = await update.message.reply_text("💭 Pensando...")
        await update.message.chat.send_action(ChatAction.TYPING)

        agent = await get_agent(uid)
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

            full_response = header + _md_to_html(output)

            # Editar el mensaje "Pensando..." con la respuesta real
            # Si la respuesta es muy larga, borrar y enviar en partes
            if len(full_response) <= 4096:
                await thinking_msg.edit_text(full_response, parse_mode=ParseMode.HTML)
            else:
                await thinking_msg.delete()
                await _send_long(update, full_response, ParseMode.HTML)

            user_sessions[uid].append({"role": "assistant", "content": output})

        except Exception as e:
            logger.error(f"Error usuario {uid}: {e}", exc_info=True)
            await thinking_msg.edit_text(
                f"❌ <b>Error:</b> <code>{str(e)[:400]}</code>\n\n"
                "Revisa tu API key y el modelo en config/settings.cfg",
                parse_mode=ParseMode.HTML,
            )


    # ── Handler de voz ────────────────────────────────────────────────────────

    async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe audios de voz, los transcribe con Whisper y los procesa como texto."""
        uid = update.effective_user.id
        if not is_allowed(uid):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        thinking_msg = await update.message.reply_text("🎙️ Transcribiendo audio...")
        await update.message.chat.send_action(ChatAction.TYPING)

        try:
            import tempfile, os as _os
            voice = update.message.voice or update.message.audio
            if not voice:
                await thinking_msg.edit_text("❌ No se pudo obtener el audio.")
                return

            # Descargar el archivo de voz
            tg_file = await context.bot.get_file(voice.file_id)
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                tmp_path = tmp.name
            await tg_file.download_to_drive(tmp_path)

            # Transcribir con MLX Whisper (Apple Silicon) o Whisper CPU
            try:
                from tools.tools import _transcribe_audio
                transcription, backend, _ = _transcribe_audio(tmp_path, language="es")
            except ImportError as ie:
                _os.unlink(tmp_path)
                await update.message.reply_text(
                    f"⚠️ Whisper no disponible: <code>{ie}</code>",
                    parse_mode=ParseMode.HTML,
                )
                return
            except Exception as we:
                _os.unlink(tmp_path)
                await update.message.reply_text(
                    f"❌ Error al transcribir: <code>{str(we)[:300]}</code>",
                    parse_mode=ParseMode.HTML,
                )
                return
            finally:
                try:
                    _os.unlink(tmp_path)
                except Exception:
                    pass

            if not transcription:
                await update.message.reply_text("⚠️ No se detectó habla en el audio.")
                return

            # Mostrar transcripción y pasar a "Pensando..."
            await thinking_msg.edit_text(
                f"🎙️ <i>Transcripción:</i> {transcription}",
                parse_mode=ParseMode.HTML,
            )
            thinking_msg2 = await update.message.reply_text("💭 Pensando...")

            # Procesar como mensaje normal
            agent = await get_agent(uid)
            user_sessions[uid].append({"role": "user", "content": transcription})

            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: agent.invoke({"input": transcription})
            )
            output = result.get("output", "Sin respuesta.")
            steps = result.get("intermediate_steps", [])
            header = f"<i>🔧 {', '.join(a.tool for a, _ in steps)}</i>\n\n" if steps else ""
            full_response = header + _md_to_html(output)

            if len(full_response) <= 4096:
                await thinking_msg2.edit_text(full_response, parse_mode=ParseMode.HTML)
            else:
                await thinking_msg2.delete()
                await _send_long(update, full_response, ParseMode.HTML)

            user_sessions[uid].append({"role": "assistant", "content": output})

        except Exception as e:
            logger.error(f"Error en handle_voice {uid}: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error al procesar audio: {str(e)[:200]}")

    # ── Handler de imágenes ───────────────────────────────────────────────────

    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe imágenes, las analiza con visión y responde."""
        uid = update.effective_user.id
        if not is_allowed(uid):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        await update.message.chat.send_action(ChatAction.TYPING)

        try:
            import tempfile, os as _os, base64 as _b64

            # Obtener la foto en mejor calidad
            photo = update.message.photo[-1]
            caption = update.message.caption or "Describe esta imagen en detalle."

            tg_file = await context.bot.get_file(photo.file_id)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
            await tg_file.download_to_drive(tmp_path)

            try:
                api_key = _os.getenv("OPENROUTER_API_KEY", "")
                model = _os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")

                if not api_key:
                    await update.message.reply_text(
                        "❌ OPENROUTER_API_KEY no configurada. La visión requiere OpenRouter."
                    )
                    return

                image_data = _b64.b64encode(open(tmp_path, "rb").read()).decode("utf-8")

                import requests as _req
                resp = _req.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                                {"type": "text", "text": caption},
                            ],
                        }],
                        "max_tokens": 1024,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"]

            finally:
                _os.unlink(tmp_path)

            await _send_long(update, _md_to_html(answer), ParseMode.HTML)

        except Exception as e:
            logger.error(f"Error en handle_photo {uid}: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error al analizar imagen: {str(e)[:200]}")


    async def cmd_cron(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /cron <horario> <comando> — añade una tarea programada."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.cron import cron_add, schedule_description, type_icon

        args = " ".join(context.args).strip() if context.args else ""
        if not args:
            await update.message.reply_text(
                "📋 <b>Uso de /cron:</b>\n\n"
                "<code>/cron HH:MM texto</code> — 🔔 Notificación fija\n"
                "<code>/cron HH:MM llm: prompt</code> — 🤖 LLM genera el mensaje\n"
                "<code>/cron HH:MM shell: cmd</code> — ⚙️ Ejecuta un comando\n\n"
                "<b>Formatos de horario:</b>\n"
                "  <code>09:00</code>  → diario a esa hora\n"
                "  <code>*/30m</code> → cada 30 minutos\n"
                "  <code>*/2h</code>  → cada 2 horas\n\n"
                "<b>Ejemplos:</b>\n"
                "  <code>/cron 09:00 Buenos días!</code>\n"
                "  <code>/cron */1h llm: Dame un consejo aleatorio</code>\n"
                "  <code>/cron 08:00 shell: ~/scripts/backup.sh</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        # Separar horario del resto
        parts = args.split(None, 1)
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Falta el comando. Uso: <code>/cron &lt;horario&gt; &lt;texto|llm:|shell:&gt;</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        schedule_str, command = parts[0], parts[1]

        try:
            task = cron_add(schedule_str, command)
            icon = type_icon(task["type"])
            desc = schedule_description(task["schedule"])
            await update.message.reply_text(
                f"✅ Tarea creada <b>[{task['id']}]</b>\n\n"
                f"{icon} <b>Tipo:</b> {task['type']}\n"
                f"⏰ <b>Horario:</b> {desc}\n"
                f"📝 <b>Contenido:</b> <code>{task['content']}</code>",
                parse_mode=ParseMode.HTML,
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)

    async def cmd_cronlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /cronlist — lista todas las tareas programadas."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.cron import cron_list, schedule_description, type_icon

        crons = cron_list()
        if not crons:
            await update.message.reply_text("📭 No hay tareas programadas.")
            return

        lines = [f"<b>⏰ Tareas programadas ({len(crons)})</b>\n"]
        for t in crons:
            icon = type_icon(t["type"])
            desc = schedule_description(t["schedule"])
            last = t["last_run"][:16].replace("T", " ") if t["last_run"] else "nunca"
            lines.append(
                f"{icon} <b>[{t['id']}]</b> <code>{t['schedule_str']}</code> — {desc}\n"
                f"   📝 {t['content'][:60]}{'...' if len(t['content']) > 60 else ''}\n"
                f"   🕐 Última ejecución: {last} · Total: {t.get('run_count', 0)}\n"
            )
        await _send_long(update, "\n".join(lines), ParseMode.HTML)

    async def cmd_crondel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /crondel <id> — elimina una tarea."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.cron import cron_delete

        task_id = context.args[0].upper() if context.args else ""
        if not task_id:
            await update.message.reply_text("❌ Uso: <code>/crondel &lt;ID&gt;</code>", parse_mode=ParseMode.HTML)
            return

        if cron_delete(task_id):
            await update.message.reply_text(f"✅ Tarea <b>[{task_id}]</b> eliminada.", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"❌ No se encontró la tarea <b>[{task_id}]</b>.", parse_mode=ParseMode.HTML)

    async def cmd_cronclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /cronclear — elimina todas las tareas."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.cron import cron_clear

        n = cron_clear()
        await update.message.reply_text(f"🗑️ {n} tarea(s) eliminada(s).")


    async def cmd_motorllm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /motorllm <proveedor> — cambia el proveedor LLM en caliente."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.llm_manager import set_provider, ALL_PROVIDERS, LOCAL_PROVIDERS, get_current_provider, get_current_model

        provider = context.args[0].lower().strip() if context.args else ""

        if not provider:
            current = get_current_provider()
            model = get_current_model()
            local = sorted(LOCAL_PROVIDERS)
            remote = sorted(ALL_PROVIDERS - LOCAL_PROVIDERS)
            await update.message.reply_text(
                f"<b>🔧 Proveedor LLM actual:</b> <code>{current}</code>\n"
                f"<b>Modelo:</b> <code>{model or '(no definido)'}</code>\n\n"
                f"<b>Proveedores locales:</b> {', '.join(f'<code>{p}</code>' for p in local)}\n"
                f"<b>Proveedores remotos:</b> {', '.join(f'<code>{p}</code>' for p in remote)}\n\n"
                f"Uso: <code>/motorllm &lt;proveedor&gt;</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        try:
            from core.llm_manager import LOCAL_PROVIDERS as _LOCAL
            set_provider(provider)

            # Si es proveedor local y el modelo actual parece remoto (contiene /),
            # limpiar para que use el modelo cargado en LM Studio/Ollama
            current_model = os.getenv("LLM_MODEL", "")
            if provider in _LOCAL and "/" in current_model:
                os.environ["LLM_MODEL"] = ""
                model_note = "\n⚠️ Modelo limpiado (era remoto). Usa /load para cargar uno local."
            else:
                model_note = ""

            # Reiniciar agentes
            user_agents.clear()

            # Para proveedores locales, pre-inicializar el agente aquí
            # con feedback visual, para no bloquear el primer mensaje
            if provider in _LOCAL:
                thinking = await update.message.reply_text(
                    f"⏳ Conectando con <code>{provider}</code> y comprobando soporte de herramientas...",
                    parse_mode=ParseMode.HTML,
                )
                try:
                    from core.agent import create_agent
                    uid = update.effective_user.id
                    user_agents[uid] = await asyncio.get_event_loop().run_in_executor(
                        None, create_agent
                    )
                    user_sessions[uid] = []
                    n_tools = len(user_agents[uid].tools)
                    tools_info = f"✅ {n_tools} herramientas activas" if n_tools > 0 else "⚠️ Sin herramientas (modelo no soporta tool calling)"
                    await thinking.edit_text(
                        f"✅ Proveedor cambiado a <code>{provider}</code>{model_note}\n"
                        f"{tools_info}\n\n"
                        f"💡 Usa /listmodels para ver modelos disponibles.",
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as e:
                    await thinking.edit_text(
                        f"❌ Error al conectar con {provider}: <code>{str(e)[:200]}</code>",
                        parse_mode=ParseMode.HTML,
                    )
            else:
                await update.message.reply_text(
                    f"✅ Proveedor cambiado a <code>{provider}</code>{model_note}\n\n"
                    f"💡 Usa /load &lt;modelo&gt; para cambiar el modelo.",
                    parse_mode=ParseMode.HTML,
                )
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}", parse_mode=ParseMode.HTML)

    async def cmd_listmodels(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /listmodels — lista modelos disponibles."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.llm_manager import (
            get_current_provider, is_local, list_models_local,
            get_remote_model_examples, format_size
        )

        provider = get_current_provider()
        await update.message.chat.send_action(ChatAction.TYPING)

        if is_local(provider):
            try:
                models = list_models_local(provider)
                if not models:
                    await update.message.reply_text(
                        f"📭 No hay modelos disponibles en {provider}.\n"
                        f"Asegúrate de que el servidor está activo.",
                        parse_mode=ParseMode.HTML,
                    )
                    return

                lines = [f"<b>📦 Modelos en {provider} ({len(models)})</b>\n"]
                for m in models:
                    loaded_icon = "🟢" if m.get("loaded") else "⚪"
                    size = f"  {format_size(m['size'])}" if m.get("size") else ""
                    lines.append(f"{loaded_icon} <code>{m['id']}</code>{size}")
                lines.append("\n🟢 En memoria  ⚪ Disponible")
                lines.append("Usa <code>/load &lt;modelo&gt;</code> para cargar uno.")
                await _send_long(update, "\n".join(lines), ParseMode.HTML)

            except requests.exceptions.ConnectionError:
                await update.message.reply_text(
                    f"❌ No se puede conectar a {provider}.\n"
                    f"¿Está el servidor activo?",
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {str(e)[:200]}", parse_mode=ParseMode.HTML)

        else:
            # Proveedor remoto — mostrar ejemplos
            examples = get_remote_model_examples(provider)
            current_model = os.getenv("LLM_MODEL", "")
            lines = [
                f"<b>🌐 Modelos de {provider}</b>\n",
                f"<b>Modelo actual:</b> <code>{current_model or '(no definido)'}</code>\n",
                "<b>Modelos populares:</b>\n",
            ]
            for m in examples:
                icon = "✅" if m == current_model else "  "
                lines.append(f"{icon} <code>{m}</code>")
            lines.append(f"\nUsa <code>/load &lt;modelo&gt;</code> para cambiar.\n"
                         f"Catálogo completo en <a href=\"https://openrouter.ai/models\">openrouter.ai/models</a>"
                         if provider == "openrouter" else "")
            await _send_long(update, "\n".join(lines), ParseMode.HTML)

    async def cmd_load(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /load <modelo> — carga un modelo."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.llm_manager import (
            get_current_provider, is_local, load_model_local, set_model
        )

        model = " ".join(context.args).strip() if context.args else ""
        if not model:
            await update.message.reply_text(
                "❌ Uso: <code>/load &lt;nombre_modelo&gt;</code>\n\n"
                "Ejemplos:\n"
                "  <code>/load qwen2.5-7b-instruct</code>\n"
                "  <code>/load anthropic/claude-3.5-sonnet</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        provider = get_current_provider()
        await update.message.chat.send_action(ChatAction.TYPING)
        await update.message.reply_text(
            f"⏳ Cargando <code>{model}</code> en <code>{provider}</code>...",
            parse_mode=ParseMode.HTML,
        )

        try:
            if is_local(provider):
                result = load_model_local(model, provider)
            else:
                result = f"✅ Modelo cambiado a <code>{model}</code> en {provider}"

            set_model(model)
            user_agents.clear()  # Reiniciar agentes con el nuevo modelo

            await update.message.reply_text(
                f"{result}\nEl agente usará este modelo en el próximo mensaje.",
                parse_mode=ParseMode.HTML,
            )

        except requests.exceptions.ConnectionError:
            await update.message.reply_text(
                f"❌ No se puede conectar a {provider}.\n¿Está el servidor activo?",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:300]}", parse_mode=ParseMode.HTML)

    async def cmd_unload(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /unload <modelo> — descarga un modelo de memoria."""
        if not is_allowed(update.effective_user.id):
            await update.message.reply_text("⛔ No tienes acceso a este bot.")
            return

        from core.llm_manager import get_current_provider, is_local, unload_model_local

        provider = get_current_provider()

        if not is_local(provider):
            await update.message.reply_text(
                f"⚠️ <code>{provider}</code> es un proveedor remoto.\n"
                "El unload solo aplica a proveedores locales (lmstudio, ollama).",
                parse_mode=ParseMode.HTML,
            )
            return

        model = " ".join(context.args).strip() if context.args else os.getenv("LLM_MODEL", "")
        if not model:
            await update.message.reply_text(
                "❌ Uso: <code>/unload &lt;modelo&gt;</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        try:
            result = unload_model_local(model, provider)
            await update.message.reply_text(result, parse_mode=ParseMode.HTML)
        except requests.exceptions.ConnectionError:
            await update.message.reply_text(
                f"❌ No se puede conectar a {provider}.",
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:300]}", parse_mode=ParseMode.HTML)

    # ── Construir app ──────────────────────────────────────────────────────────

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("reset",   cmd_reset))
    app.add_handler(CommandHandler("memoria", cmd_memoria))
    app.add_handler(CommandHandler("estado",  cmd_estado))
    app.add_handler(CommandHandler("ayuda",   cmd_ayuda))
    app.add_handler(CommandHandler("salir",      cmd_salir))
    app.add_handler(CommandHandler("cron",       cmd_cron))
    app.add_handler(CommandHandler("cronlist",   cmd_cronlist))
    app.add_handler(CommandHandler("crondel",    cmd_crondel))
    app.add_handler(CommandHandler("cronclear",   cmd_cronclear))
    app.add_handler(CommandHandler("motorllm",    cmd_motorllm))
    app.add_handler(CommandHandler("listmodels",  cmd_listmodels))
    app.add_handler(CommandHandler("load",        cmd_load))
    app.add_handler(CommandHandler("unload",      cmd_unload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    async def post_init(application):
        await application.bot.set_my_commands([
            BotCommand("start",   "Bienvenida"),
            BotCommand("ayuda",   "Qué puede hacer NEO"),
            BotCommand("memoria", "Ver recuerdos guardados"),
            BotCommand("estado",  "Estado del agente y modelo activo"),
            BotCommand("reset",   "Reiniciar conversación"),
            BotCommand("salir",      "Apagar el agente"),
            BotCommand("cron",       "Añadir tarea programada"),
            BotCommand("cronlist",   "Ver tareas programadas"),
            BotCommand("crondel",    "Eliminar tarea por ID"),
            BotCommand("cronclear",    "Borrar todas las tareas"),
            BotCommand("motorllm",     "Cambiar proveedor LLM"),
            BotCommand("listmodels",   "Listar modelos disponibles"),
            BotCommand("load",         "Cargar o cambiar modelo"),
            BotCommand("unload",       "Descargar modelo de memoria"),
        ])
        # Arrancar el scheduler de crons
        from core.cron import cron_loop
        async def _send_cron_msg(text):
            raw = os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
            if raw:
                cid = raw.split(",")[0].strip()
                try:
                    await application.bot.send_message(chat_id=cid, text=text, parse_mode="HTML")
                except Exception as ce:
                    logger.error(f"Error enviando cron msg: {ce}")
        def _get_agent():
            # Devuelve el agente del primer usuario activo (ya creado)
            # Los crons solo ejecutan si el agente ya fue inicializado
            return next(iter(user_agents.values()), None)
        asyncio.create_task(cron_loop(_send_cron_msg, _get_agent, stop_event))

    app.post_init = post_init

    logger.info(f"🤖 NEO Telegram Bot · {os.getenv('LLM_PROVIDER', '?')} / {os.getenv('LLM_MODEL', '?')}")
    if allowed_ids:
        logger.info(f"   Whitelist: {allowed_ids}")
    print("\n✅ NEO Bot activo en Telegram. Ctrl+C para detener.\n")

    return app


def _telegram_run(stop_event: threading.Event = None):
    try:
        from telegram import Update as TelegramUpdate
    except ImportError:
        print("\n❌ python-telegram-bot no está instalado. Ejecuta: pip install python-telegram-bot\n")
        return
    app = run_telegram(stop_event)
    if app is None:
        return
    app.run_polling(allowed_updates=TelegramUpdate.ALL_TYPES)
    # Si llegamos aquí es porque el bot paró (ej: /salir desde Telegram)
    if stop_event:
        stop_event.set()
    sys.exit(0)


# ── Helpers Telegram ──────────────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
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
# MODO AMBOS
# ══════════════════════════════════════════════════════════════════════════════

def run_ambos():
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
        try:
            _terminal_loop(stop_event)
        except Exception as e:
            if not stop_event.is_set():
                print(f"\n⚠️  Terminal se detuvo: {e}")
        finally:
            stop_event.set()

    t = threading.Thread(target=terminal_thread, daemon=True, name="neo-terminal")
    t.start()

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
