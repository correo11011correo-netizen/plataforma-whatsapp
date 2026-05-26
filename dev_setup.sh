#!/bin/bash

# =========================================================================
#            🚀 DEV_SETUP.SH: Instalador y Configuración Local           
# =========================================================================
# Este script automatiza la configuración de tu entorno de desarrollo local
# para Plataforma WhatsApp. Instala dependencias, configura el entorno y
# te da los pasos para iniciar todos los servicios.
#
# Autor: Gemini CLI
# =========================================================================

# Colores para mensajes en la terminal
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}INFO: ${NC}$1"; }
log_success() { echo -e "${GREEN}ÉXITO: ${NC}$1"; }
log_warn() { echo -e "${YELLOW}ADVERTENCIA: ${NC}$1"; }
log_error() { echo -e "${RED}ERROR: ${NC}$1" >&2; exit 1; }
log_header() { echo -e "
${BLUE}--- $1 ---${NC}"; }

# --- 0. Pre-verificación de Directorio --- 
CURRENT_DIR=$(pwd)
PROJECT_ROOT="$(dirname "$(dirname "$CURRENT_DIR")")"

if [[ "$(basename "$CURRENT_DIR")" != "plataforma-whatsapp" && "$(basename "$(dirname "$CURRENT_DIR")")" != "plataforma-whatsapp" ]]; then
    log_error "Debes ejecutar este script desde la raíz del proyecto 'plataforma-whatsapp'." 
fi

log_header "1. Verificando Dependencias del Sistema"

# --- 1. Verificación e Instalación de Python --- 
if ! command -v python3 &> /dev/null; then
    log_error "python3 no está instalado. Por favor, instala Python 3.8 o superior.
        Sugerencias:
          Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-venv
          macOS: brew install python@3.10 (o versión similar)
          Windows: Descarga desde python.org o usa Chocolatey: choco install python --version=3.10"
fi
log_success "Python 3.x detectado."

# --- 2. Verificación e Instalación de Node.js y npm --- 
NODE_INSTALLED=false
NPM_INSTALLED=false

if command -v node &> /dev/null; then
    NODE_INSTALLED=true
    log_success "Node.js detectado (v$(node -v))."
else
    log_warn "Node.js no detectado. El panel de administración frontend y backend pueden no funcionar sin él.
        Sugerencias de instalación:
          Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs
          macOS (Homebrew): brew install node
          Windows (Chocolatey): choco install nodejs-lts
          Windows (NVM): Busca 'nvm windows' para gestionar versiones."
fi

if command -v npm &> /dev/null; then
    NPM_INSTALLED=true
    log_success "npm detectado (v$(npm -v))."
else
    log_warn "npm no detectado. Es necesario para instalar dependencias del Admin Panel."
fi

# --- 3. Configuración de Entorno Virtual de Python ---
log_header "3. Configurando Entorno Virtual de Python"
PYTHON_VENV_DIR="venv"
if [ ! -d "$PYTHON_VENV_DIR" ]; then
    log_info "Creando entorno virtual '$PYTHON_VENV_DIR'..."
    python3 -m venv "$PYTHON_VENV_DIR" || log_error "Error al crear el entorno virtual."
fi

log_info "Activando entorno virtual..."
source "$PYTHON_VENV_DIR/bin/activate" || log_error "Error al activar el entorno virtual."
log_success "Entorno virtual activado."

# --- 4. Instalación de Dependencias de Python ---
log_header "4. Instalando Dependencias de Python"

PYTHON_REQS=(
    "bot-manager/bot-engine/requirements.txt"
    "api-fundacion-idear-webhook/requirements.txt"
)

for req_file in "${PYTHON_REQS[@]}"; do
    if [ -f "$req_file" ]; then
        log_info "Instalando dependencias de '$req_file'..."
        pip install -r "$req_file" || log_error "Fallo al instalar dependencias de '$req_file'."
    else
        log_warn "Archivo de dependencias '$req_file' no encontrado. Saltando."
    fi
done
log_success "Dependencias de Python instaladas."

# --- 5. Instalación de Dependencias de Node.js ---
log_header "5. Instalando Dependencias de Node.js (Admin Panel)"

if $NODE_INSTALLED && $NPM_INSTALLED; then
    NODE_DIRS=(
        "test-cli/bot-dashboard/backend"
        "test-cli/bot-dashboard/frontend"
    )

    for node_dir in "${NODE_DIRS[@]}"; do
        if [ -d "$node_dir" ]; then
            log_info "Instalando dependencias de Node.js en '$node_dir'..."
            (cd "$node_dir" && npm install) || log_error "Fallo al instalar dependencias de Node.js en '$node_dir'."
        else
            log_warn "Directorio de Node.js '$node_dir' no encontrado. Saltando."
        fi
    done
    log_success "Dependencias de Node.js instaladas."
else
    log_warn "Node.js o npm no están completamente configurados. Las dependencias del Admin Panel no se instalarán automáticamente."
fi

# --- 6. Configuración del archivo .env ---
log_header "6. Configurando .env"
ENV_FILE=".env"
ENV_EXAMPLE_FILE="bot-manager/bot-engine/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE_FILE" ]; then
        cp "$ENV_EXAMPLE_FILE" "$ENV_FILE" || log_error "Fallo al copiar .env.example."
        log_success "Archivo '$ENV_FILE' creado a partir de '$ENV_EXAMPLE_FILE'."
    else
        log_warn "No se encontró '$ENV_EXAMPLE_FILE'. No se pudo crear '$ENV_FILE'."
    fi
else
    log_info "Archivo '$ENV_FILE' ya existe. No se sobrescribe."
fi

# Ajustar DATABASE_URL en .env para ruta relativa correcta desde la raíz del proyecto
if [ -f "$ENV_FILE" ]; then
    log_info "Ajustando DATABASE_URL en '$ENV_FILE'..."
    # Eliminar línea antigua si existe
    sed -i '/^DATABASE_URL=/d' "$ENV_FILE"
    # Añadir la nueva línea al final
    echo "DATABASE_URL=sqlite:///./bot-manager/database/bot_dashboard.db" >> "$ENV_FILE"
    log_success "DATABASE_URL configurada para local SQLite."
fi

# --- 7. Nota sobre la Base de Datos --- 
log_header "7. Base de Datos Local (SQLite)"
log_info "La base de datos 'bot_dashboard.db' se creará automáticamente al primer acceso por los scripts de Python."

# --- 8. Instrucciones Finales de Inicio ---
log_header "8. ¡Entorno de Desarrollo Local Listo!"
log_success "Todos los componentes configurados. Sigue estos pasos para iniciar y usar el proyecto:
"

log_info "1. Asegúrate de que el entorno virtual esté activo (si abres una nueva terminal):"
echo -e "    ${YELLOW}source venv/bin/activate${NC}
"

log_info "2. Inicia el ${BLUE}Bot Engine (Python Server)${NC} (se ejecutará en segundo plano en el puerto 5001):"
echo -e "    ${YELLOW}cd bot-manager/bot-engine && python server.py & disown${NC}
"

log_info "3. Inicia el ${BLUE}Admin Panel Backend (API Flask)${NC} (se ejecutará en segundo plano en el puerto 5002):"
echo -e "    ${YELLOW}cd bot-admin-panel/backend && python dashboard_api.py & disown${NC}
"

log_info "4. Abre el ${BLUE}Admin Panel Frontend (Chats)${NC} en tu navegador:"
echo -e "    ${YELLOW}file://${CURRENT_DIR}/bot-admin-panel/frontend/index.html${NC}
"

log_info "5. Abre el ${BLUE}Admin Panel Frontend (Configuración)${NC} en tu navegador:"
echo -e "    ${YELLOW}file://${CURRENT_DIR}/bot-admin-panel/frontend-settings/index.html${NC}
"

log_info "6. Para ${RED}DETENER${NC} los servicios en segundo plano, usa los siguientes comandos:"
echo -e "    ${YELLOW}kill %1; kill %2${NC} (Si son los últimos procesos en segundo plano)"
echo -e "    ${YELLOW}pkill -f "python server.py"${NC} (Para el Bot Engine)"
echo -e "    ${YELLOW}pkill -f "python dashboard_api.py"${NC} (Para el Admin Panel Backend)
"

log_info "7. Para la funcionalidad completa con la API de Meta (Webhooks, envío real de mensajes):"
echo -e "    ${YELLOW}Debes editar el archivo .env${NC} ubicado en la raíz del proyecto. Rellena las siguientes variables con tus credenciales reales:
"
echo -e "        ${YELLOW}VERIFY_TOKEN=tu_token_de_verificacion_aqui
"
          "        WHATSAPP_TOKEN=tu_whatsapp_token
"
          "        WHATSAPP_PHONE_ID=tu_phone_id
"
          "        MESSAGING_APP_ID=tu_app_id
"
          "        MESSAGING_APP_SECRET=tu_app_secret
"
          "        INSTAGRAM_TOKEN=tu_instagram_token
"
          "        NGROK_URL=tu_url_de_ngrok_o_dominio_aqui (Para exponer tu localhost a Meta)

"
echo -e "    Consulta la documentación en la carpeta '${BLUE}docs/${NC}' para más detalles y cómo configurar Webhooks y NGROK."
echo "---------------------------------------------------"
