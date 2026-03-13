<div align="center">

# 🤖 NEO

### Agente de IA personal con ejecución real de acciones

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C?logo=chainlink&logoColor=white)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct-FF6B35)](https://langchain-ai.github.io/langgraph)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-compatible-6366F1)](https://openrouter.ai)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

</div>

---

NEO es un agente de IA personal que entiende lenguaje natural y ejecuta acciones reales: busca en internet, gestiona archivos, corre código, consulta APIs y recuerda cosas entre sesiones.

Funciona con cualquier modelo de lenguaje vía **OpenRouter** (Claude, GPT-4o, Llama, Mistral, Gemini…) o en local con **LM Studio**. Toda la configuración vive en un único fichero `config/settings.cfg`, sin tocar código. Disponible en terminal y como **bot de Telegram**.

---

## Características

- **Multi-modelo** — Cambia entre Claude, GPT-4o, Llama, Mistral o cualquier modelo de OpenRouter con una línea en la configuración
- **Herramientas reales** — Búsqueda web, lectura/escritura de archivos, ejecución de Python, peticiones HTTP y calculadora
- **Memoria persistente** — Recuerda preferencias y contexto entre sesiones mediante `memory/long_term.json`
- **Dos interfaces** — Terminal interactiva y bot de Telegram, pueden correr simultáneamente
- **Personalizable sin código** — Cambia la personalidad, el perfil de usuario y el comportamiento editando ficheros Markdown en `config/`
- **Configuración centralizada** — Una sola fuente de verdad en `config/settings.cfg`, sin variables dispersas

---

## Requisitos

- Python 3.10 o superior
- Una API key de [OpenRouter](https://openrouter.ai) (o LM Studio en local)
- Token de Telegram (opcional, para el bot)

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/arcopante/neo_agent.git
cd neo_agent

# 2. Ejecutar el setup (crea .venv e instala dependencias)
bash setup.sh

# 3. Configurar
#    El setup ya habrá creado config/settings.cfg desde la plantilla.
#    Solo necesitas añadir tu API key:
nano config/settings.cfg
```

Mínimo necesario en `config/settings.cfg`:

```ini
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=anthropic/claude-3.5-sonnet
```

```bash
# 4. Arrancar
bash start.sh
```

---

## Uso

```bash
bash start.sh              # Terminal (o ambos si hay TELEGRAM_BOT_TOKEN)
bash start.sh terminal     # Solo consola interactiva
bash start.sh telegram     # Solo bot de Telegram
bash start.sh ambos        # Terminal + Telegram simultáneamente
```

### Ejemplos de conversación

```
busca las últimas noticias sobre LangGraph
lee el archivo datos.csv y dime cuántas filas tiene
¿cuánto es el 21% de IVA sobre 3.450€?
crea un script Python que renombre estos archivos y ejecútalo
consulta la API wttr.in para Madrid y dime el tiempo
recuerda que mis proyectos están en ~/dev
guarda un resumen de esta conversación en notas.txt
```

### Comandos de terminal

| Comando | Acción |
|---|---|
| `ayuda` | Muestra ayuda y comandos disponibles |
| `config` | Ver configuración activa |
| `memoria` | Ver recuerdos guardados |
| `nueva sesión` | Reinicia la conversación (conserva la memoria larga) |
| `limpiar` | Limpia la pantalla |
| `salir` | Sale y guarda la sesión |

---

## Configuración

Todo en `config/settings.cfg`. Este fichero está en `.gitignore` y nunca se sube al repositorio.

```ini
# ── Proveedor ──────────────────────────────────────
LLM_PROVIDER=openrouter       # openrouter | lmstudio | anthropic | openai | google
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXX
LLM_MODEL=anthropic/claude-3.5-sonnet

# ── Parámetros del modelo ──────────────────────────
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# ── Telegram (opcional) ────────────────────────────
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USERS=       # IDs separados por coma. Vacío = bot público.

# ── Agente ─────────────────────────────────────────
MEMORY_WINDOW=20              # Mensajes en memoria de trabajo
AGENT_VERBOSE=false           # true → muestra llamadas a herramientas
AGENT_MAX_ITERATIONS=10
```

### Modelos disponibles en OpenRouter

| Proveedor | Modelo | Slug |
|---|---|---|
| Anthropic | Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` |
| OpenAI | GPT-4o | `openai/gpt-4o` |
| Meta | Llama 3.1 70B | `meta-llama/llama-3.1-70b-instruct` |
| Mistral | Mistral Large | `mistralai/mistral-large` |
| Google | Gemini Pro 1.5 | `google/gemini-pro-1.5` |

Catálogo completo en [openrouter.ai/models](https://openrouter.ai/models).

### Uso en local con LM Studio

```ini
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LLM_MODEL=local-model
```

Modelos recomendados con soporte de herramientas: `Qwen2.5 7B`, `Mistral 7B Instruct`, `Llama 3.1 8B`.

---

## Herramientas

| Herramienta | Descripción |
|---|---|
| `web_search` | Búsqueda en internet via DuckDuckGo |
| `read_file` | Lee archivos de texto |
| `write_file` | Escribe o crea archivos en el workspace |
| `list_directory` | Lista el contenido de carpetas |
| `run_python` | Ejecuta código Python con timeout de 30s |
| `http_request` | Peticiones GET/POST a APIs REST |
| `calculator` | Evaluación matemática segura |
| `memory_save` | Guarda recuerdos persistentes por categoría |
| `memory_search` | Busca en la memoria a largo plazo |
| `memory_list` | Lista todos los recuerdos guardados |

### Añadir una herramienta nueva

Edita `tools/tools.py` y añade una función decorada con `@tool`:

```python
@tool
def mi_herramienta(parametro: str) -> str:
    """
    Descripción clara. El LLM usa esto para decidir cuándo usarla.

    Args:
        parametro: Descripción del parámetro.

    Returns:
        Resultado como string.
    """
    return f"resultado: {parametro}"
```

Añádela a `ALL_TOOLS` al final del fichero. El agente la detecta automáticamente en el siguiente arranque.

---

## Estructura del proyecto

```
neo_agent/
├── neo.py                     ← Punto de entrada único
├── start.sh                   ← Arranque (lee config/settings.cfg)
├── setup.sh                   ← Instalación inicial (solo una vez)
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── settings.cfg           ← ⚙️  Tu configuración real (en .gitignore)
│   ├── settings.cfg.example   ← Plantilla con todos los parámetros
│   ├── SOUL.md                ← Valores y personalidad del agente
│   ├── IDENTITY.md            ← Nombre y capacidades
│   ├── USER.md                ← Tu perfil y preferencias permanentes
│   ├── MEMORY.md              ← Documentación del sistema de memoria
│   ├── TOOLS.md               ← Referencia de herramientas
│   └── SYSTEM_PROMPT.md       ← Prompt maestro (avanzado)
│
├── core/
│   ├── agent.py               ← Motor del agente (LangGraph ReAct)
│   └── config_loader.py       ← Combina los ficheros config en el prompt
│
├── tools/
│   └── tools.py               ← Definición de todas las herramientas
│
├── memory/
│   ├── long_term.json         ← Memoria persistente (auto-generado)
│   └── sessions/              ← Log de cada conversación (auto-generado)
│
└── workspace/                 ← Directorio de trabajo del agente
```

---

## Personalización sin código

Los ficheros Markdown de `config/` controlan el comportamiento del agente sin tocar Python:

| Fichero | Qué puedes cambiar |
|---|---|
| `SOUL.md` | Personalidad, valores, tono, forma de responder |
| `IDENTITY.md` | Nombre, descripción, capacidades declaradas |
| `USER.md` | Tus preferencias, contexto permanente, permisos |
| `SYSTEM_PROMPT.md` | Prompt maestro completo (para usuarios avanzados) |

---

## Bot de Telegram

1. Habla con **@BotFather** → `/newbot` → copia el token
2. Habla con **@userinfobot** para obtener tu ID de usuario
3. Añádelos en `config/settings.cfg`:
   ```ini
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   TELEGRAM_ALLOWED_USERS=12345678
   ```
4. `bash start.sh telegram`

### Comandos del bot

| Comando | Descripción |
|---|---|
| `/start` | Bienvenida |
| `/ayuda` | Qué puede hacer NEO |
| `/memoria` | Ver recuerdos guardados |
| `/estado` | Estado del agente y modelo activo |
| `/reset` | Reiniciar conversación |

---

## Memoria

NEO mantiene dos capas de memoria:

**Memoria de trabajo** — El historial de la sesión actual en RAM, configurable con `MEMORY_WINDOW` (por defecto 20 mensajes).

**Memoria a largo plazo** — Persiste en `memory/long_term.json` entre reinicios y sesiones. El agente puede guardar y recuperar recuerdos categorizados: preferencias, hechos, tareas, contexto.

```
👤 recuerda que prefiero respuestas concisas y en markdown
🤖 ✅ Guardado en memoria como preferencia.

# Próxima sesión, sin decirle nada:
🤖 [responde conciso y en markdown automáticamente]
```

---

## Contribuir

Las contribuciones son bienvenidas. Lee [CONTRIBUTING.md](CONTRIBUTING.md) para las instrucciones.

---

## Licencia

NEO se distribuye bajo la licencia **GNU General Public License v3.0**.
Puedes usarlo, modificarlo y redistribuirlo libremente siempre que mantengas la misma licencia.
Ver [LICENSE](LICENSE) para el texto completo.

---

<div align="center">
Hecho por <a href="https://github.com/arcopante">@arcopante</a>
</div>
