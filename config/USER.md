# 👤 USER — Perfil del Usuario

## Información básica

```yaml
nombre: ""          # Nombre preferido del usuario (se aprende en conversación)
idioma: "auto"      # auto | es | en | fr | ...
nivel_tecnico: "auto"  # auto | básico | intermedio | avanzado
```

## Preferencias de respuesta

```yaml
estilo: "balanceado"      # conciso | balanceado | detallado
formato: "markdown"       # texto | markdown
mostrar_razonamiento: true  # Mostrar pasos de razonamiento del agente
confirmar_acciones: true    # Pedir confirmación antes de acciones destructivas
```

## Permisos

```yaml
# Qué puede hacer el agente sin pedir confirmación
auto_permitido:
  - web_search
  - read_file
  - calculator
  - memory_search
  - http_request

# Qué SIEMPRE requiere confirmación explícita del usuario
requiere_confirmacion:
  - write_file
  - run_python
  - memory_save
```

## Contexto personal (rellenar opcionalmente)

```yaml
# Añade aquí contexto que el agente debe recordar siempre
contexto_permanente: |
  # Ejemplo:
  # El usuario trabaja con Python 3.11 en macOS.
  # Sus proyectos están en ~/proyectos/
  # Prefiere usar ruff sobre black para formateo.
```

## Historial de preferencias aprendidas

> Este apartado es actualizado automáticamente por el agente cuando aprende
> algo relevante sobre el usuario durante las conversaciones.

<!-- AGENT_LEARNED_PREFERENCES_START -->
<!-- AGENT_LEARNED_PREFERENCES_END -->
