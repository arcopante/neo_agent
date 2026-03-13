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
