# Herramientas disponibles de NEO (32)

> Desarrollado para **macOS**. Las herramientas marcadas con ⚠️ macOS usan
> AppleScript y no funcionarán en Linux.

## 💻 Sistema
- **system_info** — OS, CPU, RAM, disco, Python, hostname, IP y entorno
- **run_command** — Ejecuta comandos shell con timeout y lista negra de seguridad
- **notify** — Notificación del sistema macOS + Telegram simultáneamente ⚠️ macOS

## 📁 Archivos
- **read_file** — Lee el contenido de cualquier fichero de texto
- **write_file** — Crea o sobreescribe ficheros (modo write o append)
- **file_info** — Metadatos: tamaño, fechas, permisos, tipo MIME
- **list_directory** — Lista cualquier directorio del sistema
- **find_files** — Búsqueda recursiva por nombre o extensión
- **copy_file** — Copia ficheros o directorios
- **move_file** — Mueve o renombra ficheros y directorios
- **delete_file** — Elimina ficheros o directorios vacíos
- **compress_files** — Comprime en zip o tar.gz
- **extract_archive** — Extrae zip, tar.gz, tar.bz2 y otros formatos

## 👁️ Visión
- **analyze_image** — Analiza imágenes (ruta local o URL) con modelos multimodales

## 🎙️ Voz
- **transcribe_audio** — Transcribe audio con Whisper local
  - Apple Silicon: mlx-whisper ⚡ (más rápido)
  - CPU: openai-whisper

## 📤 Telegram
- **send_telegram_file** — Envía un fichero al chat de Telegram activo

## 📋 Portapapeles
- **clipboard_get** — Lee el portapapeles del sistema ⚠️ macOS
- **clipboard_set** — Escribe en el portapapeles ⚠️ macOS

## 🌐 Navegador y red
- **open_url** — Abre URLs en el navegador predeterminado
- **web_search** — Búsqueda en internet via DuckDuckGo
- **http_request** — Peticiones GET/POST a APIs REST

## 🐍 Código y cálculo
- **run_python** — Ejecuta fragmentos de Python con timeout de 30s
- **calculator** — Evaluación matemática segura y precisa

## 📅 Calendario macOS
- **calendar_list_all** — Lista todos los calendarios disponibles ⚠️ macOS
- **calendar_list** — Lista los próximos eventos ⚠️ macOS
- **calendar_add_event** — Crea eventos con título, fecha, hora y notas ⚠️ macOS

## 📝 Notas macOS
- **notes_list** — Lista las notas recientes ⚠️ macOS
- **notes_create** — Crea una nota con título, cuerpo y carpeta ⚠️ macOS
- **notes_search** — Busca notas por texto en título y contenido ⚠️ macOS

## 🧠 Memoria
- **memory_save** — Guarda recuerdos persistentes por categoría
- **memory_search** — Busca en la memoria a largo plazo
- **memory_list** — Lista todos los recuerdos guardados
