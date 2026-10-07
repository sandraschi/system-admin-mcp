# Per-repo fleet start config for system-admin-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'system-admin-mcp'
    BackendPort  = 10861
    FrontendPort = 10860
    HealthPath   = '/api/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'system_admin_mcp.server:app'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '10861' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'bun'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
