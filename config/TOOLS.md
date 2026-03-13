# 🛠️ TOOLS — Referencia de Herramientas

## Filosofía de uso de herramientas

> El agente usa herramientas solo cuando es necesario.
> Si puede responder desde su conocimiento con certeza, no busca externamente.
> Siempre informa qué herramienta usó y por qué.

---

## `web_search` — Búsqueda web

**Cuándo usar**: Información reciente, eventos actuales, documentación específica.  
**Proveedor**: DuckDuckGo (sin API key) / Tavily (con API key).  
**Output**: Lista de resultados con título, URL y fragmento.

```
Ejemplo de uso: "busca las últimas noticias sobre Python 3.14"
```

---

## `read_file` — Leer archivo

**Cuándo usar**: El usuario menciona un archivo o pide analizarlo.  
**Permisos**: Solo rutas permitidas (configurable en `.env`).  
**Formatos**: `.txt`, `.md`, `.py`, `.json`, `.csv`, `.yaml`, `.toml`, `.html`...

```
Ejemplo: "lee el archivo config.json y explícame la estructura"
```

---

## `write_file` — Escribir archivo

**Cuándo usar**: Guardar resultados, crear scripts, exportar datos.  
**⚠️ Requiere confirmación** si el archivo ya existe.  
**Modos**: `write` (crea/sobreescribe) | `append` (añade al final)

```
Ejemplo: "guarda el resultado en output.txt"
```

---

## `list_directory` — Listar directorio

**Cuándo usar**: El usuario quiere saber qué hay en una carpeta.  
**Output**: Árbol de archivos y directorios.

```
Ejemplo: "¿qué archivos hay en mi carpeta de proyectos?"
```

---

## `run_python` — Ejecutar Python

**Cuándo usar**: Cálculos, procesamiento de datos, scripts ad-hoc.  
**⚠️ Requiere confirmación** antes de ejecutar.  
**Entorno**: Proceso Python aislado con timeout de 30s.  
**Acceso**: Solo al directorio de trabajo definido en `.env`.

```
Ejemplo: "analiza este CSV y dime cuántas filas tienen valores nulos"
```

---

## `http_request` — Petición HTTP

**Cuándo usar**: Consultar APIs REST públicas o privadas.  
**Métodos**: GET (por defecto), POST (con parámetros explícitos).  
**Headers**: Configurables, incluye soporte para Bearer token.

```
Ejemplo: "consulta la API de wttr.in para saber el tiempo en Madrid"
```

---

## `calculator` — Calculadora

**Cuándo usar**: Expresiones matemáticas, conversiones, estadísticas básicas.  
**Motor**: `numexpr` / `eval` seguro.  
**No usa**: LLM para matemáticas — usa cálculo real.

```
Ejemplo: "¿cuánto es 15% de 2847 más el IVA del 21%?"
```

---

## `memory_save` — Guardar en memoria

**Cuándo usar**: El usuario pide recordar algo, o el agente detecta info relevante.

```
Ejemplo: "recuerda que mi base de datos está en localhost:5432"
```

---

## `memory_search` — Buscar en memoria

**Cuándo usar**: El agente necesita contexto de sesiones anteriores.

```
Ejemplo: "¿qué habíamos dicho sobre el proyecto X?"
```
