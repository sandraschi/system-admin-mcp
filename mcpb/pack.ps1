#Requires -Version 5.1
# Shim (fleet rule: never vendor the pack pipeline here).
# fleet.just `mcpb-pack` invokes this path. The canonical pipeline
# (mcp-central-docs/scripts/fleet-mcpb-pack.ps1) does fresh-copy, import
# isolation, AST + pollution checks, the launch check, and emits the stable
# <name>.mcpb + install.ps1 assets — fixes apply fleet-wide.
$central = Join-Path (Split-Path -Parent $PSScriptRoot | Split-Path -Parent) 'mcp-central-docs\scripts\fleet-mcpb-pack.ps1'
if (-not (Test-Path -LiteralPath $central)) { throw "Canonical pack script missing: $central (clone mcp-central-docs next to this repo)" }
& $central -RepoRoot (Split-Path -Parent $PSScriptRoot)
exit $LASTEXITCODE
