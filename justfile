set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff linting (Python backend)
lint-python:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .

# Execute Biome linting (webapp frontend, uses local binary)
lint-web:
    Set-Location '{{justfile_directory()}}\web_sota'
    & "node_modules\.bin\biome" ci .

# Run all linters (Python + webapp)
lint: lint-python lint-web

# Auto-fix Python linting and formatting
fix-python:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .

# Auto-fix webapp formatting
fix-web:
    Set-Location '{{justfile_directory()}}\web_sota'
    & "node_modules\.bin\biome" check --write --unsafe .

# Auto-fix all issues (Python + webapp)
fix: fix-python fix-web

# Alias for fix
format: fix

# Run all quality checks (lint + test)
check: lint test

# ── Testing ───────────────────────────────────────────────────────────────────

# Run all tests
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -v

# Run tests with coverage report
test-cov:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ --cov=system_admin_mcp --cov-report=term --cov-report=html

# ── Build & Sync ──────────────────────────────────────────────────────────────

# Sync dependencies and install package
build:
    Set-Location '{{justfile_directory()}}'
    uv sync

# Sync with all extras (dev)
build-dev:
    Set-Location '{{justfile_directory()}}'
    uv sync --all-extras

# Install npm dependencies for webapp
web-install:
    Set-Location '{{justfile_directory()}}\web_sota'
    npm install

# Full setup from scratch (Python + webapp)
setup:
    Set-Location '{{justfile_directory()}}'
    uv sync --all-extras
    Set-Location '{{justfile_directory()}}\web_sota'
    npm install
    Write-Host "Setup complete. Run 'just dev' to start." -ForegroundColor Green

# ── Development ───────────────────────────────────────────────────────────────

# Start MCP server in stdio mode (Claude Desktop)
run:
    Set-Location '{{justfile_directory()}}'
    uv run system-admin-mcp

# Alias for run
dev: run

# Start MCP server in HTTP mode on MCP_PORT (default 10861)
serve:
    Set-Location '{{justfile_directory()}}'
    uv run system-admin-mcp --http

# Start FastAPI web backend on WEBAPP_PORT (default 10861)
web:
    Set-Location '{{justfile_directory()}}'
    uv run system-admin-mcp --web

# Start webapp frontend dev server on port 10860
web-frontend:
    Set-Location '{{justfile_directory()}}\web_sota'
    npm run dev

# Check Python venv is ready and admin status
info:
    Set-Location '{{justfile_directory()}}'
    Write-Host "Python: $(uv run python --version)" -ForegroundColor Cyan
    Write-Host "uv: $(uv --version)" -ForegroundColor Cyan
    Write-Host "Ruff: $(uv run ruff --version)" -ForegroundColor Cyan
    $admin = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($admin) { Write-Host "Admin: YES" -ForegroundColor Green } else { Write-Host "Admin: NO (run as Administrator!)" -ForegroundColor Red }
    Write-Host "Server ports: 10860 (frontend) / 10861 (backend)" -ForegroundColor Gray

# ── MCPB Packaging ────────────────────────────────────────────────────────────

# Build MCPB package for Claude Desktop
mcpb-pack:
    Set-Location '{{justfile_directory()}}'
    uv run python mcpb_build.py

# Validate MCPB manifest
mcpb-validate:
    Set-Location '{{justfile_directory()}}'
    uv run python -c "import json; m=json.load(open('mcpb/manifest.json')); print(f'Manifest OK: {m[\"name\"]} v{m[\"version\"]}, type={m[\"server\"][\"type\"]}')"

# ── Housekeeping ──────────────────────────────────────────────────────────────

# Remove build artifacts and caches
clean:
    Set-Location '{{justfile_directory()}}'
    Remove-Item -Recurse -Force dist, build, htmlcov, .ruff_cache, .pytest_cache, "src/*.egg-info" -ErrorAction SilentlyContinue
    Write-Host "Cleaned build artifacts" -ForegroundColor Yellow

# Remove all generated files including .bak and node_modules
clean-all: clean
    Set-Location '{{justfile_directory()}}'
    Remove-Item -Recurse -Force "**/*.bak" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force web_sota/node_modules -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
    Remove-Item -Force coverage.xml -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force target -ErrorAction SilentlyContinue
    Write-Host "Cleaned all generated files" -ForegroundColor Yellow

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# ── Tauri Native ───────────────────────────────────────────────────────────────

# Build Tauri native desktop app (full pipeline: frontend + backend)
build-native:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npx @tauri-apps/cli build

# Run the CUA smoke test against the installed NSIS app
cua-nsis-test:
    uv run python scripts/cua-smoke.py
# ── Playwright E2E ─────────────────────────────────────────────────────

# Install Playwright browsers (one-time)
e2e-install:
    cd {{REPO}}\web_sota
    npx playwright install chromium

# Run Playwright E2E smoke tests (start backend first: just serve)
e2e:
    cd {{REPO}}\web_sota
    npx playwright test

