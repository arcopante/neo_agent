#!/bin/bash
# ══════════════════════════════════════════════════
# NEO Agent — Script de configuración
# Crea el entorno virtual e instala dependencias
# Uso: bash setup.sh
# ══════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo ""
echo "🤖 NEO Agent — Setup"
echo "════════════════════════════════════"

# ── 1. Verificar Python 3.11+ ──────────────────────
echo "🐍 Verificando Python..."
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 no encontrado."
    echo "   Instálalo con: brew install python@3.11"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MINOR" -lt 11 ]; then
    echo "⚠️  Python $PYTHON_VERSION detectado. Se recomienda 3.11+."
    echo "   Instálalo con: brew install python@3.11 && pyenv global 3.11"
fi
echo "   ✅ Python $PYTHON_VERSION"

# ── 2. Verificar / instalar uv ─────────────────────
echo "📦 Verificando uv..."
if ! command -v uv &>/dev/null; then
    echo "   uv no encontrado — instalando..."
    if command -v brew &>/dev/null; then
        brew install uv -q
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    echo "   ✅ uv instalado"
else
    UV_VERSION=$(uv --version 2>&1)
    echo "   ✅ $UV_VERSION"
fi

# ── 3. Crear entorno virtual con uv ───────────────
if [ -d "$VENV_DIR" ]; then
    echo "📦 Entorno virtual ya existe en .venv"
else
    echo "📦 Creando entorno virtual con uv..."
    uv venv "$VENV_DIR" --python python3
    echo "   ✅ Entorno virtual creado"
fi

# ── 4. Instalar dependencias con uv ───────────────
echo "📥 Instalando dependencias con uv..."
uv pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
echo "   ✅ Dependencias instaladas"

# ── 5. Whisper (opcional) ──────────────────────────
echo ""
echo "🎙️  ¿Instalar Whisper para transcripción de voz?"
echo "   Requiere ffmpeg: brew install ffmpeg"
echo ""
echo "   [1] mlx-whisper  — Apple Silicon (M1/M2/M3/M4), rápido y eficiente ⚡"
echo "   [2] openai-whisper — CPU, compatible con cualquier Mac"
echo "   [N] Omitir"
echo ""
read -r -p "   Opción [1/2/N]: " WHISPER_OPT

if [[ "$WHISPER_OPT" =~ ^[12]$ ]]; then
    if ! command -v ffmpeg &>/dev/null; then
        echo "   ⚠️  ffmpeg no encontrado. Instalando..."
        brew install ffmpeg -q && echo "   ✅ ffmpeg instalado"
    else
        echo "   ✅ ffmpeg ya instalado"
    fi

    if [[ "$WHISPER_OPT" == "1" ]]; then
        echo "   Instalando mlx-whisper (Apple Silicon)..."
        uv pip install mlx-whisper --quiet
        echo "   ✅ mlx-whisper instalado"
    else
        echo "   Instalando openai-whisper (CPU)..."
        uv pip install openai-whisper --quiet
        echo "   ✅ openai-whisper instalado"
    fi
else
    echo "   Omitido. Puedes instalarlo después con:"
    echo "   source .venv/bin/activate"
    echo "   Apple Silicon: pip install mlx-whisper"
    echo "   CPU:           pip install openai-whisper"
fi

# ── 6. Configurar config/settings.cfg ─────────────
echo ""
if [ ! -f "$SCRIPT_DIR/config/settings.cfg" ]; then
    echo "⚙️  Creando config/settings.cfg desde plantilla..."
    cp "$SCRIPT_DIR/config/settings.cfg.example" "$SCRIPT_DIR/config/settings.cfg"
    echo "   ✅ config/settings.cfg creado"
    echo "   ⚠️  Edita config/settings.cfg y añade tu OPENROUTER_API_KEY"
else
    echo "⚙️  config/settings.cfg ya existe, no se sobreescribe"
fi

# ── 7. Crear workspace ─────────────────────────────
mkdir -p "$SCRIPT_DIR/workspace"
echo "📁 Workspace listo"

# ── Listo ──────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "✅ Setup completado."
echo ""
echo "Para usar NEO:"
echo ""
echo "  1. Edita config/settings.cfg y añade tu OPENROUTER_API_KEY"
echo "  2. bash start.sh"
echo ""
echo "💡 uv usa caché global de paquetes — reinstalar en otro"
echo "   proyecto será instantáneo y no ocupa espacio extra."
echo "════════════════════════════════════"
echo ""
