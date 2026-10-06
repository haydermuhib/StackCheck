#!/usr/bin/env bash
# StackCheck: Tech Stack Market Intelligence Engine
# Universal Portable Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/haydermuhib/StackCheck/main/install.sh | bash

set -e

REPO_OWNER="${REPO_OWNER:-haydermuhib}"
REPO_NAME="StackCheck"
BINARY_NAME="stackcheck"

# Terminal formatting
if [ -t 1 ]; then
    BOLD="$(printf '\033[1m')"
    DIM="$(printf '\033[2m')"
    GREEN="$(printf '\033[38;2;52;211;153m')"
    CYAN="$(printf '\033[38;2;56;189;248m')"
    YELLOW="$(printf '\033[38;2;251;191;36m')"
    RED="$(printf '\033[38;2;248;113;113m')"
    RESET="$(printf '\033[0m')"
else
    BOLD=""
    DIM=""
    GREEN=""
    CYAN=""
    YELLOW=""
    RED=""
    RESET=""
fi

step_header() {
    local step="$1"
    local title="$2"
    printf "%b[%s]%b %b%s%b\n" "$CYAN$BOLD" "$step" "$RESET" "$BOLD" "$title" "$RESET"
}

step_item() {
    local message="$1"
    printf "  %b✔%b %b\n" "$GREEN" "$RESET" "$message"
}

step_warn() {
    local message="$1"
    printf "  %b!%b %b\n" "$YELLOW" "$RESET" "$message"
}

step_error() {
    local message="$1"
    printf "  %bx%b %b\n" "$RED" "$RESET" "$message"
}

printf "\n"
printf "%b┌──────────────────────────────────────────────────────────┐%b\n" "$CYAN$BOLD" "$RESET"
printf "%b│%b   %bStackCheck%b: %bTech Stack Market Intelligence Engine%b     %b│%b\n" "$CYAN$BOLD" "$RESET" "$BOLD" "$RESET" "$DIM" "$RESET" "$CYAN$BOLD" "$RESET"
printf "%b└──────────────────────────────────────────────────────────┘%b\n" "$CYAN$BOLD" "$RESET"
printf "\n"

# -------------------------------------------------------------
# STEP 1: Detect Platform and Architecture
# -------------------------------------------------------------
step_header "1/4" "Detecting system platform..."

OS="$(uname -s)"
case "$OS" in
    Linux)
        OS_TYPE="linux"
        ;;
    Darwin)
        OS_TYPE="macos"
        ;;
    *)
        step_error "Unsupported operating system: $OS"
        printf "StackCheck supports Linux and macOS through this installer.\n"
        printf "For Windows, download StackCheck-windows-x64.exe from GitHub Releases.\n"
        exit 1
        ;;
esac

ARCH="$(uname -m)"
case "$ARCH" in
    x86_64|amd64)
        TARGET_ARCH="x64"
        ;;
    aarch64|arm64)
        TARGET_ARCH="arm64"
        ;;
    *)
        step_error "Unsupported CPU architecture: $ARCH"
        exit 1
        ;;
esac

step_item "Platform verified: ${BOLD}${OS_TYPE} (${TARGET_ARCH})${RESET}"

# -------------------------------------------------------------
# STEP 2: Configure Target Directories
# -------------------------------------------------------------
step_header "2/4" "Setting up installation directories..."

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

step_item "Target directory: ${DIM}${INSTALL_DIR}${RESET}"

# -------------------------------------------------------------
# STEP 3: Download Binary with Active Progress Bar
# -------------------------------------------------------------
step_header "3/4" "Downloading release binary from GitHub..."

DOWNLOADER=""
if command -v curl >/dev/null 2>&1; then
    DOWNLOADER="curl"
elif command -v wget >/dev/null 2>&1; then
    DOWNLOADER="wget"
else
    step_error "Neither curl nor wget was found. Please install curl or wget."
    exit 1
fi

ARTIFACT_NAME="StackCheck-${OS_TYPE}-${TARGET_ARCH}"
if [ "$OS_TYPE" = "windows" ]; then
    ARTIFACT_NAME="${ARTIFACT_NAME}.exe"
fi

RELEASE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/latest/download/${ARTIFACT_NAME}"
FALLBACK_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/latest/download/StackCheck"

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

printf "  Fetching: %s\n" "$ARTIFACT_NAME"

download_with_progress() {
    local url="$1"
    local dest="$2"
    if [ "$DOWNLOADER" = "curl" ]; then
        if ! curl -s -f -I -L "$url" >/dev/null 2>&1; then
            return 1
        fi
        if [ -t 1 ]; then
            curl -# -f -L -o "$dest" "$url"
        else
            curl -sSL -f -o "$dest" "$url"
        fi
    else
        if ! wget --spider -q "$url" >/dev/null 2>&1; then
            return 1
        fi
        if [ -t 1 ]; then
            wget --show-progress -q -O "$dest" "$url"
        else
            wget -q -O "$dest" "$url"
        fi
    fi
}

INSTALLED_SUCCESS=0

if download_with_progress "$RELEASE_URL" "$TEMP_DIR/$BINARY_NAME"; then
    mv "$TEMP_DIR/$BINARY_NAME" "$INSTALL_DIR/$BINARY_NAME"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    INSTALLED_SUCCESS=1
elif download_with_progress "$FALLBACK_URL" "$TEMP_DIR/$BINARY_NAME"; then
    mv "$TEMP_DIR/$BINARY_NAME" "$INSTALL_DIR/$BINARY_NAME"
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    INSTALLED_SUCCESS=1
fi

# Fallback: if release binary is not yet available, build via virtualenv
if [ "$INSTALLED_SUCCESS" -eq 0 ]; then
    step_warn "Prebuilt GitHub binary for ${OS_TYPE} (${TARGET_ARCH}) not found. Setting up Python runtime..."
    
    PYTHON_CMD=""
    for cmd in python3.12 python3.11 python3.10 python3 python; do
        if command -v "$cmd" >/dev/null 2>&1; then
            PYTHON_CMD="$cmd"
            break
        fi
    done

    if [ -n "$PYTHON_CMD" ]; then
        step_item "Using system Python: $($PYTHON_CMD --version)"
        VENV_DIR="$HOME/.local/share/stackcheck/env"
        mkdir -p "$(dirname "$VENV_DIR")"
        "$PYTHON_CMD" -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip --quiet
        "$VENV_DIR/bin/pip" install "git+https://github.com/${REPO_OWNER}/${REPO_NAME}.git" --quiet
        
        cat <<EOF > "$INSTALL_DIR/$BINARY_NAME"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/stackcheck" "\$@"
EOF
        chmod +x "$INSTALL_DIR/$BINARY_NAME"
        INSTALLED_SUCCESS=1
    else
        step_error "Neither prebuilt binary nor Python 3.10+ was found."
        printf "Check release binaries at: https://github.com/%s/%s/releases\n" "$REPO_OWNER" "$REPO_NAME"
        exit 1
    fi
fi

step_item "Binary installed and verified"

# -------------------------------------------------------------
# STEP 4: Desktop Launcher and Icon Registration
# -------------------------------------------------------------
step_header "4/4" "Configuring application shortcuts..."

if [ "$OS_TYPE" = "linux" ]; then
    # Generate official Strata S vector icon
    cat <<'EOF' > "$ICONS_DIR/stackcheck.svg"
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-labelledby="icon-title">
  <title id="icon-title">StackCheck Icon</title>
  <g id="symbol">
    <path fill="#38BDF8" d="M 92 44 H 212 V 84 H 88 V 92 H 44 V 84 L 84 44 Z"/>
    <path fill="#0EA5E9" d="M 44 104 H 88 L 168 144 V 152 H 124 L 44 112 Z"/>
    <path fill="#0284C7" d="M 168 164 H 212 V 172 L 172 212 H 44 V 172 H 168 Z"/>
  </g>
</svg>
EOF

    cp "$ICONS_DIR/stackcheck.svg" "$PIXMAPS_DIR/stackcheck.svg" 2>/dev/null || true
    if [ "$EUID" -ne 0 ]; then
        mkdir -p "$HOME/.local/share/icons"
        cp "$ICONS_DIR/stackcheck.svg" "$HOME/.local/share/icons/stackcheck.svg" 2>/dev/null || true
    fi

    # Register Desktop Launcher
    cat <<EOF > "$APPS_DIR/stackcheck.desktop"
[Desktop Entry]
Type=Application
Name=StackCheck
Comment=Tech Stack Market Intelligence Engine and Data Dashboard
Exec=$INSTALL_DIR/$BINARY_NAME
Icon=$ICONS_DIR/stackcheck.svg
Categories=Development;Office;Utility;DataVisualization;
Terminal=false
StartupNotify=true
EOF
    chmod +x "$APPS_DIR/stackcheck.desktop"

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPS_DIR" 2>/dev/null || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi
    step_item "Registered desktop application launcher and SVG icon"
fi

# Check PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    step_warn "$INSTALL_DIR is not yet in your PATH."
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$rc" ] && ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$rc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
            step_item "Added $INSTALL_DIR to $(basename "$rc")"
        fi
    done
fi

printf "\n"
printf "%b┌──────────────────────────────────────────────────────────┐%b\n" "$GREEN$BOLD" "$RESET"
printf "%b│%b  %b✔ StackCheck installed successfully.%b                   %b│%b\n" "$GREEN$BOLD" "$RESET" "$GREEN" "$RESET" "$GREEN$BOLD" "$RESET"
printf "%b└──────────────────────────────────────────────────────────┘%b\n" "$GREEN$BOLD" "$RESET"
printf "\n"
printf "  %bInstalled binary:%b %s\n" "$BOLD" "$RESET" "$INSTALL_DIR/$BINARY_NAME"
if [ "$OS_TYPE" = "linux" ]; then
    printf "  %bDesktop application:%b %s\n" "$BOLD" "$RESET" "$APPS_DIR/stackcheck.desktop"
fi
printf "\n"
printf "  %bAvailable commands:%b\n" "$BOLD" "$RESET"
printf "    %bstackcheck%b         Launch interactive web dashboard\n" "$CYAN" "$RESET"
printf "    %bstackcheck search%b  Query live job demand in terminal\n" "$CYAN" "$RESET"
printf "    %bstackcheck status%b  Check server status\n" "$CYAN" "$RESET"
printf "    %bstackcheck stop%b    Stop dashboard server\n" "$CYAN" "$RESET"
printf "    %bstackcheck update%b  Check and install updates\n" "$CYAN" "$RESET"
printf "\n"
