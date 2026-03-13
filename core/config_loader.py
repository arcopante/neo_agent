"""
config_loader.py — Carga los ficheros de configuración markdown del agente.

Lee SOUL.md, IDENTITY.md, USER.md, MEMORY.md y construye
el prompt de sistema dinámico.
"""

from datetime import datetime
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_markdown(filename: str) -> str:
    """Lee un fichero markdown de configuración."""
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        return f"[{filename} no encontrado]"
    return filepath.read_text(encoding="utf-8").strip()


def build_system_prompt(relevant_memories: str = "", tools_list: str = "") -> str:
    """
    Construye el prompt de sistema completo combinando todos los ficheros config.
    
    Args:
        relevant_memories: Memorias relevantes ya recuperadas de long_term.json
        tools_list: Lista de herramientas disponibles formateada
    
    Returns:
        Prompt de sistema listo para enviar al LLM.
    """
    soul = load_markdown("SOUL.md")
    identity = load_markdown("IDENTITY.md")
    user = load_markdown("USER.md")

    # Extraer secciones relevantes de los docs más largos
    soul_excerpt = _extract_section(soul, max_chars=800)
    identity_excerpt = _extract_section(identity, max_chars=600)
    user_excerpt = _extract_section(user, max_chars=500)

    now = datetime.now().strftime("%A, %d de %B de %Y — %H:%M")

    prompt = f"""Eres NEO, un agente de IA con capacidad de acción real mediante herramientas.

═══ ESENCIA (SOUL) ═══
{soul_excerpt}

═══ IDENTIDAD ═══
{identity_excerpt}

═══ PERFIL DE USUARIO ═══
{user_excerpt}

═══ MEMORIA RELEVANTE ═══
{relevant_memories if relevant_memories else "No hay recuerdos previos relevantes."}

═══ HERRAMIENTAS DISPONIBLES ═══
{tools_list if tools_list else "Ver descripción de cada herramienta en sus definiciones."}

═══ INSTRUCCIONES OPERATIVAS ═══
1. RAZONA antes de actuar. Si la petición es ambigua, pregunta UNA cosa.
2. Cuando uses una herramienta, explica brevemente por qué la usas.
3. Muestra siempre el resultado real de las herramientas.
4. Para escribir archivos o ejecutar código, confirma con el usuario primero.
5. Si algo falla, di exactamente qué falló y propón alternativa.
6. Responde SIEMPRE en el idioma del usuario.
7. Guarda en memoria lo que sea útil para sesiones futuras.

Fecha y hora actual: {now}
"""
    return prompt.strip()


def _extract_section(content: str, max_chars: int = 800) -> str:
    """Extrae las partes más relevantes de un documento markdown."""
    if len(content) <= max_chars:
        return content
    # Devolver los primeros max_chars y avisar que hay más
    return content[:max_chars] + "\n[...documento continúa...]"


def get_user_preferences() -> dict:
    """
    Parsea USER.md y extrae preferencias en formato dict.
    Usa una extracción simple basada en patrones YAML.
    """
    user_content = load_markdown("USER.md")
    prefs = {
        "confirmar_acciones": True,
        "mostrar_razonamiento": True,
        "estilo": "balanceado",
        "formato": "markdown",
    }

    lines = user_content.split("\n")
    for line in lines:
        line = line.strip()
        if "confirmar_acciones:" in line:
            prefs["confirmar_acciones"] = "true" in line.lower()
        elif "mostrar_razonamiento:" in line:
            prefs["mostrar_razonamiento"] = "true" in line.lower()
        elif "estilo:" in line and "#" not in line:
            val = line.split(":", 1)[-1].strip().strip('"')
            if val in ("conciso", "balanceado", "detallado"):
                prefs["estilo"] = val

    return prefs
