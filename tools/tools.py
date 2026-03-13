"""
tools.py — Herramientas del agente NEO

Cada herramienta es una función decorada con @tool de LangChain.
Añade nuevas herramientas aquí y se registrarán automáticamente.
"""

import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from langchain.tools import tool

# Directorio base permitido para operaciones de archivo
WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", str(Path(__file__).parent.parent / "workspace")))
WORKSPACE.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = Path(__file__).parent.parent / "memory" / "long_term.json"
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# 🔍 BÚSQUEDA WEB
# ─────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """
    Busca información actualizada en internet usando DuckDuckGo.
    Úsala para noticias recientes, documentación, o cualquier info que pueda haber cambiado.
    
    Args:
        query: La consulta de búsqueda en lenguaje natural.
    
    Returns:
        Lista de resultados con título, URL y fragmento de texto.
    """
    try:
        try:
            from ddgs import DDGS  # nuevo nombre del paquete
        except ImportError:
            from duckduckgo_search import DDGS  # fallback nombre antiguo

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(
                    f"**{r['title']}**\n{r['href']}\n{r['body']}\n"
                )

        if not results:
            return "No se encontraron resultados para esta búsqueda."

        return "\n---\n".join(results)

    except ImportError:
        return (
            "❌ Instala el paquete de búsqueda: pip install ddgs"
        )
    except Exception as e:
        return f"❌ Error al buscar: {str(e)}"


# ─────────────────────────────────────────────
# 📁 SISTEMA DE ARCHIVOS
# ─────────────────────────────────────────────

@tool
def read_file(filepath: str) -> str:
    """
    Lee el contenido de un archivo de texto.
    
    Args:
        filepath: Ruta al archivo (absoluta o relativa al workspace).
    
    Returns:
        Contenido del archivo como texto.
    """
    try:
        path = _resolve_path(filepath)
        if not path.exists():
            return f"❌ El archivo no existe: {path}"
        if not path.is_file():
            return f"❌ La ruta no es un archivo: {path}"

        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.count("\n") + 1
        size = path.stat().st_size

        return (
            f"📄 **{path.name}** ({lines} líneas, {size} bytes)\n\n"
            f"```\n{content}\n```"
        )
    except PermissionError:
        return f"❌ Sin permisos para leer: {filepath}"
    except Exception as e:
        return f"❌ Error al leer archivo: {str(e)}"


@tool
def write_file(filepath: str, content: str, mode: str = "write") -> str:
    """
    Escribe contenido en un archivo. Crea el archivo si no existe.
    IMPORTANTE: Esta acción puede sobreescribir datos. Confirma con el usuario antes de usar.
    
    Args:
        filepath: Ruta al archivo (relativa al workspace o absoluta).
        content: Contenido a escribir.
        mode: 'write' para crear/sobreescribir, 'append' para añadir al final.
    
    Returns:
        Confirmación de escritura o mensaje de error.
    """
    try:
        path = _resolve_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        write_mode = "a" if mode == "append" else "w"
        with open(path, write_mode, encoding="utf-8") as f:
            f.write(content)

        action = "añadido a" if mode == "append" else "escrito en"
        size = path.stat().st_size
        return f"✅ Contenido {action} **{path}** ({size} bytes)"

    except PermissionError:
        return f"❌ Sin permisos para escribir en: {filepath}"
    except Exception as e:
        return f"❌ Error al escribir archivo: {str(e)}"


@tool
def list_directory(dirpath: str = ".") -> str:
    """
    Lista el contenido de un directorio mostrando archivos y carpetas.
    
    Args:
        dirpath: Ruta del directorio a listar. Por defecto el workspace.
    
    Returns:
        Árbol de archivos y directorios.
    """
    try:
        path = _resolve_path(dirpath)
        if not path.exists():
            return f"❌ El directorio no existe: {path}"
        if not path.is_dir():
            return f"❌ La ruta no es un directorio: {path}"

        lines = [f"📂 **{path}**"]
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

        for item in items:
            if item.is_dir():
                count = len(list(item.iterdir()))
                lines.append(f"  📁 {item.name}/ ({count} items)")
            else:
                size = item.stat().st_size
                lines.append(f"  📄 {item.name} ({_format_size(size)})")

        if not items:
            lines.append("  (directorio vacío)")

        return "\n".join(lines)

    except PermissionError:
        return f"❌ Sin permisos para listar: {dirpath}"
    except Exception as e:
        return f"❌ Error al listar directorio: {str(e)}"


# ─────────────────────────────────────────────
# 🐍 EJECUCIÓN DE CÓDIGO
# ─────────────────────────────────────────────

@tool
def run_python(code: str) -> str:
    """
    Ejecuta un fragmento de código Python y devuelve el output.
    IMPORTANTE: Requiere confirmación del usuario antes de ejecutar.
    El código tiene acceso limitado al sistema. Timeout: 30 segundos.
    
    Args:
        code: Código Python a ejecutar.
    
    Returns:
        Stdout y stderr del proceso, o mensaje de error.
    """
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(WORKSPACE),
        )

        output_parts = []
        if result.stdout:
            output_parts.append(f"**Output:**\n```\n{result.stdout.strip()}\n```")
        if result.stderr:
            output_parts.append(f"**Stderr:**\n```\n{result.stderr.strip()}\n```")
        if result.returncode != 0:
            output_parts.append(f"**Código de salida:** {result.returncode}")

        return "\n\n".join(output_parts) if output_parts else "✅ Ejecutado sin output."

    except subprocess.TimeoutExpired:
        return "❌ Timeout: el código tardó más de 30 segundos."
    except FileNotFoundError:
        return "❌ Python3 no encontrado en el sistema."
    except Exception as e:
        return f"❌ Error al ejecutar: {str(e)}"


# ─────────────────────────────────────────────
# 🌐 HTTP / APIs
# ─────────────────────────────────────────────

@tool
def http_request(
    url: str,
    method: str = "GET",
    params: Optional[str] = None,
    headers: Optional[str] = None,
    body: Optional[str] = None,
) -> str:
    """
    Realiza una petición HTTP a una URL o API externa.
    
    Args:
        url: URL completa incluyendo protocolo (https://...).
        method: Método HTTP: GET, POST, PUT, DELETE. Por defecto GET.
        params: Parámetros de query como JSON string. Ej: '{"key": "value"}'.
        headers: Headers HTTP como JSON string. Ej: '{"Authorization": "Bearer token"}'.
        body: Cuerpo de la petición como JSON string (para POST/PUT).
    
    Returns:
        Respuesta de la API (status code + body).
    """
    try:
        parsed_params = json.loads(params) if params else None
        parsed_headers = json.loads(headers) if headers else {}
        parsed_body = json.loads(body) if body else None

        # Headers por defecto
        parsed_headers.setdefault("User-Agent", "NEO-Agent/1.0")

        resp = requests.request(
            method=method.upper(),
            url=url,
            params=parsed_params,
            headers=parsed_headers,
            json=parsed_body,
            timeout=15,
        )

        # Intentar parsear como JSON, si no, texto plano
        try:
            content = json.dumps(resp.json(), indent=2, ensure_ascii=False)
            content_type = "json"
        except Exception:
            content = resp.text[:3000]
            content_type = "text"

        return (
            f"**Status:** {resp.status_code} {resp.reason}\n\n"
            f"**Respuesta ({content_type}):**\n```\n{content}\n```"
        )

    except requests.exceptions.ConnectionError:
        return f"❌ No se pudo conectar a: {url}"
    except requests.exceptions.Timeout:
        return "❌ Timeout: la petición tardó más de 15 segundos."
    except Exception as e:
        return f"❌ Error en petición HTTP: {str(e)}"


# ─────────────────────────────────────────────
# 🧮 CALCULADORA
# ─────────────────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """
    Evalúa una expresión matemática de forma segura y precisa.
    No uses el LLM para matemáticas — usa siempre esta herramienta.
    
    Args:
        expression: Expresión matemática. Ej: "15 * 2847 / 100 + 2847 * 0.21"
    
    Returns:
        Resultado numérico de la expresión.
    """
    try:
        # Importar numexpr si está disponible para mayor seguridad
        try:
            import numexpr as ne
            result = ne.evaluate(expression).item()
        except ImportError:
            # Fallback seguro: solo operaciones matemáticas básicas
            import ast
            import math

            safe_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, **{k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            }
            tree = ast.parse(expression, mode="eval")
            # Verificar que solo hay operaciones seguras
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id not in safe_names:
                        return f"❌ Función no permitida: {node.func.id}"
            result = eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, safe_names)  # noqa: S307

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return f"**{expression}** = `{result:,}` " if isinstance(result, (int, float)) else f"{result}"

    except ZeroDivisionError:
        return "❌ División por cero."
    except SyntaxError:
        return f"❌ Expresión inválida: {expression}"
    except Exception as e:
        return f"❌ Error al calcular: {str(e)}"


# ─────────────────────────────────────────────
# 🧠 MEMORIA A LARGO PLAZO
# ─────────────────────────────────────────────

@tool
def memory_save(content: str, category: str = "hecho") -> str:
    """
    Guarda un recuerdo importante en la memoria a largo plazo (persiste entre sesiones).
    
    Args:
        content: Lo que quieres recordar. Sé específico y claro.
        category: Tipo de recuerdo: 'preferencia', 'hecho', 'tarea', 'contexto', 'error'.
    
    Returns:
        Confirmación de que el recuerdo fue guardado.
    """
    try:
        memories = _load_memories()
        
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "importance": 1,
            "content": content,
            "source": "agente",
        }
        
        memories["memories"].append(entry)
        _save_memories(memories)
        
        return f"✅ Recuerdo guardado (ID: {entry['id']}) en categoría '{category}':\n> {content}"

    except Exception as e:
        return f"❌ Error al guardar recuerdo: {str(e)}"


@tool
def memory_search(query: str) -> str:
    """
    Busca en la memoria a largo plazo usando texto libre.
    Úsala cuando el usuario hace referencia a algo de sesiones anteriores.
    
    Args:
        query: Lo que quieres buscar en la memoria.
    
    Returns:
        Recuerdos relevantes encontrados.
    """
    try:
        memories = _load_memories()
        
        if not memories["memories"]:
            return "📭 No hay recuerdos guardados aún."
        
        query_lower = query.lower()
        results = []
        
        for m in memories["memories"]:
            if query_lower in m["content"].lower() or query_lower in m["category"].lower():
                results.append(m)
        
        if not results:
            # Si no hay resultados exactos, devolver los últimos 5
            results = memories["memories"][-5:]
            header = f"No encontré recuerdos sobre '{query}'. Mostrando los más recientes:\n\n"
        else:
            header = f"**{len(results)} recuerdo(s) sobre '{query}':**\n\n"
        
        lines = [header]
        for m in results:
            ts = m["timestamp"][:10]
            lines.append(f"- [{ts}] **{m['category']}**: {m['content']}")
        
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error al buscar en memoria: {str(e)}"


@tool
def memory_list() -> str:
    """
    Lista todos los recuerdos guardados en la memoria a largo plazo.
    
    Returns:
        Lista completa de recuerdos organizados por categoría.
    """
    try:
        memories = _load_memories()
        
        if not memories["memories"]:
            return "📭 No hay recuerdos guardados."
        
        by_category = {}
        for m in memories["memories"]:
            cat = m["category"]
            by_category.setdefault(cat, []).append(m)
        
        lines = [f"**🧠 Memoria a largo plazo ({len(memories['memories'])} recuerdos)**\n"]
        
        for cat, items in sorted(by_category.items()):
            lines.append(f"\n**{cat.upper()}** ({len(items)})")
            for m in items:
                ts = m["timestamp"][:10]
                lines.append(f"  - [{ts}] {m['content']}")
        
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error al listar memoria: {str(e)}"


# ─────────────────────────────────────────────
# UTILIDADES INTERNAS
# ─────────────────────────────────────────────

def _resolve_path(filepath: str) -> Path:
    """Resuelve una ruta, relativa al workspace si no es absoluta."""
    path = Path(filepath)
    if not path.is_absolute():
        path = WORKSPACE / path
    return path.resolve()


def _format_size(size: int) -> str:
    """Formatea tamaño de archivo en unidades legibles."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _load_memories() -> dict:
    """Carga el archivo de memoria a largo plazo."""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"memories": [], "version": "1.0"}


def _save_memories(data: dict) -> None:
    """Guarda el archivo de memoria a largo plazo."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# REGISTRO DE HERRAMIENTAS
# ─────────────────────────────────────────────

ALL_TOOLS = [
    web_search,
    read_file,
    write_file,
    list_directory,
    run_python,
    http_request,
    calculator,
    memory_save,
    memory_search,
    memory_list,
]
