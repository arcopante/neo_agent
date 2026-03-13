#!/usr/bin/env python3
"""
main.py — Punto de entrada del agente NEO

Interfaz de línea de comandos con formato rico.
Ejecutar con: python main.py
"""

import os
import sys
from pathlib import Path

# Cargar .env solo si existe (opcional — la config principal va en start.sh)
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass

# Añadir raíz del proyecto al path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Verificar dependencias básicas ──────────────────────────────────────────

def check_dependencies():
    """Verifica que las dependencias críticas estén instaladas."""
    missing = []
    try:
        import langchain  # noqa: F401
    except ImportError:
        missing.append("langchain")
    try:
        import langchain_core  # noqa: F401
    except ImportError:
        missing.append("langchain-core")

    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "anthropic":
        try:
            import langchain_anthropic  # noqa: F401
        except ImportError:
            missing.append("langchain-anthropic")
    elif provider == "openai":
        try:
            import langchain_openai  # noqa: F401
        except ImportError:
            missing.append("langchain-openai")
    elif provider == "google":
        try:
            import langchain_google_genai  # noqa: F401
        except ImportError:
            missing.append("langchain-google-genai")

    if missing:
        print(f"\n❌ Faltan dependencias: {', '.join(missing)}")
        print("   Instálalas con: pip install -r requirements.txt\n")
        sys.exit(1)


# ── Interface Rich ──────────────────────────────────────────────────────────

def print_banner():
    """Muestra el banner de inicio."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()
        title = Text("NEO", style="bold cyan", justify="center")
        subtitle = Text(
            "Agente de Ejecución Orgánica\n"
            "Powered by LangChain · Escribe 'ayuda' para ver comandos",
            style="dim",
            justify="center",
        )
        content = Text.assemble(title, "\n", subtitle)
        console.print(Panel(content, border_style="cyan", padding=(1, 4)))

    except ImportError:
        print("\n" + "═" * 50)
        print("  NEO — Agente de IA con LangChain")
        print("  Escribe 'ayuda' para ver comandos")
        print("═" * 50 + "\n")


def format_response(response: dict) -> str:
    """Formatea la respuesta del agente para mostrarla."""
    output = response.get("output", "")
    
    # Si hay pasos intermedios, mostrarlos
    steps = response.get("intermediate_steps", [])
    if steps:
        tool_info = []
        for action, result in steps:
            tool_info.append(f"🔧 Usé **{action.tool}** → {str(result)[:200]}...")
        if tool_info:
            output = "\n".join(tool_info) + "\n\n" + output

    return output


# ── Comandos especiales del CLI ─────────────────────────────────────────────

SPECIAL_COMMANDS = {
    "ayuda": """
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
También puedes pedir al agente:
  "busca información sobre X"
  "lee el archivo X.txt"
  "guarda esto en memoria"
  "ejecuta este código Python: ..."
  "¿cuánto es [expresión matemática]?"
""",
    "config": None,  # Se genera dinámicamente
}


def show_config():
    """Muestra la configuración actual del agente."""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    workspace = os.getenv("AGENT_WORKSPACE", str(Path.home() / "agent_workspace"))
    memory_window = os.getenv("MEMORY_WINDOW", "20")
    verbose = os.getenv("AGENT_VERBOSE", "false")

    return f"""
🔧 **Configuración actual:**
  - Proveedor LLM : {provider}
  - Modelo        : {model}
  - Workspace     : {workspace}
  - Ventana mem.  : {memory_window} mensajes
  - Verbose       : {verbose}
  - Config dir    : {ROOT / 'config'}
  - Memoria dir   : {ROOT / 'memory'}
"""


# ── Bucle principal ─────────────────────────────────────────────────────────

def main():
    """Bucle principal de conversación."""
    check_dependencies()
    print_banner()

    # Inicializar agente
    print("⏳ Inicializando agente...")
    try:
        from core.agent import create_agent, save_session
        agent = create_agent()
        print("✅ Agente listo.\n")
    except Exception as e:
        print(f"❌ Error al inicializar el agente: {e}")
        print(f"\nDetalle: {e}")
        print("\nAsegúrate de que LM Studio está abierto y el servidor local activo.")
        sys.exit(1)

    # Intentar usar Rich para output bonito
    try:
        from rich.console import Console
        from rich.markdown import Markdown
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False
        console = None

    session_messages = []
    session_dir = ROOT / "memory" / "sessions"

    def print_response(text: str):
        if use_rich:
            try:
                console.print(Markdown(text))
            except Exception:
                print(text)
        else:
            print(text)

    # Bucle de conversación
    while True:
        try:
            user_input = input("\n👤 Tú: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 ¡Hasta luego!")
            save_session(session_messages, session_dir)
            break

        if not user_input:
            continue

        # Comandos especiales
        cmd = user_input.lower()

        if cmd in ("salir", "exit", "quit", "q"):
            print("\n👋 ¡Hasta luego!")
            save_session(session_messages, session_dir)
            break

        if cmd == "ayuda":
            print(SPECIAL_COMMANDS["ayuda"])
            continue

        if cmd == "config":
            print_response(show_config())
            continue

        if cmd == "limpiar":
            os.system("clear" if os.name != "nt" else "cls")
            print_banner()
            continue

        if cmd in ("nueva sesión", "nueva sesion", "reset"):
            save_session(session_messages, session_dir)
            from core.agent import create_agent
            agent = create_agent()
            session_messages = []
            print("🔄 Sesión reiniciada.\n")
            continue

        if cmd == "memoria":
            # Invocar la herramienta de memoria directamente
            user_input = "lista todos mis recuerdos guardados en memoria"

        # Registrar mensaje del usuario
        session_messages.append({"role": "user", "content": user_input})

        # Invocar al agente
        print("\n🤖 Neo: ", end="", flush=True)
        try:
            response = agent.invoke({"input": user_input})
            formatted = format_response(response)
            print()  # Nueva línea después del prefijo
            print_response(formatted)

            # Registrar respuesta
            session_messages.append({"role": "assistant", "content": formatted})

        except KeyboardInterrupt:
            print("\n[Respuesta interrumpida]")

        except Exception as e:
            error_msg = f"❌ Error del agente: {str(e)}"
            print(f"\n{error_msg}")
            if os.getenv("AGENT_DEBUG", "false").lower() == "true":
                import traceback
                traceback.print_exc()
            session_messages.append({"role": "error", "content": error_msg})


if __name__ == "__main__":
    main()
