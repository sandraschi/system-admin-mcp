# Web Dashboard

14-page React SPA for point-and-click Windows system administration.

## Stack

- **React 19** + **TypeScript 5.9**
- **Vite 7** (dev server on port 10860)
- **Tailwind CSS 3** + `tailwindcss-animate`
- **Radix UI** primitives (dialog, dropdown, tabs, tooltip, etc.)
- **TanStack React Query 5** for data fetching
- **Lucide React** icons
- **React Router v7** for routing
- **Biome** for linting

## Dev

```powershell
cd web_sota
npm install
npm run dev        # → http://localhost:10860
```

Proxies `/api` to backend at `http://127.0.0.1:10861`.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Health overview cards |
| `/status` | Status | Detailed system metrics |
| `/processes` | Processes | Process list + detail modal |
| `/services` | Services | Windows services table |
| `/volumes` | Volumes | Volume management |
| `/file-owner` | File Owner | File/folder ownership viewer |
| `/file-recovery` | File Recovery | NTFS recovery interface |
| `/logs` | Logs | System log viewer |
| `/tools` | Tools | Browse MCP tools |
| `/apps` | Apps | Prefab UI apps |
| `/elevated` | Elevated | Elevated ops panel |
| `/chat` | Chat | MCP chat interface |
| `/settings` | Settings | Server config |
| `/help` | Help | Documentation |

## Backend

The backend FastAPI server runs on port 10861. Start it with:

```powershell
# from repo root
uv run system-admin-mcp --web
```

## Production Build

```powershell
npm run build     # outputs to dist/
```

## Linting

```powershell
npm run biome:ci         # check
npm run biome            # auto-fix
```
