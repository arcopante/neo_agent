"""
tools.py — Herramientas del agente NEO

Cada herramienta es una función decorada con @tool de LangChain.
Añade nuevas herramientas aquí y se registrarán automáticamente.
"""

import json
import mimetypes
import os
import platform
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from langchain.tools import tool

# Directorio base para operaciones de archivo relativas
WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", str(Path(__file__).parent.parent / "workspace")))
WORKSPACE.mkdir(parents=True, exist_ok=True)

MEMORY_FILE = Path(__file__).parent.parent / "memory" / "long_term.json"
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

# Token de Telegram (para send_telegram_file)
_TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


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
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(f"**{r['title']}**\n{r['href']}\n{r['body']}\n")

        return "\n---\n".join(results) if results else "No se encontraron resultados."

    except ImportError:
        return "❌ Instala el paquete de búsqueda: pip install ddgs"
    except Exception as e:
        return f"❌ Error al buscar: {str(e)}"


# ─────────────────────────────────────────────
# 💻 SISTEMA
# ─────────────────────────────────────────────

@tool
def system_info() -> str:
    """
    Devuelve información completa del sistema: OS, CPU, RAM, disco, Python, red y entorno.
    Úsala cuando el usuario pregunte por el sistema, recursos, o el entorno de ejecución.

    Returns:
        Informe detallado del sistema.
    """
    try:
        import socket
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False

        lines = ["**💻 Información del sistema**\n"]

        # OS y máquina
        lines.append(f"**Sistema operativo:** {platform.system()} {platform.release()} ({platform.version()})")
        lines.append(f"**Arquitectura:** {platform.machine()}")
        lines.append(f"**Hostname:** {socket.gethostname()}")
        lines.append(f"**Usuario:** {os.getenv('USER') or os.getenv('USERNAME', 'desconocido')}")
        lines.append(f"**Directorio home:** {Path.home()}")
        lines.append(f"**Python:** {platform.python_version()} — {platform.python_implementation()}")
        lines.append(f"**Workspace NEO:** {WORKSPACE}")

        # IP local
        try:
            ip = socket.gethostbyname(socket.gethostname())
            lines.append(f"**IP local:** {ip}")
        except Exception:
            pass

        if has_psutil:
            # CPU
            cpu_count = psutil.cpu_count(logical=True)
            cpu_phys = psutil.cpu_count(logical=False)
            cpu_pct = psutil.cpu_percent(interval=0.5)
            lines.append(f"\n**CPU:** {cpu_phys} físicos / {cpu_count} lógicos — uso actual: {cpu_pct}%")

            # RAM
            mem = psutil.virtual_memory()
            lines.append(
                f"**RAM:** {_fmt_size(mem.total)} total — "
                f"{_fmt_size(mem.available)} disponible — {mem.percent}% en uso"
            )

            # Disco
            disk = psutil.disk_usage("/")
            lines.append(
                f"**Disco (/):** {_fmt_size(disk.total)} total — "
                f"{_fmt_size(disk.free)} libre — {disk.percent}% en uso"
            )

            # Procesos
            lines.append(f"**Procesos activos:** {len(psutil.pids())}")
        else:
            lines.append("\n_Instala psutil para info de CPU/RAM/disco: pip install psutil_")

        # Variables de entorno relevantes
        path_dirs = len(os.getenv("PATH", "").split(":"))
        lines.append(f"\n**PATH:** {path_dirs} directorios")
        lines.append(f"**SHELL:** {os.getenv('SHELL', 'desconocido')}")
        lang = os.getenv("LANG") or os.getenv("LANGUAGE", "desconocido")
        lines.append(f"**Idioma:** {lang}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error al obtener info del sistema: {str(e)}"


@tool
def run_command(command: str, timeout: int = 30) -> str:
    """
    Ejecuta un comando de shell en el sistema y devuelve su salida.
    Úsala para operaciones del sistema que no tienen herramienta específica.
    IMPORTANTE: Confirma con el usuario antes de ejecutar comandos destructivos.

    Args:
        command: Comando shell a ejecutar. Ej: "ls -la ~/Desktop", "df -h", "ps aux"
        timeout: Tiempo máximo de espera en segundos (default: 30).

    Returns:
        Stdout y stderr del comando, o mensaje de error.
    """
    # Comandos bloqueados por seguridad
    blocked = ["rm -rf /", "mkfs", "dd if=", ":(){:|:&};:", "chmod 777 /"]
    for b in blocked:
        if b in command:
            return f"❌ Comando bloqueado por seguridad: contiene '{b}'"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE),
        )

        parts = []
        if result.stdout.strip():
            parts.append(f"```\n{result.stdout.strip()}\n```")
        if result.stderr.strip():
            parts.append(f"**Stderr:**\n```\n{result.stderr.strip()}\n```")
        if result.returncode != 0:
            parts.append(f"**Código de salida:** {result.returncode}")

        return "\n\n".join(parts) if parts else "✅ Comando ejecutado sin output."

    except subprocess.TimeoutExpired:
        return f"❌ Timeout: el comando tardó más de {timeout} segundos."
    except Exception as e:
        return f"❌ Error al ejecutar comando: {str(e)}"


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

        return f"📄 **{path.name}** ({lines} líneas, {_fmt_size(size)})\n\n```\n{content}\n```"

    except PermissionError:
        return f"❌ Sin permisos para leer: {filepath}"
    except Exception as e:
        return f"❌ Error al leer archivo: {str(e)}"


@tool
def write_file(filepath: str, content: str, mode: str = "write") -> str:
    """
    Escribe contenido en un archivo. Crea el archivo si no existe.
    IMPORTANTE: Puede sobreescribir datos. Confirma con el usuario antes de usar.

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
        return f"✅ Contenido {action} **{path}** ({_fmt_size(path.stat().st_size)})"

    except PermissionError:
        return f"❌ Sin permisos para escribir en: {filepath}"
    except Exception as e:
        return f"❌ Error al escribir archivo: {str(e)}"


@tool
def file_info(filepath: str) -> str:
    """
    Devuelve metadatos detallados de un archivo o directorio: tamaño, fechas, permisos y tipo.

    Args:
        filepath: Ruta al archivo o directorio.

    Returns:
        Metadatos del archivo.
    """
    try:
        path = _resolve_path(filepath)
        if not path.exists():
            return f"❌ No existe: {path}"

        stat = path.stat()
        mime, _ = mimetypes.guess_type(str(path))
        created  = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        accessed = datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")
        perms = oct(stat.st_mode)[-3:]

        lines = [
            f"**📄 {path.name}**",
            f"**Ruta completa:** {path}",
            f"**Tipo:** {'Directorio' if path.is_dir() else 'Archivo'}",
            f"**Tamaño:** {_fmt_size(stat.st_size)}",
            f"**MIME:** {mime or 'desconocido'}",
            f"**Permisos:** {perms}",
            f"**Creado:** {created}",
            f"**Modificado:** {modified}",
            f"**Último acceso:** {accessed}",
        ]
        if path.is_dir():
            n = len(list(path.iterdir()))
            lines.append(f"**Contenido:** {n} elementos")

        return "\n".join(lines)

    except PermissionError:
        return f"❌ Sin permisos para acceder a: {filepath}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def list_directory(dirpath: str = ".") -> str:
    """
    Lista el contenido de cualquier directorio del sistema con tamaños y tipos.
    Puede explorar rutas absolutas fuera del workspace (ej: ~/Desktop, /tmp).

    Args:
        dirpath: Ruta del directorio. '.' usa el workspace. Soporta ~ para home.

    Returns:
        Listado de archivos y carpetas con metadatos.
    """
    try:
        path = _resolve_path(dirpath)
        if not path.exists():
            return f"❌ El directorio no existe: {path}"
        if not path.is_dir():
            return f"❌ La ruta no es un directorio: {path}"

        lines = [f"📂 **{path}**\n"]
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

        dirs = [i for i in items if i.is_dir()]
        files = [i for i in items if i.is_file()]

        for item in dirs:
            try:
                count = len(list(item.iterdir()))
                lines.append(f"  📁 {item.name}/  ({count} elementos)")
            except PermissionError:
                lines.append(f"  📁 {item.name}/  (sin acceso)")

        for item in files:
            size = _fmt_size(item.stat().st_size)
            modified = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"  📄 {item.name}  {size}  {modified}")

        if not items:
            lines.append("  (directorio vacío)")

        lines.append(f"\n**Total:** {len(dirs)} carpetas, {len(files)} archivos")
        return "\n".join(lines)

    except PermissionError:
        return f"❌ Sin permisos para listar: {dirpath}"
    except Exception as e:
        return f"❌ Error al listar directorio: {str(e)}"


@tool
def find_files(pattern: str, search_path: str = "~", max_results: int = 20) -> str:
    """
    Busca archivos por nombre o extensión en el sistema de archivos.

    Args:
        pattern: Patrón de búsqueda. Ej: '*.py', 'config.json', '*.pdf', 'notas*'
        search_path: Directorio donde buscar. Por defecto el home del usuario.
        max_results: Número máximo de resultados (default: 20).

    Returns:
        Lista de rutas encontradas con tamaños.
    """
    try:
        base = Path(search_path).expanduser().resolve()
        if not base.exists():
            return f"❌ El directorio de búsqueda no existe: {search_path}"

        results = []
        try:
            for match in base.rglob(pattern):
                if match.is_file():
                    results.append(match)
                    if len(results) >= max_results:
                        break
        except PermissionError:
            pass

        if not results:
            return f"No se encontraron archivos con el patrón '{pattern}' en {base}"

        lines = [f"**🔍 {len(results)} resultado(s) para '{pattern}' en {base}:**\n"]
        for f in results:
            try:
                size = _fmt_size(f.stat().st_size)
                lines.append(f"  📄 {f}  ({size})")
            except Exception:
                lines.append(f"  📄 {f}")

        if len(results) == max_results:
            lines.append(f"\n_Mostrando los primeros {max_results} resultados._")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error al buscar archivos: {str(e)}"


@tool
def copy_file(source: str, destination: str) -> str:
    """
    Copia un archivo o directorio a otra ubicación.

    Args:
        source: Ruta del archivo o directorio origen.
        destination: Ruta de destino.

    Returns:
        Confirmación de la copia o mensaje de error.
    """
    try:
        src = _resolve_path(source)
        dst = _resolve_path(destination)

        if not src.exists():
            return f"❌ El origen no existe: {src}"

        if src.is_dir():
            shutil.copytree(src, dst)
            return f"✅ Directorio copiado: {src} → {dst}"
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return f"✅ Archivo copiado: {src} → {dst} ({_fmt_size(dst.stat().st_size)})"

    except PermissionError:
        return f"❌ Sin permisos para copiar."
    except Exception as e:
        return f"❌ Error al copiar: {str(e)}"


@tool
def move_file(source: str, destination: str) -> str:
    """
    Mueve o renombra un archivo o directorio.

    Args:
        source: Ruta del archivo o directorio origen.
        destination: Ruta de destino.

    Returns:
        Confirmación del movimiento o mensaje de error.
    """
    try:
        src = _resolve_path(source)
        dst = _resolve_path(destination)

        if not src.exists():
            return f"❌ El origen no existe: {src}"

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"✅ Movido: {src} → {dst}"

    except PermissionError:
        return f"❌ Sin permisos para mover."
    except Exception as e:
        return f"❌ Error al mover: {str(e)}"


@tool
def delete_file(filepath: str) -> str:
    """
    Elimina un archivo o directorio vacío.
    IMPORTANTE: Esta acción es irreversible. Confirma siempre con el usuario antes de usar.

    Args:
        filepath: Ruta del archivo o directorio a eliminar.

    Returns:
        Confirmación de eliminación o mensaje de error.
    """
    try:
        path = _resolve_path(filepath)

        if not path.exists():
            return f"❌ No existe: {path}"

        if path.is_dir():
            if any(path.iterdir()):
                return f"❌ El directorio no está vacío: {path}. Usa run_command con 'rm -rf' si estás seguro."
            path.rmdir()
            return f"✅ Directorio eliminado: {path}"
        else:
            size = _fmt_size(path.stat().st_size)
            path.unlink()
            return f"✅ Archivo eliminado: {path} ({size})"

    except PermissionError:
        return f"❌ Sin permisos para eliminar: {filepath}"
    except Exception as e:
        return f"❌ Error al eliminar: {str(e)}"


@tool
def compress_files(source: str, output: str = "", format: str = "zip") -> str:
    """
    Comprime un archivo o directorio en un archivo zip o tar.gz.

    Args:
        source: Ruta del archivo o directorio a comprimir.
        output: Ruta del archivo de salida (sin extensión). Si vacío, usa el nombre del origen.
        format: Formato de compresión: 'zip' o 'tar.gz'. Por defecto 'zip'.

    Returns:
        Confirmación con la ruta del archivo comprimido.
    """
    try:
        src = _resolve_path(source)
        if not src.exists():
            return f"❌ No existe: {src}"

        out_name = output if output else str(WORKSPACE / src.stem)
        out_path = _resolve_path(out_name)

        fmt = "gztar" if format == "tar.gz" else "zip"
        result = shutil.make_archive(str(out_path), fmt, str(src.parent), src.name)
        size = _fmt_size(Path(result).stat().st_size)

        return f"✅ Comprimido: {result} ({size})"

    except Exception as e:
        return f"❌ Error al comprimir: {str(e)}"


@tool
def extract_archive(filepath: str, destination: str = "") -> str:
    """
    Extrae un archivo comprimido (.zip, .tar.gz, .tar.bz2, etc.).

    Args:
        filepath: Ruta del archivo comprimido.
        destination: Directorio de destino. Si vacío, extrae junto al archivo.

    Returns:
        Confirmación de extracción o mensaje de error.
    """
    try:
        path = _resolve_path(filepath)
        if not path.exists():
            return f"❌ No existe: {path}"

        dst = _resolve_path(destination) if destination else path.parent / path.stem
        dst.mkdir(parents=True, exist_ok=True)

        shutil.unpack_archive(str(path), str(dst))
        items = len(list(dst.rglob("*")))
        return f"✅ Extraído en {dst} ({items} elementos)"

    except Exception as e:
        return f"❌ Error al extraer: {str(e)}"


# ─────────────────────────────────────────────
# 📤 TELEGRAM
# ─────────────────────────────────────────────

@tool
def send_telegram_file(filepath: str, caption: str = "", chat_id: str = "") -> str:
    """
    Envía un archivo al chat de Telegram activo.
    Útil para compartir documentos, imágenes, logs o cualquier archivo generado.

    Args:
        filepath: Ruta del archivo a enviar.
        caption: Texto descriptivo que acompañará al archivo (opcional).
        chat_id: ID del chat destino. Si vacío, usa TELEGRAM_ALLOWED_USERS.

    Returns:
        Confirmación de envío o mensaje de error.
    """
    token = _TELEGRAM_TOKEN
    if not token:
        return "❌ TELEGRAM_BOT_TOKEN no configurado en settings.cfg"

    try:
        path = _resolve_path(filepath)
        if not path.exists():
            return f"❌ El archivo no existe: {path}"
        if not path.is_file():
            return f"❌ La ruta no es un archivo: {path}"

        # Determinar chat_id destino
        target = chat_id
        if not target:
            allowed = os.getenv("TELEGRAM_ALLOWED_USERS", "").strip()
            if allowed:
                target = allowed.split(",")[0].strip()
        if not target:
            return "❌ No se pudo determinar el chat de destino. Proporciona chat_id o configura TELEGRAM_ALLOWED_USERS."

        size = _fmt_size(path.stat().st_size)
        url = f"https://api.telegram.org/bot{token}/sendDocument"

        with open(path, "rb") as f:
            resp = requests.post(
                url,
                data={"chat_id": target, "caption": caption or f"📎 {path.name}"},
                files={"document": (path.name, f)},
                timeout=60,
            )

        if resp.status_code == 200:
            return f"✅ Archivo enviado por Telegram: **{path.name}** ({size})"
        else:
            return f"❌ Error al enviar: {resp.status_code} — {resp.text[:200]}"

    except Exception as e:
        return f"❌ Error al enviar archivo por Telegram: {str(e)}"


# ─────────────────────────────────────────────
# 📋 PORTAPAPELES
# ─────────────────────────────────────────────

@tool
def clipboard_get() -> str:
    """
    Lee el contenido actual del portapapeles del sistema.

    Returns:
        Texto que hay en el portapapeles.
    """
    try:
        result = subprocess.run(
            ["pbpaste"] if platform.system() == "Darwin"
            else ["xclip", "-selection", "clipboard", "-o"] if platform.system() == "Linux"
            else ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        content = result.stdout.strip()
        if not content:
            return "📋 El portapapeles está vacío."
        return f"📋 **Contenido del portapapeles:**\n```\n{content}\n```"
    except FileNotFoundError:
        return "❌ No se encontró el comando del portapapeles (pbpaste/xclip/powershell)."
    except Exception as e:
        return f"❌ Error al leer el portapapeles: {str(e)}"


@tool
def clipboard_set(text: str) -> str:
    """
    Copia texto al portapapeles del sistema.

    Args:
        text: Texto a copiar al portapapeles.

    Returns:
        Confirmación de que el texto fue copiado.
    """
    try:
        if platform.system() == "Darwin":
            subprocess.run(["pbcopy"], input=text, text=True, timeout=5)
        elif platform.system() == "Linux":
            subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, timeout=5)
        else:
            subprocess.run(["powershell", "-command", f"Set-Clipboard '{text}'"], timeout=5)
        preview = text[:80] + "..." if len(text) > 80 else text
        return f"✅ Copiado al portapapeles:\n```\n{preview}\n```"
    except FileNotFoundError:
        return "❌ No se encontró el comando del portapapeles (pbcopy/xclip/powershell)."
    except Exception as e:
        return f"❌ Error al escribir en el portapapeles: {str(e)}"


# ─────────────────────────────────────────────
# 🌐 NAVEGADOR
# ─────────────────────────────────────────────

@tool
def open_url(url: str) -> str:
    """
    Abre una URL en el navegador predeterminado del sistema.

    Args:
        url: URL a abrir. Debe incluir protocolo (https://...).

    Returns:
        Confirmación de apertura o mensaje de error.
    """
    try:
        import webbrowser
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"✅ Abierto en el navegador: {url}"
    except Exception as e:
        return f"❌ Error al abrir URL: {str(e)}"


# ─────────────────────────────────────────────
# 🐍 EJECUCIÓN DE CÓDIGO
# ─────────────────────────────────────────────

@tool
def run_python(code: str) -> str:
    """
    Ejecuta un fragmento de código Python y devuelve el output.
    IMPORTANTE: Requiere confirmación del usuario antes de ejecutar.
    Timeout: 30 segundos.

    Args:
        code: Código Python a ejecutar.

    Returns:
        Stdout y stderr del proceso, o mensaje de error.
    """
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=30, cwd=str(WORKSPACE),
        )

        parts = []
        if result.stdout:
            parts.append(f"**Output:**\n```\n{result.stdout.strip()}\n```")
        if result.stderr:
            parts.append(f"**Stderr:**\n```\n{result.stderr.strip()}\n```")
        if result.returncode != 0:
            parts.append(f"**Código de salida:** {result.returncode}")

        return "\n\n".join(parts) if parts else "✅ Ejecutado sin output."

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
        headers: Headers HTTP como JSON string.
        body: Cuerpo de la petición como JSON string (para POST/PUT).

    Returns:
        Respuesta de la API (status code + body).
    """
    try:
        parsed_params   = json.loads(params)  if params  else None
        parsed_headers  = json.loads(headers) if headers else {}
        parsed_body     = json.loads(body)    if body    else None

        parsed_headers.setdefault("User-Agent", "NEO-Agent/1.0")

        resp = requests.request(
            method=method.upper(), url=url,
            params=parsed_params, headers=parsed_headers,
            json=parsed_body, timeout=15,
        )

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
        try:
            import numexpr as ne
            result = ne.evaluate(expression).item()
        except ImportError:
            import ast
            import math
            safe_names = {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow,
                **{k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            }
            tree = ast.parse(expression, mode="eval")
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id not in safe_names:
                        return f"❌ Función no permitida: {node.func.id}"
            result = eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, safe_names)  # noqa: S307

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        return f"**{expression}** = `{result:,}`" if isinstance(result, (int, float)) else str(result)

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
            "content": content,
        }
        memories["memories"].append(entry)
        _save_memories(memories)
        return f"✅ Recuerdo guardado (ID: {entry['id']}) en '{category}':\n> {content}"
    except Exception as e:
        return f"❌ Error al guardar recuerdo: {str(e)}"


@tool
def memory_search(query: str) -> str:
    """
    Busca en la memoria a largo plazo usando texto libre.

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
        results = [m for m in memories["memories"]
                   if query_lower in m["content"].lower() or query_lower in m["category"].lower()]

        if not results:
            results = memories["memories"][-5:]
            header = f"No encontré recuerdos sobre '{query}'. Mostrando los más recientes:\n\n"
        else:
            header = f"**{len(results)} recuerdo(s) sobre '{query}':**\n\n"

        lines = [header]
        for m in results:
            lines.append(f"- [{m['timestamp'][:10]}] **{m['category']}**: {m['content']}")
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
            by_category.setdefault(m["category"], []).append(m)

        lines = [f"**🧠 Memoria a largo plazo ({len(memories['memories'])} recuerdos)**\n"]
        for cat, items in sorted(by_category.items()):
            lines.append(f"\n**{cat.upper()}** ({len(items)})")
            for m in items:
                lines.append(f"  - [{m['timestamp'][:10]}] {m['content']}")
        return "\n".join(lines)

    except Exception as e:
        return f"❌ Error al listar memoria: {str(e)}"


# ─────────────────────────────────────────────
# UTILIDADES INTERNAS
# ─────────────────────────────────────────────

def _resolve_path(filepath: str) -> Path:
    """Resuelve una ruta: expande ~, y si es relativa la sitúa en el workspace."""
    path = Path(filepath).expanduser()
    if not path.is_absolute():
        path = WORKSPACE / path
    return path.resolve()


def _fmt_size(size: int) -> str:
    """Formatea tamaño de archivo en unidades legibles."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _load_memories() -> dict:
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"memories": [], "version": "1.0"}


def _save_memories(data: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# REGISTRO DE HERRAMIENTAS
# ─────────────────────────────────────────────

ALL_TOOLS = [
    # Sistema
    system_info,
    run_command,
    # Archivos
    read_file,
    write_file,
    file_info,
    list_directory,
    find_files,
    copy_file,
    move_file,
    delete_file,
    compress_files,
    extract_archive,
    # Telegram
    send_telegram_file,
    # Portapapeles
    clipboard_get,
    clipboard_set,
    # Navegador
    open_url,
    # Red y código
    web_search,
    http_request,
    run_python,
    calculator,
    # Memoria
    memory_save,
    memory_search,
    memory_list,
]
