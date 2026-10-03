#!/usr/bin/env bash
# StackCheck - Tech Stack Market Intelligence Engine
# Universal 1-line portable installer script
# Usage: curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash

set -e

REPO_OWNER="${REPO_OWNER:-haydermuhib}"
REPO_NAME="StackCheck"
BINARY_NAME="stackcheck"

# Colors
GREEN='\033[0;32m'
CYAN='\033[1;36m'
PURPLE='\033[1;35m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}        📊 StackCheck Portable Installer            ${NC}"
echo -e "${CYAN}====================================================${NC}"

# 1. Detect Operating System
OS="$(uname -s)"
case "$OS" in
    Linux)
        OS_TYPE="linux"
        ;;
    Darwin)
        OS_TYPE="macos"
        ;;
    *)
        echo -e "${RED}Error: Unsupported operating system: $OS${NC}"
        echo -e "StackCheck supports Linux and macOS via this installer."
        echo -e "For Windows, download StackCheck-windows-x64.exe from GitHub Releases."
        exit 1
        ;;
esac

# 2. Detect CPU Architecture
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64|amd64)
        TARGET_ARCH="x64"
        ;;
    aarch64|arm64)
        TARGET_ARCH="arm64"
        ;;
    *)
        echo -e "${RED}Error: Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

echo -e "Detected platform: ${GREEN}$OS_TYPE ($TARGET_ARCH)${NC}"

# 3. Determine Installation Directories
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/bin"
    APPS_DIR="/usr/local/share/applications"
    ICONS_DIR="/usr/local/share/icons/hicolor/scalable/apps"
    PIXMAPS_DIR="/usr/local/share/pixmaps"
else
    INSTALL_DIR="$HOME/.local/bin"
    APPS_DIR="$HOME/.local/share/applications"
    ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
    PIXMAPS_DIR="$HOME/.local/share/pixmaps"
fi

mkdir -p "$INSTALL_DIR"
if [ "$OS_TYPE" = "linux" ]; then
    mkdir -p "$APPS_DIR"
    mkdir -p "$ICONS_DIR"
    mkdir -p "$PIXMAPS_DIR"
fi

# 4. Check Download Tools
DOWNLOADER=""
if command -v curl >/dev/null 2>&1; then
    DOWNLOADER="curl"
elif command -v wget >/dev/null 2>&1; then
    DOWNLOADER="wget"
else
    echo -e "${RED}Error: neither curl nor wget was found. Please install curl or wget.${NC}"
    exit 1
fi

# 5. Fetch and Download Release Binary
ARTIFACT_NAME="StackCheck-${OS_TYPE}-${TARGET_ARCH}"
RELEASE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/latest/download/${ARTIFACT_NAME}"
FALLBACK_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/latest/download/StackCheck"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

INSTALLED_SUCCESS=0

echo -e "Fetching latest release binary: ${CYAN}${ARTIFACT_NAME}${NC}..."

download_file() {
    local url="$1"
    local dest="$2"
    if [ "$DOWNLOADER" = "curl" ]; then
        curl -fsSL -o "$dest" "$url" 2>/dev/null
    else
        wget -q -O "$dest" "$url" 2>/dev/null
    fi
}

if download_file "$RELEASE_URL" "$TEMP_DIR/$BINARY_NAME"; then
    mv "$TEMP_DIR/$BINARY_NAME" "$INSTALL_DIR/$BINARY_NAME"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    INSTALLED_SUCCESS=1
elif download_file "$FALLBACK_URL" "$TEMP_DIR/$BINARY_NAME"; then
    mv "$TEMP_DIR/$BINARY_NAME" "$INSTALL_DIR/$BINARY_NAME"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    INSTALLED_SUCCESS=1
fi

# 6. Fallback: If precompiled binary is not yet published on GitHub, install via Python venv
if [ "$INSTALLED_SUCCESS" -eq 0 ]; then
    echo -e "${YELLOW}Prebuilt binary not found on GitHub Releases.${NC}"
    echo -e "${CYAN}Falling back to portable Python environment build...${NC}"
    
    PYTHON_CMD=""
    for cmd in python3.12 python3.11 python3.10 python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            PYTHON_CMD="$cmd"
            break
        fi
    done

    if [ -n "$PYTHON_CMD" ]; then
        echo -e "Using Python: ${GREEN}$($PYTHON_CMD --version)${NC}"
        VENV_DIR="$HOME/.local/share/stackcheck/env"
        mkdir -p "$(dirname "$VENV_DIR")"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip --quiet
        "$VENV_DIR/bin/pip" install "git+https://github.com/${REPO_OWNER}/${REPO_NAME}.git" --quiet
        
        # Create portable runner shim in INSTALL_DIR
        cat <<EOF > "$INSTALL_DIR/$BINARY_NAME"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/stackcheck" "\$@"
EOF
        chmod +x "$INSTALL_DIR/$BINARY_NAME"
        INSTALLED_SUCCESS=1
    else
        echo -e "${RED}Error: Neither prebuilt binary nor Python 3.10+ was found.${NC}"
        echo -e "Please check releases at: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases"
        exit 1
    fi
fi

# 7. Install Application Icon and Desktop Launcher (Linux only)
if [ "$OS_TYPE" = "linux" ]; then
    # Fetch or generate high-fidelity SVG icon
    cat <<'EOF' > "$ICONS_DIR/stackcheck.svg"
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0c1322"/>
      <stop offset="45%" stop-color="#070c17"/>
      <stop offset="100%" stop-color="#020408"/>
    </linearGradient>
    <linearGradient id="border-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.5"/>
      <stop offset="30%" stop-color="#818cf8" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.9"/>
    </linearGradient>
    <linearGradient id="l1-top" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <linearGradient id="l1-left" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0284c7"/>
      <stop offset="100%" stop-color="#075985"/>
    </linearGradient>
    <linearGradient id="l1-right" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0369a1"/>
      <stop offset="100%" stop-color="#0c4a6e"/>
    </linearGradient>
    <linearGradient id="l2-top" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34d399"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <linearGradient id="l2-left" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#065f46"/>
    </linearGradient>
    <linearGradient id="l2-right" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#047857"/>
      <stop offset="100%" stop-color="#064e3b"/>
    </linearGradient>
    <linearGradient id="l3-top" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#7c3aed"/>
    </linearGradient>
    <linearGradient id="l3-left" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#7c3aed"/>
      <stop offset="100%" stop-color="#5b21b6"/>
    </linearGradient>
    <linearGradient id="l3-right" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#6d28d9"/>
      <stop offset="100%" stop-color="#4c1d95"/>
    </linearGradient>
    <linearGradient id="l4-top" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6366f1"/>
      <stop offset="100%" stop-color="#4f46e5"/>
    </linearGradient>
    <linearGradient id="l4-left" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#4f46e5"/>
      <stop offset="100%" stop-color="#3730a3"/>
    </linearGradient>
    <linearGradient id="l4-right" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#4338ca"/>
      <stop offset="100%" stop-color="#312e81"/>
    </linearGradient>
    <linearGradient id="check-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#67e8f9"/>
      <stop offset="50%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#a7f3d0"/>
    </linearGradient>
  </defs>
  <rect x="20" y="20" width="472" height="472" rx="108" fill="url(#bg-grad)" stroke="url(#border-grad)" stroke-width="2.5"/>
  <ellipse cx="256" cy="260" rx="150" ry="100" fill="#0284c7" opacity="0.14"/>
  <path d="M 136 340 L 256 394 L 256 410 L 136 356 Z" fill="url(#l4-left)"/>
  <path d="M 256 394 L 376 340 L 376 356 L 256 410 Z" fill="url(#l4-right)"/>
  <path d="M 256 286 L 376 340 L 256 394 L 136 340 Z" fill="url(#l4-top)"/>
  <path d="M 136 285 L 256 339 L 256 355 L 136 301 Z" fill="url(#l3-left)"/>
  <path d="M 256 339 L 376 285 L 376 301 L 256 355 Z" fill="url(#l3-right)"/>
  <path d="M 256 231 L 376 285 L 256 339 L 136 285 Z" fill="url(#l3-top)"/>
  <path d="M 136 230 L 256 284 L 256 300 L 136 246 Z" fill="url(#l2-left)"/>
  <path d="M 256 284 L 376 230 L 376 246 L 256 300 Z" fill="url(#l2-right)"/>
  <path d="M 256 176 L 376 230 L 256 284 L 136 230 Z" fill="url(#l2-top)"/>
  <path d="M 136 175 L 256 229 L 256 245 L 136 191 Z" fill="url(#l1-left)"/>
  <path d="M 256 229 L 376 175 L 376 191 L 256 245 Z" fill="url(#l1-right)"/>
  <path d="M 256 121 L 376 175 L 256 229 L 136 175 Z" fill="url(#l1-top)"/>
  <path d="M 256 133 L 350 175 L 256 217 L 162 175 Z" fill="#ffffff" opacity="0.18"/>
  <path d="M 198 168 L 242 202 L 320 132" fill="none" stroke="#000000" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" opacity="0.4"/>
  <path d="M 198 165 L 242 199 L 320 129" fill="none" stroke="url(#check-grad)" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M 198 165 L 242 199 L 320 129" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/>
  <circle cx="320" cy="129" r="3.5" fill="#ffffff"/>
</svg>
EOF

    cp "$ICONS_DIR/stackcheck.svg" "$PIXMAPS_DIR/stackcheck.svg" 2>/dev/null || true
    if [ "$EUID" -ne 0 ]; then
        mkdir -p "$HOME/.local/share/icons"
        cp "$ICONS_DIR/stackcheck.svg" "$HOME/.local/share/icons/stackcheck.svg" 2>/dev/null || true
    fi

    # 8. Register Desktop Launcher
    cat <<EOF > "$APPS_DIR/stackcheck.desktop"
[Desktop Entry]
Type=Application
Name=StackCheck
Comment=Tech Stack Market Intelligence Engine & Data Dashboard
Exec=$INSTALL_DIR/$BINARY_NAME
Icon=$ICONS_DIR/stackcheck.svg
Categories=Development;Office;Utility;DataVisualization;
Terminal=false
StartupNotify=true
EOF
    chmod +x "$APPS_DIR/stackcheck.desktop"

    # Update system desktop & icon cache
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPS_DIR" 2>/dev/null || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi
fi

# 9. Check PATH configuration
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}Notice: $INSTALL_DIR is not in your PATH.${NC}"
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$rc" ] && ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$rc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
            echo -e "Added ~/.local/bin to $(basename "$rc")"
        fi
    done
fi

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}  🎉 StackCheck was successfully installed!          ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "Portable binary at: ${CYAN}$INSTALL_DIR/$BINARY_NAME${NC}"
if [ "$OS_TYPE" = "linux" ]; then
    echo -e "Desktop launcher:   ${CYAN}$APPS_DIR/stackcheck.desktop${NC}"
    echo -e "Application icon:   ${CYAN}$ICONS_DIR/stackcheck.svg${NC}"
fi

echo -e "\n🚀 Launch Dashboard:  ${GREEN}stackcheck${NC}"
echo -e "🔍 CLI Scrape & Test: ${GREEN}stackcheck scrape \"Data Engineer\" --location Pakistan${NC}"
echo -e "🔄 Check for Updates: ${GREEN}stackcheck update${NC}\n"
