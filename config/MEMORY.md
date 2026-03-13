# 🧠 MEMORY — Sistema de Memoria

## Tipos de memoria

### 1. Memoria de trabajo (Working Memory)
- **Qué es**: Las últimas N interacciones de la sesión actual.
- **Dónde vive**: En RAM, objeto `ConversationBufferWindowMemory` de LangChain.
- **Duración**: Solo mientras el proceso está activo.
- **Tamaño**: Últimas `20` interacciones (configurable en `.env`).

### 2. Memoria a largo plazo (Long-Term Memory)
- **Qué es**: Hechos, preferencias y recuerdos que el agente decide persistir.
- **Dónde vive**: `memory/long_term.json`
- **Duración**: Permanente entre sesiones.
- **Formato**: Lista de entradas con timestamp, categoría y contenido.

### 3. Memoria de sesión (Session Log)
- **Qué es**: Registro completo de todas las conversaciones.
- **Dónde vive**: `memory/sessions/YYYY-MM-DD_HH-MM.json`
- **Duración**: Permanente (archivo por sesión).

## Estructura de memoria a largo plazo

```json
{
  "memories": [
    {
      "id": "uuid-aquí",
      "timestamp": "2024-01-15T10:30:00",
      "category": "preferencia | hecho | tarea | contexto",
      "importance": 1,
      "content": "El usuario prefiere respuestas en español.",
      "source": "aprendido | manual"
    }
  ]
}
```

## Categorías de memoria

| Categoría    | Descripción                                         |
|--------------|-----------------------------------------------------|
| `preferencia`| Gustos y preferencias del usuario                   |
| `hecho`      | Información factual aprendida en conversación       |
| `tarea`      | Tareas pendientes o en progreso                     |
| `contexto`   | Contexto del proyecto o situación actual            |
| `error`      | Errores pasados para no repetirlos                  |

## Cuándo guardar en memoria a largo plazo

El agente guarda automáticamente cuando detecta:
- Preferencias explícitas: *"siempre quiero..."*, *"prefiero..."*
- Datos de contexto: rutas de proyecto, stack técnico, etc.
- Correcciones: *"no, lo que quería decir era..."*
- Información personal relevante para futuras sesiones.

## Comandos de memoria

El usuario puede pedirle al agente:
- *"recuerda que..."* → guarda en long_term
- *"olvida que..."* → elimina de long_term  
- *"¿qué recuerdas de mí?"* → lista memorias
- *"borra tu memoria"* → limpia long_term (con confirmación)
