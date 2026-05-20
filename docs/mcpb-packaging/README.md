# MCPB Packaging

This server supports MCPB (Claude Desktop bundle) packaging via the Anthropic `mcpb` CLI tool.

## Build

```powershell
# From repo root
just mcpb-pack

# Or manually
uv run python mcpb_build.py
```

Output: `dist/system-admin-mcp-v0.4.0.mcpb`

## Structure

```
mcpb/
├── manifest.json          # v0.2 standard
├── server/
│   └── __main__.py        # Runtime entry point
└── assets/prompts/
    ├── system.md          # Core capabilities (3000+ words)
    ├── user.md            # Tutorials (4000+ words)
    ├── examples.json      # 100+ tool call mappings
    ├── file_recovery.md   # Domain guide
    ├── security_management.md
    ├── system_diagnostics.md
    ├── troubleshooting.md
    └── volume_maintenance.md
```

## Use with Claude Desktop

Drag `dist/system-admin-mcp-v0.4.0.mcpb` into Claude Desktop, or configure via `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "system-admin-mcp": {
      "command": "uvx",
      "args": ["system-admin-mcp"]
    }
  }
}
```

## .mcpbignore

Defined at repo root. Excludes `.venv`, `node_modules/`, `tests/`, `docs/`, `target/`, `__pycache__/`, and other build artifacts per SOTA MCPB_PACKAGING_STANDARDS.md v2.0.
