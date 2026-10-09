; Fleet NSIS hooks: kill procs + register/unregister in AI clients.
; mcp-clients.nsh is vendored from mcp-central-docs/scripts/nsis/ (NOREG retrofit
; 2026-10-09). The custom NSIS_HOOK_PAGES page needs the patched Tauri template
; (scripts/patch-nsis-template.ps1) — not wired here — so installs register by
; default (McpRegState empty != "0") and silent installs behave the same.

!define MCP_REG_NAME "system-admin-mcp"
!define MCP_REG_EXE "system-admin-mcp-backend.exe"
!include "mcp-clients.nsh"

!macro KillProcesses
  DetailPrint "Stopping processes..."
  ExecWait 'taskkill /F /IM "system-admin-mcp-backend.exe" /T' $0
  ExecWait 'taskkill /F /IM "system-admin-mcp-native.exe" /T' $0
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  !insertmacro McpClientsRegister
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillProcesses
  !insertmacro McpClientsUnregister
!macroend
