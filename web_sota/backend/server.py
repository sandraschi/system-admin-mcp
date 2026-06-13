"""Logging backend for the webapp dashboard."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from web_sota.backend.routes.logging import router as logging_router
from web_sota.backend.log_buffer import activity_log

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.activity_log = activity_log
    log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    activity_log.start_file_watch(log_dir / "server.log")
    activity_log.info("server", "Logging backend started")
    yield
    activity_log.info("server", "Logging backend stopped")

app = FastAPI(title="system-admin-mcp-logging", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(logging_router)

@app.get("/api/llm/providers")
async def llm_providers():
    import httpx
    result = {}
    for name, url in [("ollama", "http://127.0.0.1:11434/api/tags"), ("lm_studio", "http://127.0.0.1:1234/v1/models")]:
        try:
            r = httpx.get(url, timeout=3)
            if r.status_code == 200:
                data = r.json()
                if name == "ollama":
                    result[name] = [{"name": m["name"]} for m in data.get("models", [])]
                else:
                    result[name] = [{"name": m["id"]} for m in data.get("data", [])]
            else:
                result[name] = []
        except Exception:
            result[name] = []
    if not any(result.values()):
        result["ollama"] = [{"name": "llama3.2:3b"}]
    return result

