#!/bin/bash
# ══════════════════════════════════════════════════
# NEO Agent — Script de configuración
# Crea el entorno virtual e instala dependencias
# Uso: bash setup.sh
# ══════════════════════════════════════════════════

set -e  # Parar si algo falla

VENV_DIR=".venv"
PYTHON=$(which python3)

echo ""
echo "🤖 NEO Agent — Setup"
echo "════════════════════════════════════"

# ── 1. Verificar Python ────────────────────────────
echo "🐍 Verificando Python..."
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 no encontrado. Instálalo desde https://python.org"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "   ✅ Python $PYTHON_VERSION encontrado"

# ── 2. Crear entorno virtual ───────────────────────
if [ -d "$VENV_DIR" ]; then
    echo "📦 Entorno virtual ya existe en $VENV_DIR, saltando creación..."
else
    echo "📦 Creando entorno virtual en $VENV_DIR..."
    $PYTHON -m venv $VENV_DIR
    echo "   ✅ Entorno virtual creado"
fi

# ── 3. Activar entorno virtual ─────────────────────
echo "⚡ Activando entorno virtual..."
source $VENV_DIR/bin/activate

# ── 4. Actualizar pip ──────────────────────────────
echo "⬆️  Actualizando pip..."
pip install --upgrade pip -q

# ── 5. Instalar dependencias ───────────────────────
echo "📥 Instalando dependencias..."
pip install -r requirements.txt -q
echo "   ✅ Dependencias instaladas"

# Verificar que langchain-openai está instalado (necesario para LM Studio)
pip show langchain-openai &>/dev/null || pip install langchain-openai -q

# ── 6. Configurar config/settings.cfg ─────────────
if [ ! -f "config/settings.cfg" ]; then
    echo "⚙️  Creando config/settings.cfg desde plantilla..."
    cp config/settings.cfg.example config/settings.cfg
    echo "   ✅ config/settings.cfg creado"
    echo ""
    echo "   ⚠️  Edita config/settings.cfg y añade tu OPENROUTER_API_KEY"
else
    echo "⚙️  config/settings.cfg ya existe, no se sobreescribe"
fi

# ── 7. Crear workspace ─────────────────────────────
WORKSPACE="$(dirname "$0")/workspace"
mkdir -p "$WORKSPACE"
echo "📁 Workspace: $WORKSPACE (dentro de la carpeta del agente)"

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
echo "════════════════════════════════════"
echo ""
