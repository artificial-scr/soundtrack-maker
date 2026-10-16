#!/usr/bin/env bash
# One-time setup (Linux): checks system tools, creates .venv, installs the pinned Python
# packages and downloads the GeneralUser GS soundfont (verified by SHA-256).
# Safe to re-run: finished steps are skipped.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
SF_DIR="soundfonts"
SF_FILE="$SF_DIR/GeneralUser-GS.sf2"
SF_COMMIT="684543d5e5efaef08d02be50dcda8d552478fa60"   # GeneralUser GS v2.0.3
SF_SHA256="9575028c7a1f589f5770fccc8cff2734566af40cd26ed836944e9a5152688cfe"
SF_URL="https://github.com/mrbumpy409/GeneralUser-GS/raw/$SF_COMMIT/GeneralUser-GS.sf2"
SF_LICENSE_URL="https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/$SF_COMMIT/documentation/LICENSE.txt"

step() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nerror: %s\n' "$*" >&2; exit 1; }

step "Checking system tools"
command -v "$PYTHON" >/dev/null || fail "$PYTHON not found. Install Python 3.11 or newer."
"$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 11))' \
  || fail "Python 3.11+ required, found $("$PYTHON" -V 2>&1). Set PYTHON=/path/to/python3.11 and re-run."
"$PYTHON" -c 'import venv, ensurepip' 2>/dev/null \
  || fail "Python venv support missing. On Debian/Ubuntu: sudo apt install python3-venv"
command -v fluidsynth >/dev/null \
  || fail "FluidSynth not found. On Debian/Ubuntu: sudo apt install fluidsynth   (Fedora: sudo dnf install fluidsynth, Arch: sudo pacman -S fluidsynth)"
command -v curl >/dev/null || fail "curl not found. On Debian/Ubuntu: sudo apt install curl"
echo "python: $("$PYTHON" -V 2>&1)   fluidsynth: $(fluidsynth --version 2>/dev/null | head -1)"

step "Python virtual environment (.venv)"
if [[ ! -x .venv/bin/python ]]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "installed $(wc -l < requirements.txt) pinned packages"

step "Soundfont: GeneralUser GS v2.0.3"
mkdir -p "$SF_DIR"
if [[ -f "$SF_FILE" ]] && echo "$SF_SHA256  $SF_FILE" | sha256sum --check --status; then
  echo "already present and verified"
else
  curl -fL --progress-bar -o "$SF_FILE.part" "$SF_URL"
  echo "$SF_SHA256  $SF_FILE.part" | sha256sum --check --status \
    || { rm -f "$SF_FILE.part"; fail "soundfont checksum mismatch; download aborted"; }
  mv "$SF_FILE.part" "$SF_FILE"
  curl -fsSL -o "$SF_DIR/GeneralUser-GS-LICENSE.txt" "$SF_LICENSE_URL"
  echo "downloaded and verified"
fi

step "Done"
cat <<'EOF'
Try:
  make list                              # levels, keys, tempos
  make level LEVEL=meadow SEEDS=1-4      # generate a few seeds of one level
  make check LEVEL=meadow                # technical checks
EOF
