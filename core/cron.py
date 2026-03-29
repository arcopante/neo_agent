"""
cron.py — Sistema de tareas programadas de NEO

Soporta tres tipos de tareas:
  notify  → Notificación de texto fijo
  llm     → El LLM genera el mensaje dinámicamente
  shell   → Ejecuta un comando o script

Formatos de horario:
  HH:MM   → Hora exacta diaria        (ej: 09:00)
  */Nm    → Cada N minutos            (ej: */30m)
  */Nh    → Cada N horas              (ej: */2h)
"""

import asyncio
import json
import logging
import os
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("neo.cron")

CRON_FILE = Path(__file__).parent.parent / "memory" / "crons.json"


# ── Persistencia ──────────────────────────────────────────────────────────────

def _load_crons() -> list:
    if CRON_FILE.exists():
        try:
            return json.loads(CRON_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_crons(crons: list) -> None:
    CRON_FILE.parent.mkdir(parents=True, exist_ok=True)
    CRON_FILE.write_text(json.dumps(crons, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Parsing de horario ────────────────────────────────────────────────────────

def parse_schedule(schedule: str) -> dict:
    """
    Parsea el horario y devuelve un dict con tipo e intervalo.
    Lanza ValueError si el formato no es válido.

    Retorna:
        {"type": "daily", "hour": 9, "minute": 0}
        {"type": "interval", "seconds": 3600}
    """
    s = schedule.strip()

    # Intervalo: */Nm o */Nh
    if s.startswith("*/"):
        val = s[2:]
        if val.endswith("m"):
            minutes = int(val[:-1])
            if minutes < 1:
                raise ValueError("El intervalo mínimo es 1 minuto")
            return {"type": "interval", "seconds": minutes * 60}
        elif val.endswith("h"):
            hours = int(val[:-1])
            if hours < 1:
                raise ValueError("El intervalo mínimo es 1 hora")
            return {"type": "interval", "seconds": hours * 3600}
        else:
            raise ValueError("Formato de intervalo inválido. Usa */Nm o */Nh (ej: */30m, */2h)")

    # Hora exacta: HH:MM
    if ":" in s:
        parts = s.split(":")
        if len(parts) != 2:
            raise ValueError("Formato de hora inválido. Usa HH:MM (ej: 09:00)")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Hora fuera de rango. Hora: 0-23, Minuto: 0-59")
        return {"type": "daily", "hour": hour, "minute": minute}

    raise ValueError("Formato de horario inválido. Usa HH:MM, */Nm o */Nh")


def parse_cron_command(text: str) -> tuple[str, str]:
    """
    Parsea el tipo y contenido del comando cron.
    Retorna (tipo, contenido): tipo = 'notify' | 'llm' | 'shell'
    """
    t = text.strip()
    if t.lower().startswith("llm:"):
        return "llm", t[4:].strip()
    elif t.lower().startswith("shell:"):
        return "shell", t[6:].strip()
    else:
        return "notify", t


def schedule_description(schedule: dict) -> str:
    """Descripción legible del horario."""
    if schedule["type"] == "daily":
        return f"{schedule['hour']:02d}:{schedule['minute']:02d} diario"
    else:
        secs = schedule["seconds"]
        if secs < 3600:
            return f"cada {secs // 60} minuto(s)"
        else:
            return f"cada {secs // 3600} hora(s)"


def type_icon(task_type: str) -> str:
    return {"notify": "🔔", "llm": "🤖", "shell": "⚙️"}.get(task_type, "📌")


# ── Gestión de tareas ─────────────────────────────────────────────────────────

def cron_add(schedule_str: str, command: str) -> dict:
    """
    Añade una nueva tarea cron.
    Retorna el dict de la tarea creada o lanza ValueError.
    """
    schedule = parse_schedule(schedule_str)
    task_type, content = parse_cron_command(command)

    task = {
        "id": str(uuid.uuid4())[:6].upper(),
        "schedule_str": schedule_str,
        "schedule": schedule,
        "type": task_type,
        "content": content,
        "created": datetime.now().isoformat(),
        "last_run": None,
        "run_count": 0,
    }

    crons = _load_crons()
    crons.append(task)
    _save_crons(crons)
    return task


def cron_list() -> list:
    return _load_crons()


def cron_delete(task_id: str) -> bool:
    """Elimina una tarea por ID. Retorna True si se eliminó."""
    crons = _load_crons()
    new = [c for c in crons if c["id"].upper() != task_id.upper()]
    if len(new) == len(crons):
        return False
    _save_crons(new)
    return True


def cron_clear() -> int:
    """Elimina todas las tareas. Retorna el número eliminado."""
    crons = _load_crons()
    _save_crons([])
    return len(crons)


# ── Motor de ejecución ────────────────────────────────────────────────────────

def _should_run(task: dict, now: datetime) -> bool:
    """Decide si una tarea debe ejecutarse ahora."""
    schedule = task["schedule"]
    last_run = datetime.fromisoformat(task["last_run"]) if task["last_run"] else None

    if schedule["type"] == "daily":
        target = now.replace(hour=schedule["hour"], minute=schedule["minute"],
                             second=0, microsecond=0)
        # Ejecutar si estamos dentro del minuto objetivo y no se ha ejecutado hoy
        if now.hour == schedule["hour"] and now.minute == schedule["minute"]:
            if last_run is None or last_run.date() < now.date():
                return True
        return False

    elif schedule["type"] == "interval":
        if last_run is None:
            return True
        elapsed = (now - last_run).total_seconds()
        return elapsed >= schedule["seconds"]

    return False


async def _execute_task(task: dict, send_fn, agent=None) -> str:
    """
    Ejecuta una tarea y devuelve el mensaje resultante.
    send_fn(text) es la función para enviar el mensaje al usuario.
    """
    task_type = task["type"]
    content = task["content"]

    try:
        if task_type == "notify":
            message = content

        elif task_type == "llm":
            if agent is None:
                message = f"⚠️ Agente no disponible para ejecutar: {content}"
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: agent.invoke({"input": content})
                )
                message = result.get("output", "Sin respuesta.")

        elif task_type == "shell":
            expanded = os.path.expanduser(content)
            result = subprocess.run(
                expanded, shell=True, capture_output=True,
                text=True, timeout=60
            )
            output = result.stdout.strip() or result.stderr.strip() or "(sin output)"
            message = f"⚙️ `{content}`\n```\n{output[:1000]}\n```"

        else:
            message = f"Tipo de tarea desconocido: {task_type}"

        icon = type_icon(task_type)
        full_message = f"{icon} **Cron [{task['id']}]** `{task['schedule_str']}`\n\n{message}"
        await send_fn(full_message)
        return message

    except subprocess.TimeoutExpired:
        err = f"❌ Timeout al ejecutar: {content}"
        await send_fn(err)
        return err
    except Exception as e:
        err = f"❌ Error en cron [{task['id']}]: {str(e)}"
        await send_fn(err)
        return err


async def cron_loop(send_fn, get_agent_fn, stop_event: "threading.Event" = None):
    """
    Bucle principal del scheduler. Comprueba cada 30 segundos.
    send_fn(text)     → envía mensaje al usuario
    get_agent_fn()    → devuelve el agente activo (o None)
    stop_event        → threading.Event para detener el bucle
    """
    import threading
    logger.info("⏰ Scheduler de crons iniciado")

    while True:
        if stop_event and stop_event.is_set():
            break

        try:
            now = datetime.now()
            crons = _load_crons()
            updated = False

            for task in crons:
                if _should_run(task, now):
                    logger.info(f"⏰ Ejecutando cron [{task['id']}]: {task['content'][:50]}")
                    agent = get_agent_fn() if get_agent_fn else None
                    await _execute_task(task, send_fn, agent)
                    task["last_run"] = now.isoformat()
                    task["run_count"] = task.get("run_count", 0) + 1
                    updated = True

            if updated:
                _save_crons(crons)

        except Exception as e:
            logger.error(f"Error en cron_loop: {e}", exc_info=True)

        # Esperar 30 segundos entre comprobaciones
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            break

    logger.info("⏰ Scheduler de crons detenido")
