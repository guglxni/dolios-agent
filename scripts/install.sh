#!/usr/bin/env bash
# Dolios Agent — One-Line Installer
# Usage: curl -fsSL https://dolios.dev/install.sh | bash
set -euo pipefail

DOLIOS_BLUE='\033[0;34m'
DOLIOS_RED='\033[0;31m'
DOLIOS_GREEN='\033[0;32m'
DOLIOS_DIM='\033[2m'
DOLIOS_NC='\033[0m'

info()  { echo -e "${DOLIOS_BLUE}[Δ]${DOLIOS_NC} $1"; }
ok()    { echo -e "${DOLIOS_GREEN}[✓]${DOLIOS_NC} $1"; }
err()   { echo -e "${DOLIOS_RED}[✗]${DOLIOS_NC} $1" >&2; }
dim()   { echo -e "${DOLIOS_DIM}    $1${DOLIOS_NC}"; }

echo ""
echo -e "${DOLIOS_BLUE}  Δ DOLIOS${DOLIOS_NC} — The Crafty Agent"
echo -e "  ${DOLIOS_DIM}Scheme. Execute. Deliver.${DOLIOS_NC}"
echo ""

# Step 1: Check prerequisites
info "Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    err "Python 3.12+ required. Install from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    err "Python 3.12+ required (found $PYTHON_VERSION)"
    exit 1
fi
ok "Python $PYTHON_VERSION"

if ! command -v git &>/dev/null; then
    err "git required. Install from https://git-scm.com"
    exit 1
fi
ok "git $(git --version | cut -d' ' -f3)"

# Step 2: Install uv if not present
if ! command -v uv &>/dev/null; then
    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ok "uv installed"
else
    ok "uv $(uv --version 2>/dev/null | head -1)"
fi

# Step 3: Clone Dolios
INSTALL_DIR="${DOLIOS_INSTALL_DIR:-$HOME/dolios}"

if [ -d "$INSTALL_DIR" ]; then
    info "Updating existing installation at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || true
else
    info "Cloning Dolios..."
    git clone https://github.com/dolios-agent/dolios.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Step 4: Initialize submodules (vendor repos)
info "Initializing vendor repos..."
git submodule update --init --recursive 2>/dev/null || {
    dim "Submodules not configured — cloning vendor repos..."
    mkdir -p vendor
    [ -d vendor/hermes-agent ] || git clone https://github.com/NousResearch/hermes-agent.git vendor/hermes-agent
    [ -d vendor/nemoclaw ] || git clone https://github.com/NVIDIA/NemoClaw.git vendor/nemoclaw
    [ -d vendor/hermes-agent-self-evolution ] || git clone https://github.com/NousResearch/hermes-agent-self-evolution.git vendor/hermes-agent-self-evolution
}
ok "Vendor repos ready"

# Step 5: Install dependencies
info "Installing dependencies..."
case "${DOLIOS_INSTALL_OPTIONAL_TOOLS:-0}" in
    1|true|TRUE|yes|YES)
        uv sync --extra optional-tools
        dim "Optional web/image tool dependencies installed"
        ;;
    *)
        uv sync
        dim "Optional web/image tool dependencies skipped (set DOLIOS_INSTALL_OPTIONAL_TOOLS=1 to include)"
        ;;
esac
ok "Dependencies installed"

# Step 6: Create ~/.dolios
mkdir -p "$HOME/.dolios/traces"
ok "Created ~/.dolios"

echo ""
ok "Dolios installed successfully!"
echo ""
echo -e "  ${DOLIOS_DIM}Next steps:${DOLIOS_NC}"
echo -e "  ${DOLIOS_BLUE}cd $INSTALL_DIR${DOLIOS_NC}"
echo -e "  ${DOLIOS_BLUE}dolios setup${DOLIOS_NC}     ${DOLIOS_DIM}# Configure providers${DOLIOS_NC}"
echo -e "  ${DOLIOS_BLUE}dolios${DOLIOS_NC}            ${DOLIOS_DIM}# Start the agent${DOLIOS_NC}"
echo -e "  ${DOLIOS_BLUE}dolios doctor${DOLIOS_NC}     ${DOLIOS_DIM}# Check installation${DOLIOS_NC}"
echo ""
