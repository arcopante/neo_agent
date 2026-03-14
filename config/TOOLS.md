# Herramientas disponibles de NEO

## 💻 Sistema
- **system_info** — OS, CPU, RAM, disco, Python, hostname, IP, variables de entorno
- **run_command** — Ejecuta comandos shell (bash/zsh) con timeout y lista de bloqueados

## 📁 Archivos
- **read_file** — Lee el contenido de cualquier fichero de texto
- **write_file** — Crea o sobreescribe ficheros (modo write o append)
- **file_info** — Metadatos: tamaño, fechas, permisos, tipo MIME
- **list_directory** — Lista cualquier directorio del sistema (no solo workspace)
- **find_files** — Busca ficheros por nombre o extensión de forma recursiva
- **copy_file** — Copia ficheros o directorios
- **move_file** — Mueve o renombra ficheros y directorios
- **delete_file** — Elimina ficheros o directorios vacíos
- **compress_files** — Comprime en zip o tar.gz
- **extract_archive** — Extrae zip, tar.gz, tar.bz2 y otros formatos

## 📤 Telegram
- **send_telegram_file** — Envía un fichero al chat de Telegram activo

## 📋 Portapapeles
- **clipboard_get** — Lee el contenido del portapapeles del sistema
- **clipboard_set** — Copia texto al portapapeles

## 🌐 Navegador y red
- **open_url** — Abre una URL en el navegador predeterminado
- **web_search** — Búsqueda en internet via DuckDuckGo
- **http_request** — Peticiones GET/POST a APIs REST

## 🐍 Código
- **run_python** — Ejecuta fragmentos de Python con timeout de 30s

## 🧮 Cálculo
- **calculator** — Evaluación matemática segura y precisa

## 🧠 Memoria
- **memory_save** — Guarda recuerdos persistentes por categoría
- **memory_search** — Busca en la memoria a largo plazo
- **memory_list** — Lista todos los recuerdos guardados
