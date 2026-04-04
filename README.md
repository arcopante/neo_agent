<div align="center">

# 🤖 NEO

### Agente de IA personal con ejecución real de acciones

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C?logo=chainlink&logoColor=white)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct-FF6B35)](https://langchain-ai.github.io/langgraph)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-compatible-6366F1)](https://openrouter.ai)
[![macOS](https://img.shields.io/badge/macOS-primary-000000?logo=apple&logoColor=white)](https://www.apple.com/macos)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

</div>

---

NEO es un agente de IA personal que entiende lenguaje natural y ejecuta acciones reales: busca en internet, gestiona archivos, analiza imágenes, transcribe voz, crea eventos y notas en macOS, ejecuta tareas programadas y recuerda cosas entre sesiones.

Funciona con cualquier modelo vía **OpenRouter**, **OpenAI**, **Anthropic**, **Google**, **LM Studio** u **Ollama**. El proveedor y el modelo se pueden cambiar en caliente desde Telegram. Toda la configuración vive en `config/settings.cfg`.

> **Desarrollado para macOS.** Las herramientas de Calendario, Notas y notificaciones del sistema usan AppleScript y no funcionarán en Linux.

---

## Características

- **Multi-modelo y multi-proveedor** — OpenRouter, OpenAI, Anthropic, Google, LM Studio y Ollama. Cambia proveedor y modelo en caliente con `/motorllm` y `/load`
- **Detección automática de capacidades** — en modelos locales, NEO detecta si soportan tool calling y se adapta sin configuración manual
- **32 herramientas reales** — sistema, archivos, shell, visión, voz, búsqueda web, HTTP, código Python, calculadora, portapapeles, navegador, Telegram, Calendario y Notas de macOS
- **Tareas programadas (crons)** — programa notificaciones, consultas al LLM o scripts con `/cron`. Persisten entre reinicios
- **Visión** — analiza imágenes enviadas por Telegram o rutas locales con modelos multimodales
- **Voz con Whisper local** — transcribe mensajes de voz. Acelerado por GPU en Apple Silicon con `mlx-whisper`
- **Feedback en tiempo real** — muestra `💭 Pensando...` mientras procesa y lo reemplaza con la respuesta
- **Notificaciones proactivas** — avisa vía banner macOS y Telegram cuando termina una tarea
- **Calendario y Notas macOS** — lee, crea y busca eventos y notas via AppleScript nativo
- **Memoria persistente** — recuerda preferencias y contexto entre sesiones
- **Dos interfaces** — terminal interactiva y bot de Telegram simultáneamente

---

## Requisitos

- Python 3.11+ (recomendado; funciona con 3.9 con warnings menores)
- API key de [OpenRouter](https://openrouter.ai) u otro proveedor, o LM Studio/Ollama en local
- Token de Telegram (opcional)
- `ffmpeg` para transcripción de voz: `brew install ffmpeg`
- Whisper (opcional): `pip install mlx-whisper` (Apple Silicon) o `pip install openai-whisper` (CPU)
- [`uv`](https://github.com/astral-sh/uv) — se instala automáticamente con `setup.sh`

---

## Instalación

```bash
git clone https://github.com/arcopante/neo_agent.git
cd neo_agent
bash setup.sh
nano config/settings.cfg   # añade tu API key
bash start.sh
```

Mínimo necesario en `config/settings.cfg`:

```ini
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=anthropic/claude-3.5-sonnet
```

---

## Uso

```bash
bash start.sh              # Terminal (o ambos si hay TELEGRAM_BOT_TOKEN)
bash start.sh terminal     # Solo consola
bash start.sh telegram     # Solo bot de Telegram
bash start.sh ambos        # Terminal + Telegram simultáneamente
```

### Comandos de terminal

| Comando | Acción |
|---|---|
| `/ayuda` | Muestra ayuda y comandos |
| `/config` | Ver configuración activa |
| `/memoria` | Ver recuerdos guardados |
| `/reset` | Reinicia la conversación |
| `/limpiar` | Limpia la pantalla |
| `/salir` | Sale y guarda la sesión |

---

## Comandos de Telegram

### Generales
| Comando | Descripción |
|---|---|
| `/start` | Bienvenida |
| `/ayuda` | Qué puede hacer NEO |
| `/memoria` | Ver recuerdos guardados |
| `/estado` | Estado del agente y modelo activo |
| `/reset` | Reiniciar conversación |
| `/salir` | Apagar el agente |

### Gestión del LLM
| Comando | Descripción |
|---|---|
| `/motorllm` | Ver proveedor y modelo actuales |
| `/motorllm <proveedor>` | Cambiar proveedor (openrouter, openai, anthropic, google, lmstudio, ollama) |
| `/listmodels` | Listar modelos disponibles |
| `/load <modelo>` | Cargar o cambiar modelo |
| `/unload <modelo>` | Descargar modelo de memoria (local) |

### Tareas programadas
| Comando | Descripción |
|---|---|
| `/cron <horario> <texto>` | 🔔 Notificación de texto fijo |
| `/cron <horario> llm: <prompt>` | 🤖 El LLM genera el mensaje |
| `/cron <horario> shell: <cmd>` | ⚙️ Ejecuta un comando |
| `/cronlist` | Ver todas las tareas |
| `/crondel <ID>` | Eliminar tarea |
| `/cronclear` | Borrar todas las tareas |

**Formatos de horario:** `09:00` (diario), `*/30m` (cada 30 min), `*/2h` (cada 2 horas)

```
/cron 08:00 llm: Dame el resumen del día
/cron */1h shell: df -h | grep /dev/disk
/cron 22:00 Recuerda cerrar los proyectos
```

---

## Herramientas (32)

### 💻 Sistema
| Herramienta | Descripción |
|---|---|
| `system_info` | OS, CPU, RAM, disco, Python, hostname, IP |
| `run_command` | Ejecuta comandos shell con timeout |
| `notify` | Notificación macOS + Telegram ⚠️ macOS |

### 📁 Archivos
| Herramienta | Descripción |
|---|---|
| `read_file` | Lee ficheros de texto |
| `write_file` | Crea o sobreescribe ficheros |
| `file_info` | Metadatos: tamaño, fechas, permisos, MIME |
| `list_directory` | Lista cualquier directorio del sistema |
| `find_files` | Búsqueda recursiva por nombre o extensión |
| `copy_file` | Copia ficheros o directorios |
| `move_file` | Mueve o renombra |
| `delete_file` | Elimina ficheros o directorios vacíos |
| `compress_files` | Comprime en zip o tar.gz |
| `extract_archive` | Extrae zip, tar.gz, tar.bz2... |

### 👁️ Visión
| Herramienta | Descripción |
|---|---|
| `analyze_image` | Analiza imágenes con modelos multimodales |

### 🎙️ Voz
| Herramienta | Descripción |
|---|---|
| `transcribe_audio` | Transcribe audio con Whisper local (mlx-whisper o openai-whisper) |

### 📤 Telegram
| Herramienta | Descripción |
|---|---|
| `send_telegram_file` | Envía un fichero al chat activo |

### 📋 Portapapeles
| Herramienta | Descripción |
|---|---|
| `clipboard_get` | Lee el portapapeles ⚠️ macOS |
| `clipboard_set` | Escribe en el portapapeles ⚠️ macOS |

### 🌐 Red y navegador
| Herramienta | Descripción |
|---|---|
| `open_url` | Abre URLs en el navegador |
| `web_search` | Búsqueda web via DuckDuckGo |
| `http_request` | Peticiones GET/POST a APIs REST |

### 🐍 Código y cálculo
| Herramienta | Descripción |
|---|---|
| `run_python` | Ejecuta Python con timeout de 30s |
| `calculator` | Evaluación matemática segura |

### 📅 Calendario macOS
| Herramienta | Descripción |
|---|---|
| `calendar_list_all` | Lista todos los calendarios ⚠️ macOS |
| `calendar_list` | Lista próximos eventos ⚠️ macOS |
| `calendar_add_event` | Crea eventos ⚠️ macOS |

### 📝 Notas macOS
| Herramienta | Descripción |
|---|---|
| `notes_list` | Lista notas recientes ⚠️ macOS |
| `notes_create` | Crea una nota ⚠️ macOS |
| `notes_search` | Busca notas por texto ⚠️ macOS |

### 🧠 Memoria
| Herramienta | Descripción |
|---|---|
| `memory_save` | Guarda recuerdos persistentes |
| `memory_search` | Busca en la memoria |
| `memory_list` | Lista todos los recuerdos |

---

## Configuración

Todo en `config/settings.cfg` (en `.gitignore`, nunca se sube al repo).

```ini
# ── Proveedor ──────────────────────────────────────────────────
LLM_PROVIDER=openrouter    # openrouter | openai | anthropic | google | lmstudio | ollama
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXX
LLM_MODEL=anthropic/claude-3.5-sonnet

# ── Parámetros ─────────────────────────────────────────────────
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048

# ── Telegram ───────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USERS=

# ── Voz ────────────────────────────────────────────────────────
WHISPER_MODEL=small        # tiny | base | small | medium | large

# ── macOS ──────────────────────────────────────────────────────
CALENDAR_DEFAULT=          # Nombre exacto del calendario por defecto

# ── Proveedores locales ────────────────────────────────────────
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_TOOL_CALLING=auto # auto | true | false
OLLAMA_BASE_URL=http://localhost:11434/v1

# ── Agente ─────────────────────────────────────────────────────
MEMORY_WINDOW=15           # Historial para modelos remotos
MEMORY_WINDOW_LOCAL=4      # Historial para modelos locales
AGENT_VERBOSE=false
AGENT_MAX_ITERATIONS=10
```

### Proveedores soportados

| Proveedor | Tipo | Variable requerida |
|---|---|---|
| `openrouter` | Remoto | `OPENROUTER_API_KEY` |
| `openai` | Remoto | `OPENAI_API_KEY` |
| `anthropic` | Remoto | `ANTHROPIC_API_KEY` |
| `google` | Remoto | `GOOGLE_API_KEY` |
| `lmstudio` | Local | `LMSTUDIO_BASE_URL` |
| `ollama` | Local | `OLLAMA_BASE_URL` |

### Modelos locales recomendados (tool calling)

| Modelo | Tool calling |
|---|---|
| Qwen2.5 7B Instruct | ✅ Excelente |
| Llama 3.1 8B Instruct | ✅ Bueno |
| Mistral 7B Instruct v0.3 | ✅ Bueno |
| Ministral 3B | ❌ No soportado |

---

## Estructura del proyecto

```
neo_agent/
├── neo.py                     ← Punto de entrada único
├── start.sh                   ← Arranque
├── setup.sh                   ← Instalación inicial
├── requirements.txt
│
├── config/
│   ├── settings.cfg           ← ⚙️ Tu configuración (en .gitignore)
│   ├── settings.cfg.example   ← Plantilla con todos los parámetros
│   ├── SOUL.md                ← Personalidad del agente
│   ├── IDENTITY.md            ← Nombre y capacidades
│   ├── USER.md                ← Tu perfil y preferencias
│   └── TOOLS.md               ← Referencia de herramientas
│
├── core/
│   ├── agent.py               ← Motor LangGraph ReAct
│   ├── config_loader.py       ← Carga ficheros de configuración
│   ├── cron.py                ← Scheduler de tareas programadas
│   └── llm_manager.py         ← Gestión dinámica de proveedores y modelos
│
├── tools/
│   └── tools.py               ← 32 herramientas
│
├── memory/
│   ├── long_term.json         ← Memoria persistente
│   ├── crons.json             ← Tareas programadas
│   └── sessions/              ← Log de sesiones
│
└── workspace/                 ← Directorio de trabajo del agente
```

---

## Personalización sin código

| Fichero | Qué puedes cambiar |
|---|---|
| `SOUL.md` | Personalidad, valores, tono |
| `IDENTITY.md` | Nombre, descripción, capacidades |
| `USER.md` | Tus preferencias, contexto permanente |
| `SYSTEM_PROMPT.md` | Prompt maestro completo |

---

## Contribuir

Las contribuciones son bienvenidas. Lee [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Licencia

GPL v3 — Ver [LICENSE](LICENSE).

---

<div align="center">
Hecho por <a href="https://github.com/arcopante">@arcopante</a>
</div>
