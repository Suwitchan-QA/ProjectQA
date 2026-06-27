#!/bin/bash
# ============================================================
# ProjectQA — Setup script (Mac / Linux)
# Run once on a new machine:  bash scripts/setup.sh
# ============================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[setup]${NC} $1"; }
warn() { echo -e "${YELLOW}[warn] ${NC} $1"; }
fail() { echo -e "${RED}[error]${NC} $1"; exit 1; }

echo ""
echo "============================================"
echo "  ProjectQA — Environment Setup"
echo "============================================"
echo ""

# ── 1. Python ────────────────────────────────────────────────
log "Checking Python..."
if ! command -v python3 &>/dev/null; then
  fail "Python 3.11+ is required. Install from https://python.org"
fi
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log "Python $PY_VERSION found."

# ── 2. Node.js / nvm ─────────────────────────────────────────
log "Checking Node.js..."
if ! command -v node &>/dev/null; then
  warn "Node.js not found. Installing via nvm..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm install --lts
else
  log "Node.js $(node --version) found."
fi

# ── 3. Python virtual environment ────────────────────────────
log "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "Python dependencies installed."

# ── 4. Playwright browsers ───────────────────────────────────
log "Installing npm dependencies..."
npm install -q

log "Installing Playwright browsers (chromium, firefox)..."
npx playwright install chromium firefox
log "Playwright browsers installed."

# ── 5. .env file ─────────────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  warn ".env created from template — fill in your credentials before running agents."
else
  log ".env already exists."
fi

# ── 6. Git hooks ─────────────────────────────────────────────
log "Installing pre-commit security hook..."
cp .git-hooks/pre-commit .git/hooks/pre-commit 2>/dev/null || true
chmod +x .git/hooks/pre-commit 2>/dev/null || true
log "Pre-commit hook installed."

# ── 7. Security scan ─────────────────────────────────────────
log "Running security scan..."
python scripts/security_scan.py . && log "Security scan passed." || warn "Review findings above before proceeding."

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Fill in .env with real credentials"
echo "  2. Activate venv:  source .venv/bin/activate"
echo "  3. Run agent:      python agent.py"
echo "  4. Run tests:      npm test"
echo "============================================"
echo ""
