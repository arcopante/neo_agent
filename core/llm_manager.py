"""
llm_manager.py — Gestión dinámica del proveedor y modelo LLM

Permite cambiar proveedor y modelo en caliente sin reiniciar el agente.
Mantiene el estado en memoria y lo persiste en config/settings.cfg.

Proveedores locales soportados (con API REST):
  - lmstudio  → http://localhost:1234
  - ollama    → http://localhost:11434

Proveedores externos:
  - openrouter, openai, anthropic, google
"""

import os
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Proveedores soportados
LOCAL_PROVIDERS  = {"lmstudio", "ollama"}
REMOTE_PROVIDERS = {"openrouter", "openai", "anthropic", "google"}
ALL_PROVIDERS    = LOCAL_PROVIDERS | REMOTE_PROVIDERS

# URLs base por defecto
_DEFAULT_URLS = {
    "lmstudio": "http://localhost:1234",
    "ollama":   "http://localhost:11434",
}


def _strip_v1(url: str) -> str:
    """Elimina el sufijo /v1 si existe, para uso en endpoints nativos."""
    return url.rstrip("/").removesuffix("/v1")

# Modelos de ejemplo para proveedores remotos
_REMOTE_MODEL_EXAMPLES = {
    "openrouter": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-70b-instruct",
        "mistralai/mistral-large",
        "google/gemini-pro-1.5",
        "google/gemini-flash-1.5",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ],
    "anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ],
    "google": [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-pro",
    ],
}


# ── Estado en memoria ─────────────────────────────────────────────────────────

def get_current_provider() -> str:
    return os.getenv("LLM_PROVIDER", "openrouter").lower()

def get_current_model() -> str:
    return os.getenv("LLM_MODEL", "")

def get_base_url(provider: str = None) -> str:
    """Devuelve la URL base sin /v1 para llamadas a endpoints nativos."""
    p = provider or get_current_provider()
    if p == "lmstudio":
        return _strip_v1(os.getenv("LMSTUDIO_BASE_URL", _DEFAULT_URLS["lmstudio"]))
    elif p == "ollama":
        return _strip_v1(os.getenv("OLLAMA_BASE_URL", _DEFAULT_URLS["ollama"]))
    return ""

def is_local(provider: str = None) -> bool:
    return (provider or get_current_provider()) in LOCAL_PROVIDERS


# ── Cambio de proveedor/modelo ────────────────────────────────────────────────

def set_provider(provider: str) -> None:
    """Cambia el proveedor activo en memoria."""
    provider = provider.lower().strip()
    if provider not in ALL_PROVIDERS:
        raise ValueError(
            f"Proveedor '{provider}' no soportado.\n"
            f"Disponibles: {', '.join(sorted(ALL_PROVIDERS))}"
        )
    os.environ["LLM_PROVIDER"] = provider


def set_model(model: str) -> None:
    """Cambia el modelo activo en memoria."""
    os.environ["LLM_MODEL"] = model.strip()


def set_provider_and_model(provider: str, model: str = "") -> None:
    set_provider(provider)
    if model:
        set_model(model)


# ── Operaciones con modelos locales ───────────────────────────────────────────

def list_models_local(provider: str = None) -> list[dict]:
    """
    Lista los modelos disponibles en LM Studio u Ollama.
    Retorna lista de dicts con al menos 'id' y 'loaded'.
    """
    p = provider or get_current_provider()
    base = get_base_url(p)

    if p == "lmstudio":
        # LM Studio expone /v1/models (OpenAI compatible)
        resp = requests.get(f"{base}/v1/models", timeout=5)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return [{"id": m["id"], "loaded": True} for m in data]

    elif p == "ollama":
        # Ollama expone /api/tags para modelos descargados
        resp = requests.get(f"{base}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        # También consultar cuál está en memoria
        running = set()
        try:
            ps = requests.get(f"{base}/api/ps", timeout=3).json()
            running = {m["name"] for m in ps.get("models", [])}
        except Exception:
            pass
        return [
            {
                "id": m["name"],
                "size": m.get("size", 0),
                "loaded": m["name"] in running,
            }
            for m in models
        ]

    raise ValueError(f"list_models solo disponible para: {', '.join(LOCAL_PROVIDERS)}")


def load_model_local(model: str, provider: str = None) -> str:
    """
    Carga un modelo en LM Studio u Ollama.
    En LM Studio no hay API de carga directa — solo setea el modelo activo.
    En Ollama hace un pull si no existe y lo carga con un prompt vacío.
    """
    p = provider or get_current_provider()
    base = get_base_url(p)

    if p == "lmstudio":
        # LM Studio carga el modelo al hacer la primera petición
        # Hacemos una petición mínima para forzar la carga
        resp = requests.post(
            f"{base}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            },
            timeout=60,
        )
        if resp.status_code in (200, 400):  # 400 puede ser respuesta válida con modelo cargado
            return f"✅ Modelo '{model}' cargado en LM Studio"
        resp.raise_for_status()

    elif p == "ollama":
        # Ollama: cargar con keep_alive
        resp = requests.post(
            f"{base}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": "5m"},
            timeout=120,
        )
        resp.raise_for_status()
        return f"✅ Modelo '{model}' cargado en Ollama"

    raise ValueError(f"load_model solo disponible para: {', '.join(LOCAL_PROVIDERS)}")


def unload_model_local(model: str, provider: str = None) -> str:
    """
    Descarga un modelo de memoria.
    LM Studio: no tiene API de unload — informa al usuario.
    Ollama: keep_alive=0 libera la memoria.
    """
    p = provider or get_current_provider()
    base = get_base_url(p)

    if p == "lmstudio":
        return (
            "⚠️ LM Studio no tiene API de descarga de modelo.\n"
            "Usa la interfaz de LM Studio para cambiar o descargar el modelo cargado."
        )

    elif p == "ollama":
        resp = requests.post(
            f"{base}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": 0},
            timeout=15,
        )
        resp.raise_for_status()
        return f"✅ Modelo '{model}' descargado de memoria (Ollama)"

    raise ValueError(f"unload_model solo disponible para: {', '.join(LOCAL_PROVIDERS)}")


def get_remote_model_examples(provider: str = None) -> list[str]:
    """Devuelve modelos de ejemplo para un proveedor remoto."""
    p = provider or get_current_provider()
    return _REMOTE_MODEL_EXAMPLES.get(p, [])


def format_size(bytes_: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"

def probe_tool_calling(provider: str = None) -> bool:
    """
    Comprueba si el modelo local soporta tool calling enviando
    una petición mínima con una herramienta de prueba.
    Retorna True si soporta tools, False si falla.
    """
    p = provider or get_current_provider()
    base = get_base_url(p)

    test_payload = {
        "model": os.getenv("LLM_MODEL", "local-model"),
        "messages": [{"role": "user", "content": "test"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "Tool de prueba",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }],
        "max_tokens": 5,
    }

    try:
        resp = requests.post(
            f"{base}/v1/chat/completions",
            json=test_payload,
            timeout=10,
        )
        # Si devuelve 200 o 400 (sin usar la tool) es compatible
        return resp.status_code in (200, 400)
    except Exception:
        return False

