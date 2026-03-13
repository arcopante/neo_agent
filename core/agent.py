"""
agent.py — Núcleo del agente NEO

Usa la API moderna de LangChain con langgraph (create_react_agent),
compatible con LangChain >= 0.3 y Python 3.12+.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Directorio raíz del proyecto
ROOT = Path(__file__).parent.parent


def _load_settings():
    """
    Carga config/settings.cfg y exporta sus valores como variables de entorno.
    Las variables ya definidas en el entorno tienen prioridad (no se sobreescriben).
    """
    settings_path = ROOT / "config" / "settings.cfg"
    if not settings_path.exists():
        return  # Sin fichero de config se continúa con lo que haya en el entorno

    with open(settings_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Ignorar comentarios y líneas vacías
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # El entorno tiene prioridad sobre el fichero
            if key and key not in os.environ:
                os.environ[key] = value


# Cargar configuración al importar el módulo
_load_settings()


def _get_llm():
    """
    Inicializa el LLM según LLM_PROVIDER.
    Soporta: lmstudio (default), anthropic, openai, google.
    """
    provider = os.getenv("LLM_PROVIDER", "lmstudio").lower()

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY no está definida. "
                "Añádela en config/settings.cfg o como variable de entorno."
            )
        model = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
        app_name = os.getenv("OPENROUTER_APP_NAME", "NEO Agent")
        return ChatOpenAI(
            model=model,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            default_headers={
                "HTTP-Referer": "https://github.com/neo-agent",
                "X-Title": app_name,
            },
        )

    elif provider == "lmstudio":
        from langchain_openai import ChatOpenAI
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = os.getenv("LLM_MODEL", "local-model")
        if os.getenv("LMSTUDIO_TOOL_MODE", "auto").lower() == "prompt":
            _warn_tool_mode()
        return ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key="lm-studio",
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("LLM_MODEL", "gemini-1.5-pro"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        )

    else:
        raise ValueError(
            f"LLM_PROVIDER desconocido: '{provider}'. "
            "Opciones válidas: lmstudio, anthropic, openai, google"
        )


def _warn_tool_mode():
    print(
        "\n⚠️  LMSTUDIO_TOOL_MODE=prompt activo.\n"
        "   Si el agente no usa herramientas, prueba Qwen2.5, Mistral o Llama 3.1+\n"
    )


class NeoAgent:
    """
    Wrapper del agente NEO usando la API moderna de LangChain.
    Mantiene el historial de conversación internamente.
    """

    def __init__(self, llm, tools, system_prompt: str, window_size: int = 20):
        from langgraph.prebuilt import create_react_agent
        from langchain_core.messages import SystemMessage

        self.tools = tools
        self.window_size = window_size
        self.history = []  # Lista de mensajes HumanMessage / AIMessage

        self.graph = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt,
        )

    def invoke(self, input_dict: dict) -> dict:
        from langchain_core.messages import HumanMessage

        user_text = input_dict["input"]
        self.history.append(HumanMessage(content=user_text))

        # Ventana deslizante
        window = self.history[-(self.window_size * 2):]

        result = self.graph.invoke({"messages": window})

        # Extraer respuesta final
        messages = result.get("messages", [])
        output = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content and msg.__class__.__name__ == "AIMessage":
                output = msg.content
                break

        # Guardar respuesta en historial
        from langchain_core.messages import AIMessage
        self.history.append(AIMessage(content=output))

        # Extraer herramientas usadas para mostrarlas
        intermediate = []
        for msg in messages:
            if msg.__class__.__name__ == "ToolMessage":
                intermediate.append((
                    type("Action", (), {"tool": msg.name})(),
                    msg.content
                ))

        return {
            "output": output,
            "intermediate_steps": intermediate,
        }


def create_agent() -> NeoAgent:
    """
    Crea y configura el agente NEO completo.
    """
    sys.path.insert(0, str(ROOT))
    from core.config_loader import build_system_prompt, get_user_preferences
    from tools.tools import ALL_TOOLS

    llm = _get_llm()
    prefs = get_user_preferences()

    tools_list = "\n".join([f"- {t.name}: {t.description[:80]}..." for t in ALL_TOOLS])
    system_prompt = build_system_prompt(tools_list=tools_list)

    window_size = int(os.getenv("MEMORY_WINDOW", "20"))

    return NeoAgent(
        llm=llm,
        tools=ALL_TOOLS,
        system_prompt=system_prompt,
        window_size=window_size,
    )


def save_session(messages: list, session_dir: Path) -> None:
    """Guarda el log de la sesión en un archivo JSON."""
    session_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_file = session_dir / f"{timestamp}.json"
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(
            {"timestamp": timestamp, "messages": messages, "message_count": len(messages)},
            f, indent=2, ensure_ascii=False,
        )
