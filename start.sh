#!/bin/bash
# ══════════════════════════════════════════════════
# NEO Agent — Script de arranque
#
# La configuración se gestiona en: config/settings.cfg
#
# Uso:
#   bash start.sh          → terminal (o ambos si hay TELEGRAM_BOT_TOKEN)
#   bash start.sh terminal → solo terminal
#   bash start.sh telegram → solo Telegram
#   bash start.sh ambos    → terminal + Telegram simultáneamente
# ══════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
CONFIG_FILE="$SCRIPT_DIR/config/settings.cfg"
MODE="${1:-auto}"

# ── Cargar config/settings.cfg ────────────────────
if [ -f "$CONFIG_FILE" ]; then
    echo "📄 Cargando configuración desde config/settings.cfg"
    while IFS= read -r line || [ -n "$line" ]; do
        # Ignorar comentarios y líneas vacías
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
            key="${line%%=*}"
            value="${line#*=}"
            # Eliminar comentarios inline (# ...) y espacios sobrantes
            value="${value%%#*}"
            value="${value%"${value##*[![:space:]]}"}"
            if [ -z "${!key+x}" ]; then
                export "$key=$value"
            fi
        fi
    done < "$CONFIG_FILE"
else
    echo "⚠️  No se encontró config/settings.cfg"
    echo "   Copia config/settings.cfg.example como config/settings.cfg y edítalo."
    exit 1
fi

# ── Workspace ─────────────────────────────────────
export AGENT_WORKSPACE="$SCRIPT_DIR/workspace"

# ── Verificar entorno virtual ──────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Entorno virtual no encontrado. Ejecuta primero: bash setup.sh"
    exit 1
fi

source "$VENV_DIR/bin/activate"

# ── Verificar token si modo Telegram ──────────────
if [ "$MODE" = "telegram" ] && [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo ""
    echo "❌ TELEGRAM_BOT_TOKEN está vacío."
    echo "   Edita config/settings.cfg y añade tu token de @BotFather."
    echo ""
    exit 1
fi

# ── Resolver modo auto ────────────────────────────
if [ "$MODE" = "auto" ]; then
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        MODE="ambos"
    else
        MODE="terminal"
    fi
fi

echo "🤖 Proveedor LLM: ${LLM_PROVIDER} | Modelo: ${LLM_MODEL}"
echo "🚀 Arrancando NEO en modo $MODE..."

cd "$SCRIPT_DIR"
python neo.py "$MODE"
