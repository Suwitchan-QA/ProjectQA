# ============================================================
# ProjectQA — Setup script (Windows PowerShell)
# Run once on a new machine:  .\scripts\setup.ps1
# ============================================================

function log  { Write-Host "[setup] $args" -ForegroundColor Green }
function warn { Write-Host "[warn]  $args" -ForegroundColor Yellow }
function fail { Write-Host "[error] $args" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ProjectQA — Environment Setup (Windows)"  -ForegroundColor Cyan
Write-Host "============================================"
Write-Host ""

# ── 1. Python ────────────────────────────────────────────────
log "Checking Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    fail "Python 3.11+ is required. Install from https://python.org"
}
$pyVersion = python --version
log "$pyVersion found."

# ── 2. Node.js ───────────────────────────────────────────────
log "Checking Node.js..."
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    warn "Node.js not found. Install from https://nodejs.org then re-run this script."
    exit 1
}
log "Node.js $(node --version) found."

# ── 3. Python virtual environment ────────────────────────────
log "Setting up Python virtual environment..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip -q
pip install -r requirements.txt -q
log "Python dependencies installed."

# ── 4. Playwright ────────────────────────────────────────────
log "Installing npm dependencies..."
npm install -q

log "Installing Playwright browsers..."
npx playwright install chromium firefox
log "Playwright browsers installed."

# ── 5. .env file ─────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    warn ".env created from template — fill in your credentials before running agents."
} else {
    log ".env already exists."
}

# ── 6. Security scan ─────────────────────────────────────────
log "Running security scan..."
python scripts/security_scan.py .

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup complete!"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "  1. Fill in .env with real credentials"
Write-Host "  2. Activate venv:  .\.venv\Scripts\Activate.ps1"
Write-Host "  3. Run agent:      python agent.py"
Write-Host "  4. Run tests:      npm test"
Write-Host "============================================"
Write-Host ""
