#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This setup script is for Linux. The source uses the Brother QL Linux kernel backend." >&2
    exit 1
fi

has_sudo() {
    command -v sudo >/dev/null 2>&1
}

install_system_packages() {
    if command -v apt-get >/dev/null 2>&1; then
        if has_sudo; then SUDO=sudo; elif [[ "$EUID" -eq 0 ]]; then SUDO=; else
            echo "Install these system packages, then rerun this script:" >&2
            echo "  python3 python3-venv python3-tk python3-pip git" >&2
            exit 1
        fi
        $SUDO apt-get update
        $SUDO apt-get install -y python3 python3-venv python3-tk python3-pip git
    elif command -v dnf >/dev/null 2>&1; then
        if has_sudo; then SUDO=sudo; elif [[ "$EUID" -eq 0 ]]; then SUDO=; else
            echo "Install these system packages, then rerun this script:" >&2
            echo "  python3 python3-pip python3-tkinter git" >&2
            exit 1
        fi
        $SUDO dnf install -y python3 python3-pip python3-tkinter git
    elif command -v pacman >/dev/null 2>&1; then
        if has_sudo; then SUDO=sudo; elif [[ "$EUID" -eq 0 ]]; then SUDO=; else
            echo "Install python, python-pip, tk, and git using pacman, then rerun." >&2
            exit 1
        fi
        $SUDO pacman -Sy --needed python python-pip tk git
    else
        echo "Unsupported package manager. Install Python 3, venv/pip, Tkinter, and Git manually." >&2
        exit 1
    fi
}

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 was not found. Installing basic system packages..."
    install_system_packages
else
    # Make sure the GUI dependency (Tkinter) is available on common Linux distributions.
    if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
        echo "Tkinter is missing; installing Linux system packages..."
        install_system_packages
    fi
fi

if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
    if ! python3 -m venv "$ROOT_DIR/.venv"; then
        echo "Creating a virtual environment failed; installing venv packages and retrying..."
        install_system_packages
        python3 -m venv "$ROOT_DIR/.venv"
    fi
fi

PY="$ROOT_DIR/.venv/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$ROOT_DIR/requirements.txt"

# The included RFID wheel is native and only matches CPython 3.14 on Linux x86_64.
# Skip it on other systems so the printer and manual PID entry remain usable.
WHEEL="$ROOT_DIR/vendor/rfid_m7e_hecto-1.0.0-cp314-none-linux_x86_64.whl"
PY_TAG="$("$PY" -c 'import sys; print(f"cp{sys.version_info.major}{sys.version_info.minor}")')"
ARCH="$(uname -m)"
if [[ -f "$WHEEL" && "$PY_TAG" == "cp314" && "$ARCH" == "x86_64" ]]; then
    echo "Installing the included RFID package for CPython 3.14 / Linux x86_64..."
   "$PY" -m pip install --force-reinstall --no-deps "$WHEEL"
else
    echo "NOTE: The included RFID wheel is for CPython 3.14 on Linux x86_64."
    echo "Current environment: Python $PY_TAG, architecture $ARCH."
    echo "RFID reading will be unavailable unless a compatible RFID package is installed."
    echo "The GUI and command-line tool still support manual PID entry."
fi

DEVICE="${LABEL_PRINTER_DEVICE:-/dev/usb/lp0}"
if [[ -e "$DEVICE" ]]; then
    echo "Printer device found: $DEVICE"
    ls -l "$DEVICE" || true
else
    echo "NOTE: Printer device '$DEVICE' was not found during setup."
    echo "Connect the Brother printer or set LABEL_PRINTER_DEVICE to its actual path."
fi

if [[ -e "$ROOT_DIR/UR_Logo.jpg" ]]; then
    echo "University logo found: UR_Logo.jpg"
else
    echo "NOTE: UR_Logo.jpg is not bundled with this package."
    echo "Copy it from your existing project into: $ROOT_DIR/UR_Logo.jpg"
    echo "The app works without the logo, but no logo will print until it is added."
fi

echo
echo "Installation is complete."
echo "Launch GUI:          ./run_gui.sh"
echo "Command-line labels:  ./run_cli.sh"
echo "Printer test:        ./run_printer_test.sh"
