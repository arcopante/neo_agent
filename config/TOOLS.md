# Herramientas disponibles de NEO (32)

> Desarrollado principalmente para **macOS**. Las herramientas marcadas con ⚠️ macOS
> usan AppleScript u osascript y no funcionarán en Linux.

## 💻 Sistema
- **system_info** — OS, CPU, RAM, disco, Python, hostname, IP y entorno
- **run_command** — Ejecuta comandos shell con timeout y lista de bloqueados
- **notify** — Notificación del sistema macOS + Telegram simultáneamente ⚠️ macOS

## 📁 Archivos
- **read_file** — Lee el contenido de cualquier fichero de texto
- **write_file** — Crea o sobreescribe ficheros (modo write o append)
- **file_info** — Metadatos: tamaño, fechas, permisos, tipo MIME
- **list_directory** — Lista cualquier directorio del sistema
- **find_files** — Busca ficheros por nombre o extensión de forma recursiva
- **copy_file** — Copia ficheros o directorios
- **move_file** — Mueve o renombra ficheros y directorios
- **delete_file** — Elimina ficheros o directorios vacíos
- **compress_files** — Comprime en zip o tar.gz
- **extract_archive** — Extrae zip, tar.gz, tar.bz2 y otros formatos

## 👁️ Visión
- **analyze_image** — Analiza imágenes (ruta local o URL) con modelos multimodales

## 🎙️ Voz
- **transcribe_audio** — Transcribe audio a texto con Whisper local (requiere `openai-whisper` + `ffmpeg`)

## 📤 Telegram
- **send_telegram_file** — Envía un fichero al chat de Telegram activo

## 📋 Portapapeles
- **clipboard_get** — Lee el contenido del portapapeles ⚠️ macOS/Linux
- **clipboard_set** — Copia texto al portapapeles ⚠️ macOS/Linux

## 🌐 Navegador y red
- **open_url** — Abre una URL en el navegador predeterminado
- **web_search** — Búsqueda en internet via DuckDuckGo
- **http_request** — Peticiones GET/POST a APIs REST

## 🐍 Código y cálculo
- **run_python** — Ejecuta fragmentos de Python con timeout de 30s
- **calculator** — Evaluación matemática segura y precisa

## 📅 Calendario macOS
- **calendar_list** — Lista los próximos eventos del Calendario ⚠️ macOS
- **calendar_add_event** — Crea un nuevo evento en el Calendario ⚠️ macOS

## 📝 Notas macOS
- **notes_list** — Lista las notas recientes de la app Notas ⚠️ macOS
- **notes_create** — Crea una nueva nota ⚠️ macOS
- **notes_search** — Busca notas por texto ⚠️ macOS

## 🧠 Memoria
- **memory_save** — Guarda recuerdos persistentes por categoría
- **memory_search** — Busca en la memoria a largo plazo
- **memory_list** — Lista todos los recuerdos guardados
