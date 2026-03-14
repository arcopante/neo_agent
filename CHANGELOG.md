# Changelog

Todos los cambios relevantes de este proyecto se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [1.0.0] - 2026-03-13

Primera release pública de NEO.

### Añadido

- Motor del agente basado en **LangGraph ReAct** con soporte de herramientas nativas
- Soporte multi-proveedor: **OpenRouter**, LM Studio, Anthropic, OpenAI, Google
- Configuración centralizada en `config/settings.cfg` — sin variables dispersas en scripts
- Herramientas integradas: búsqueda web (DuckDuckGo), lectura/escritura de archivos, ejecución de Python, peticiones HTTP y calculadora
- Sistema de memoria en dos capas: memoria de trabajo por sesión y memoria a largo plazo persistente en JSON
- Interfaz de **terminal interactiva** con historial de sesión y comandos (`ayuda`, `config`, `memoria`, `salir`...)
- **Bot de Telegram** con whitelist de usuarios, modo `ambos` (terminal + Telegram simultáneo) y comandos `/start`, `/ayuda`, `/memoria`, `/estado`, `/reset`, `/salir`
- Personalización sin código mediante ficheros Markdown en `config/` (SOUL, IDENTITY, USER, SYSTEM_PROMPT)
- Scripts `setup.sh` y `start.sh` para instalación y arranque en un solo paso
- Detección automática de modo al arrancar (terminal vs ambos según si hay token de Telegram)

## [1.0.1] - 2026-03-14

### Corregido

- **Spam de logs** — silenciados `httpx`, `httpcore` y `telegram` en nivel INFO; el polling de Telegram ya no llena la consola de peticiones HTTP
- **`/salir` no funcionaba en terminal** — el comando no salía del proceso; ahora llama a `sys.exit(0)` correctamente
- **Comandos con o sin barra** — el terminal acepta tanto `salir` como `/salir`; el banner y la ayuda muestran la barra `/` de forma consistente
- **Referencias a LM Studio** en mensajes de error, `/estado` y configuración — ahora muestran los valores reales del proveedor activo
- **Default de proveedor** cambiado de `lmstudio` a `openrouter` en `core/agent.py`
- **Comentarios inline en settings.cfg** — el parser de `start.sh` ahora elimina correctamente los comentarios `# ...` al leer los valores
- **Auto-detección de modo `ambos`** — el modo por defecto en `start.sh` pasa a ser `auto` para evitar conflictos con la detección de token

### Eliminado

- `main.py` y `telegram_bot.py` — ficheros duplicados; toda la lógica vive en `neo.py`

## [1.1.0] - 2026-03-14

### Añadido

- **`system_info`** — información completa del sistema: OS, CPU, RAM, disco, Python, hostname, IP y variables de entorno. Requiere `psutil` (incluido en requirements)
- **`run_command`** — ejecuta comandos shell arbitrarios con timeout y lista negra de comandos destructivos
- **`file_info`** — metadatos detallados de cualquier fichero: tamaño, fechas, permisos y tipo MIME
- **`find_files`** — búsqueda recursiva de ficheros por nombre o extensión en cualquier ruta del sistema
- **`copy_file`** — copia ficheros o directorios completos
- **`move_file`** — mueve o renombra ficheros y directorios
- **`delete_file`** — elimina ficheros o directorios vacíos con confirmación
- **`compress_files`** — comprime en zip o tar.gz
- **`extract_archive`** — extrae zip, tar.gz, tar.bz2 y otros formatos
- **`send_telegram_file`** — envía cualquier fichero al chat de Telegram activo
- **`clipboard_get`** — lee el contenido del portapapeles del sistema
- **`clipboard_set`** — copia texto al portapapeles
- **`open_url`** — abre URLs en el navegador predeterminado
- `psutil>=5.9.0` añadido a `requirements.txt`

### Mejorado

- **`list_directory`** — ahora opera en cualquier ruta del sistema (no solo workspace), muestra fecha de modificación y distingue carpetas de ficheros
- **`_resolve_path`** — expande correctamente `~` en todas las rutas
- README actualizado con las 23 herramientas, nuevos ejemplos y badge de Python 3.11+
- `config/TOOLS.md` actualizado con el catálogo completo de herramientas

## [1.2.0] - 2026-03-14

### Añadido

- **`notify`** — notificación proactiva vía osascript (macOS) + Telegram simultáneamente. El agente puede avisar al usuario cuando termina una tarea larga sin que tenga que estar mirando la pantalla
- **`analyze_image`** — análisis de imágenes con modelos multimodales (Claude 3, GPT-4o) vía OpenRouter. Acepta rutas locales y URLs
- **Handler de imágenes en Telegram** — envía una foto al bot y Neo la analiza directamente con visión. El caption de la foto se usa como pregunta
- **`transcribe_audio`** — transcripción de audio a texto con Whisper ejecutándose en local, sin APIs externas. Soporta mp3, wav, ogg, m4a, flac
- **Handler de voz en Telegram** — los mensajes de voz se transcriben automáticamente con Whisper y se procesan como texto normal
- **`calendar_list`** — lista los próximos eventos del Calendario de macOS vía AppleScript
- **`calendar_add_event`** — crea eventos en el Calendario de macOS con título, fecha/hora, duración y notas
- **`notes_list`** — lista las notas recientes de la app Notas de macOS
- **`notes_create`** — crea nuevas notas en la app Notas de macOS con título, cuerpo y carpeta
- **`notes_search`** — busca notas por texto en título y contenido
- `WHISPER_MODEL` añadido a `settings.cfg` (opciones: tiny, base, small, medium, large)
- Badge de macOS en el README
- Nota de compatibilidad: desarrollado para macOS, las herramientas de sistema nativo no funcionan en Linux

### Notas de instalación

Para usar transcripción de voz:
```bash
brew install ffmpeg
pip install openai-whisper
```

## [1.2.1] - 2026-03-14

### Corregido

- **`calendar_add_event`** — formato de fecha corregido a `MM/DD/YYYY HH:MM:SS` para compatibilidad con AppleScript independientemente del locale del sistema
- **`calendar_add_event`** — nuevo parámetro `CALENDAR_DEFAULT` en `settings.cfg` para evitar que los eventos se creen en un calendario inesperado
- **Nueva herramienta `calendar_list_all`** — lista todos los calendarios con su estado de escritura para saber exactamente qué nombres usar
- Warning de `resource_tracker` silenciado al cerrar con `/salir`

### Añadido

- `CALENDAR_DEFAULT` en `settings.cfg.example` — nombre del calendario por defecto para crear eventos
- `WHISPER_MODEL` en `settings.cfg.example` — documentado con todas las opciones disponibles
- `setup.sh` ahora pregunta entre `mlx-whisper` (Apple Silicon) y `openai-whisper` (CPU)
