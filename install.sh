#!/bin/bash
#
# Tonie API - Automatisches Installationsskript für macOS
#

set -e

echo ""
echo "🎵 Tonie API Installer"
echo "======================"
echo ""

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

progress() {
    echo -e "${GREEN}✓${NC} $1"
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# 1. Homebrew
if ! command -v brew &> /dev/null; then
    info "Homebrew wird installiert..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add to PATH
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile 2>/dev/null || true
    elif [[ -f /usr/local/bin/brew ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    progress "Homebrew installiert"
else
    progress "Homebrew bereits installiert"
fi

# 2. Python
if ! command -v python3 &> /dev/null; then
    info "Python wird installiert..."
    brew install python
    progress "Python installiert"
else
    progress "Python bereits installiert"
fi

# 3. pipx
if ! command -v pipx &> /dev/null; then
    info "pipx wird installiert..."
    brew install pipx
    pipx ensurepath --force
    progress "pipx installiert"
else
    progress "pipx bereits installiert"
fi

# Update PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# 4. tonie-api
info "Tonie API wird installiert..."
pipx install git+https://github.com/Julschik/toniebox-api.git --force 2>/dev/null || pipx upgrade tonie-api 2>/dev/null || true
progress "Tonie API installiert"

echo ""
echo "========================================"
echo -e "${GREEN}Installation erfolgreich!${NC}"
echo "========================================"
echo ""

# 5. Login
info "Jetzt richten wir deine Zugangsdaten ein..."
echo ""

if toniebox login; then
    echo ""
    echo "========================================"
    echo -e "${GREEN}Alles fertig! Hier ist die Übersicht:${NC}"
    echo "========================================"
    echo ""
    toniebox --help
    echo ""
    echo -e "${GREEN}Tipp:${NC} Starte mit 'toniebox tonies' um deine Tonies zu sehen."
else
    echo ""
    echo -e "${YELLOW}Login übersprungen. Du kannst später 'toniebox login' ausführen.${NC}"
    echo ""
    toniebox --help
fi
