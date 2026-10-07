"""Unified local + cloud LLM provider registry, keystore, and chat proxy helpers.

Vendored from the arxiv-mcp pilot (docs/SPEC-llm-providers.md) with the settings
layer replaced: the webapp never talks to providers from the browser. All traffic
goes through the backend, and API keys live in a 0600 keystore under the repo
data dir (or env vars, which win). SYSTEMADMIN_LLM_KEYSTORE overrides the path
(used by tests to isolate the real keystore).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

LOCAL_PROBE_TIMEOUT = 3.0
CLOUD_TIMEOUT = 30.0
CHAT_TIMEOUT = 120.0
KEYSTORE_NAME = "llm_keys.json"
ANTHROPIC_VERSION = "2023-06-01"

PROVIDERS: tuple[dict[str, Any], ...] = (
    {
        "id": "ollama",
        "label": "Ollama",
        "kind": "local",
        "base_url": "http://127.0.0.1:11434",
        # Native API: /v1 ignores options (e.g. num_ctx), and long-ctx models
        # default to 262k KV which offloads to CPU. Native honors num_ctx.
        "chat_path": "/api/chat",
        "models_path": "/api/tags",
        "tag_style": "ollama",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "lmstudio",
        "label": "LM Studio",
        "kind": "local",
        "base_url": "http://127.0.0.1:1234",
        "chat_path": "/v1/chat/completions",
        "models_path": "/v1/models",
        "tag_style": "openai",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "vllm",
        "label": "vLLM",
        "kind": "local",
        "base_url": "http://127.0.0.1:8000",
        "chat_path": "/v1/chat/completions",
        "models_path": "/v1/models",
        "tag_style": "openai",
        "key_env": None,
        "curated": [],
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "kind": "cloud",
        "base_url": "https://api.openai.com/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "OPENAI_API_KEY",
        "curated": ["gpt-4o", "gpt-4o-mini"],
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "kind": "cloud",
        "base_url": "https://api.anthropic.com",
        "chat_path": "/v1/messages",
        "models_path": "/v1/models",
        "tag_style": "anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "curated": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-fable-5.1"],
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "kind": "cloud",
        # No /v1 prefix on this host: chat is POST /chat/completions.
        "base_url": "https://api.deepseek.com",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "DEEPSEEK_API_KEY",
        # Flash first: newest and stronger than pro despite the name.
        "curated": ["deepseek-v4-flash", "deepseek-v4-pro", "deepseek-v4-flash-vision-exp"],
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "kind": "cloud",
        "base_url": "https://openrouter.ai/api/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "OPENROUTER_API_KEY",
        "curated": [
            "openrouter/auto",
            "anthropic/claude-sonnet-4",
            "openai/gpt-4o",
            "meta-llama/llama-4-maverick",
        ],
    },
    {
        "id": "meta",
        "label": "Meta",
        "kind": "cloud",
        "base_url": "https://api.meta.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "MODEL_API_KEY",
        # Contributor first: $0.20/M out, training-on-prompts acceptable per owner.
        "curated": [
            "muse-spark-1.3-contributor",
            "muse-spark-1.3",
            "muse-spark-1.2-contributor",
            "muse-spark-1.2",
            "muse-spark-1.1",
        ],
    },
    {
        "id": "google",
        "label": "Google",
        "kind": "cloud",
        # OpenAI-compatible endpoint: Bearer auth + /chat/completions + /models
        # just work (native Gemini API uses x-goog-api-key and other paths).
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "GEMINI_API_KEY",
        "key_env_fallbacks": ["GOOGLE_API_KEY"],
        # Curated names only surface with key_missing flag (BUG-042);
        # verify against the AI Studio model list when keyed.
        "curated": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    },
    {
        "id": "groq",
        "label": "Groq",
        "kind": "cloud",
        "base_url": "https://api.groq.com/openai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "GROQ_API_KEY",
        "curated": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
    },
    {
        "id": "mistral",
        "label": "Mistral",
        "kind": "cloud",
        "base_url": "https://api.mistral.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "MISTRAL_API_KEY",
        # -latest aliases resolve server-side, so this row barely ages.
        "curated": ["mistral-large-latest", "mistral-small-latest"],
    },
    {
        "id": "together",
        "label": "Together",
        "kind": "cloud",
        "base_url": "https://api.together.xyz/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "TOGETHER_API_KEY",
        "curated": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
    },
    {
        "id": "fireworks",
        "label": "Fireworks",
        "kind": "cloud",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "FIREWORKS_API_KEY",
        "curated": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/mixtral-8x7b-instruct",
        ],
    },
    {
        "id": "cohere",
        "label": "Cohere",
        "kind": "cloud",
        # OpenAI-compatibility endpoint (the fleet gateway uses native v2 with
        # a custom adapter; the pilot proxy stays uniform on openai shape).
        "base_url": "https://api.cohere.com/compatibility/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "COHERE_API_KEY",
        "key_env_fallbacks": ["CO_API_KEY"],
        "curated": ["command-r-plus", "command-r"],
    },
    {
        "id": "xai",
        "label": "xAI",
        "kind": "cloud",
        "base_url": "https://api.x.ai/v1",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "XAI_API_KEY",
        "curated": ["grok-3", "grok-3-mini", "grok-2-1212"],
    },
    {
        "id": "perplexity",
        "label": "Perplexity",
        "kind": "cloud",
        # No public /models endpoint as of 2026-09-29: the live list degrades
        # to curated (with error note) while chat works normally.
        "base_url": "https://api.perplexity.ai",
        "chat_path": "/chat/completions",
        "models_path": "/models",
        "tag_style": "openai",
        "key_env": "PERPLEXITY_API_KEY",
        "curated": ["sonar-pro", "sonar"],
    },
)


def get_provider(provider_id: str) -> dict[str, Any] | None:
    """Return the registry row for a provider ID, or None."""
    for row in PROVIDERS:
        if row["id"] == provider_id:
            return row
    return None


def require_provider(provider_id: str) -> dict[str, Any]:
    row = get_provider(provider_id)
    if row is None:
        known = ", ".join(r["id"] for r in PROVIDERS)
        raise ValueError(f"Unknown provider '{provider_id}'. Known: {known}")
    return row


def _settings():
    # No settings object in this repo; kept for pilot-compatible signatures.
    return None


def keystore_path(settings=None) -> Path:
    if settings is not None and hasattr(settings, "resolved_data_dir"):
        return settings.resolved_data_dir() / KEYSTORE_NAME
    override = os.getenv("SYSTEMADMIN_LLM_KEYSTORE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent.parent / "data" / KEYSTORE_NAME


def _read_keystore(settings=None) -> dict[str, str]:
    path = keystore_path(settings)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("llm keystore unreadable (%s); treating as empty", exc)
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str) and v}


def _write_keystore(entries: dict[str, str], settings=None) -> None:
    path = keystore_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        logger.debug("chmod 0600 on keystore failed (non-POSIX fs); continuing")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def get_key(provider_id: str, settings=None) -> str:
    """Resolve an API key: env var(s) first, then keystore. Empty when unset.

    key_env is the primary display name; key_env_fallbacks (optional list)
    are extra env names accepted for the same key (first hit wins).
    """
    row = require_provider(provider_id)
    env_names = [row.get("key_env"), *(row.get("key_env_fallbacks") or [])]
    for env_name in env_names:
        if not env_name:
            continue
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return _read_keystore(settings).get(provider_id, "")


def is_configured(provider_id: str, settings=None) -> bool:
    """True when a cloud provider has a key available. Locals need no key."""
    row = require_provider(provider_id)
    if row["kind"] == "local":
        return True
    return bool(get_key(provider_id, settings))


def keys_configured(settings=None) -> dict[str, bool]:
    return {r["id"]: is_configured(r["id"], settings) for r in PROVIDERS if r["kind"] == "cloud"}


def save_key(provider_id: str, api_key: str, settings=None) -> None:
    row = require_provider(provider_id)
    if row["kind"] != "cloud":
        raise ValueError(f"Provider '{provider_id}' takes no API key")
    key = (api_key or "").strip()
    if not key:
        raise ValueError("Empty API key")
    entries = _read_keystore(settings)
    entries[provider_id] = key
    _write_keystore(entries, settings)


def delete_key(provider_id: str, settings=None) -> bool:
    require_provider(provider_id)
    entries = _read_keystore(settings)
    if provider_id not in entries:
        return False
    del entries[provider_id]
    _write_keystore(entries, settings)
    return True


def public_provider_info(settings=None) -> list[dict[str, Any]]:
    """Registry rows safe for GET responses: capability flags, never key bytes."""
    return [
        {
            "id": r["id"],
            "label": r["label"],
            "kind": r["kind"],
            "base_url": r["base_url"],
            "needs_key": r["kind"] == "cloud",
            "key_env": r.get("key_env"),
            "configured": is_configured(r["id"], settings),
        }
        for r in PROVIDERS
    ]


def _parse_model_list(tag_style: str, payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    if tag_style == "ollama":
        models = payload.get("models") or []
        return [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]
    data = payload.get("data") or []
    return [m.get("id", "") for m in data if isinstance(m, dict) and m.get("id")]


async def probe_local(provider_id: str) -> tuple[bool, list[str]]:
    """Probe a local engine (fast timeout). Returns (reachable, models)."""
    row = require_provider(provider_id)
    if row["kind"] != "local":
        raise ValueError(f"Provider '{provider_id}' is not local")
    url = row["base_url"] + row["models_path"]
    try:
        async with httpx.AsyncClient(timeout=LOCAL_PROBE_TIMEOUT) as client:
            resp = await client.get(url)
    except Exception as exc:
        logger.debug("local probe %s failed: %s", provider_id, exc)
        return False, []
    if resp.status_code >= 500:
        return False, []
    try:
        models = _parse_model_list(row["tag_style"], resp.json())
    except Exception:
        models = []
    return True, models


async def list_models(provider_id: str, settings=None, api_key: str = "") -> dict[str, Any]:
    """Model list with source flag. Cloud: live when keyed, else curated.

    api_key overrides the stored/env key for this call only (lets Test
    validate a typed-but-unsaved key). Never persisted here. Unkeyed
    clouds return curated names with key_missing=True -- callers must not
    report those as success (BUG-042).
    """
    row = require_provider(provider_id)
    if row["kind"] == "local":
        reachable, models = await probe_local(provider_id)
        return {"provider": provider_id, "models": models, "source": "live" if reachable else "none"}
    key = (api_key or "").strip() or get_key(provider_id, settings)
    if not key:
        return {
            "provider": provider_id,
            "models": list(row["curated"]),
            "source": "curated",
            "key_missing": True,
            "note": "Save a key for the live list. Curated names still work once keyed.",
        }
    url = row["base_url"] + row["models_path"]
    headers = _auth_headers(row, key)
    try:
        async with httpx.AsyncClient(timeout=CLOUD_TIMEOUT) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            models = _parse_model_list(row["tag_style"], resp.json())
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        logger.warning("live model list for %s HTTP %s; curated fallback", provider_id, status)
        if status in (401, 403):
            error = f"{row['label']} rejected the key (HTTP {status}) -- check the key, then Save and Test again."
        else:
            error = f"{row['label']} HTTP {status}."
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated", "error": error}
    except Exception as exc:
        logger.warning("live model list for %s failed (%s); curated fallback", provider_id, exc)
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    if not models:
        return {"provider": provider_id, "models": list(row["curated"]), "source": "curated"}
    return {"provider": provider_id, "models": models, "source": "live"}


def _auth_headers(row: dict[str, Any], api_key: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if row["id"] == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = ANTHROPIC_VERSION
    elif row["id"] == "openrouter":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = "http://localhost:10771/"
        headers["X-Title"] = "system-admin-mcp"
    elif row["kind"] == "cloud":
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _openai_body(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    return {"model": model, "messages": messages, "stream": False}


def _to_anthropic(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Map OpenAI messages array to the Anthropic Messages API body."""
    system_parts: list[str] = []
    converted: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            converted.append({"role": role, "content": str(content)})
        else:
            converted.append({"role": "user", "content": str(content)})
    body: dict[str, Any] = {"model": model, "max_tokens": 1024, "messages": converted}
    if system_parts:
        body["system"] = "\n\n".join(system_parts)
    return body


def _from_anthropic(payload: dict[str, Any]) -> str:
    blocks = payload.get("content") or []
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(texts)


# Context window for local Ollama chat: Ollama's vram-based default is 32k,
# but long-ctx models (e.g. 262k) would eat VRAM and offload to CPU.
OLLAMA_NUM_CTX = 32768


def _to_ollama_native(model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Map OpenAI messages array to the Ollama native /api/chat body."""
    converted = [{"role": m.get("role", "user"), "content": str(m.get("content", ""))} for m in messages]
    return {
        "model": model,
        "messages": converted,
        "stream": False,
        "options": {"num_ctx": OLLAMA_NUM_CTX},
    }


def _from_ollama_native(payload: dict[str, Any]) -> str:
    return str((payload.get("message") or {}).get("content", ""))


def _ollama_stream_text(payload: dict[str, Any]) -> str:
    """Extract delta text from one Ollama native SSE line ({}), "" when final."""
    if payload.get("done"):
        return ""
    return str((payload.get("message") or {}).get("content", ""))


async def chat_complete(
    provider_id: str,
    model: str,
    messages: list[dict[str, Any]],
    settings=None,
) -> str:
    """Non-streaming chat via the backend proxy. Returns assistant text."""
    row = require_provider(provider_id)
    if not model.strip():
        raise ValueError("Empty model name")
    key = get_key(provider_id, settings) if row["kind"] == "cloud" else ""
    if row["kind"] == "cloud" and not key:
        raise ValueError(f"Provider '{provider_id}' has no API key configured")
    headers = _auth_headers(row, key)
    if row["id"] == "anthropic":
        url = row["base_url"] + row["chat_path"]
        body = _to_anthropic(model, messages)
    elif row["id"] == "ollama":
        url = row["base_url"] + row["chat_path"]
        body = _to_ollama_native(model, messages)
    else:
        url = row["base_url"] + row["chat_path"]
        body = _openai_body(model, messages)
    try:
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        raise RuntimeError(f"Provider '{provider_id}' HTTP {status}") from exc
    except Exception as exc:
        raise RuntimeError(f"Provider '{provider_id}' unreachable ({exc})") from exc
    if row["id"] == "anthropic":
        return _from_anthropic(data)
    if row["id"] == "ollama":
        return _from_ollama_native(data)
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Provider '{provider_id}' returned an unexpected body") from exc


def _openai_sse_chunk(model: str, text: str) -> bytes:
    import time
    import uuid

    chunk = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
    }
    return ("data: " + json.dumps(chunk) + "\n\n").encode("utf-8")


async def chat_stream(
    provider_id: str,
    model: str,
    messages: list[dict[str, Any]],
    settings=None,
) -> AsyncIterator[bytes]:
    """Streaming chat as OpenAI-style SSE bytes, normalized for every provider."""
    row = require_provider(provider_id)
    if not model.strip():
        raise ValueError("Empty model name")
    key = get_key(provider_id, settings) if row["kind"] == "cloud" else ""
    if row["kind"] == "cloud" and not key:
        raise ValueError(f"Provider '{provider_id}' has no API key configured")
    headers = _auth_headers(row, key)
    headers["Accept"] = "text/event-stream"
    if row["id"] == "anthropic":
        url = row["base_url"] + row["chat_path"]
        body = _to_anthropic(model, messages)
        body["stream"] = True
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload in ("[DONE]", ""):
                        continue
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        text = (event.get("delta") or {}).get("text", "")
                        if text:
                            yield _openai_sse_chunk(model, text)
    elif row["id"] == "ollama":
        url = row["base_url"] + row["chat_path"]
        body = _to_ollama_native(model, messages)
        body["stream"] = True
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        event = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    delta = _ollama_stream_text(event)
                    if delta:
                        yield _openai_sse_chunk(model, delta)
    else:
        url = row["base_url"] + row["chat_path"]
        body = _openai_body(model, messages)
        body["stream"] = True
        async with httpx.AsyncClient(timeout=CHAT_TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield (line + "\n\n").encode("utf-8")
    yield b"data: [DONE]\n\n"


def _parse_nvidia_smi(stdout: str) -> list[dict[str, Any]]:
    """Parse `nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free
    --format=csv,noheader,nounits` output. Never raises: garbage lines are skipped."""
    gpus: list[dict[str, Any]] = []
    for line in (stdout or "").splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        try:
            gpus.append(
                {
                    "index": int(parts[0]),
                    "name": ",".join(parts[1:-3]).strip(),
                    "total_mb": int(parts[-3]),
                    "used_mb": int(parts[-2]),
                    "free_mb": int(parts[-1]),
                }
            )
        except ValueError:
            continue
    return gpus


def gpu_vram() -> list[dict[str, Any]]:
    """Live per-GPU VRAM via nvidia-smi. Empty list when unavailable (no GPU,
    no driver, timeout). Shared by the REST endpoint and the llm_ops MCP tool."""
    import subprocess

    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        logger.debug("nvidia-smi unavailable (%s)", exc)
        return []
    if proc.returncode != 0:
        return []
    return _parse_nvidia_smi(proc.stdout)


def _same_model(a: str, b: str) -> bool:
    """Loose tag equality: an untagged name matches any tag of the same repo."""
    if a == b:
        return True
    a_repo, _, a_tag = a.partition(":")
    b_repo, _, b_tag = b.partition(":")
    if a_repo != b_repo:
        return False
    return not a_tag or not b_tag or a_tag == b_tag


async def ollama_loaded(base_url: str) -> dict[str, Any]:
    """Residents on the Ollama engine (`/api/ps`): name + VRAM + expiry.

    Feeds the Settings loaded-model KPI and the llm_ops `loaded` op.
    Never raises: engine down means engine=False with an empty list.
    """
    result: dict[str, Any] = {"engine": False, "models": []}
    base = (base_url or "").rstrip("/") or "http://127.0.0.1:11434"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            ps = await client.get(base + "/api/ps")
            if ps.status_code != 200:
                return result
            result["engine"] = True
            try:
                items = ps.json().get("models") or []
            except Exception:
                items = []
            for m in items:
                if not isinstance(m, dict) or not m.get("name"):
                    continue
                result["models"].append(
                    {
                        "name": m["name"],
                        "size_vram_mb": round((m.get("size_vram") or 0) / 1048576),
                        "expires_at": m.get("expires_at") or "",
                    }
                )
    except Exception as exc:
        logger.debug("ollama loaded probe failed (%s)", exc)
    return result


async def switch_ollama_model(keep: str, base_url: str) -> dict[str, Any]:
    """Make `keep` the only loaded Ollama model: evict the rest, warm `keep`.

    Empty `keep` evicts everything and warms nothing (full VRAM release).
    Pure HTTP against the engine (no ollama CLI needed). Selecting a model in
    Settings must switch VRAM, not just write config — otherwise a 20 GB hog
    keeps squatting while the new choice can't fit. All failures are
    non-fatal; the caller reports what happened.
    """
    result: dict[str, Any] = {"evicted": [], "warmed": False, "engine": False}
    keep = (keep or "").strip()
    base = (base_url or "").rstrip("/") or "http://127.0.0.1:11434"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            ps = await client.get(base + "/api/ps")
            if ps.status_code != 200:
                return result
            result["engine"] = True
            try:
                loaded = [
                    m.get("name", "") for m in (ps.json().get("models") or []) if isinstance(m, dict) and m.get("name")
                ]
            except Exception:
                loaded = []
            if keep and any(_same_model(keep, name) for name in loaded):
                result["warmed"] = True
            for name in loaded:
                if keep and _same_model(keep, name):
                    continue
                try:
                    await client.post(base + "/api/generate", json={"model": name, "keep_alive": 0})
                    result["evicted"].append(name)
                except Exception as exc:
                    logger.warning("ollama evict %s failed (%s)", name, exc)
            if keep and not result["warmed"]:
                try:
                    async with httpx.AsyncClient(timeout=180.0) as warm_client:
                        warm = await warm_client.post(
                            base + "/api/generate",
                            json={
                                "model": keep,
                                "prompt": " ",
                                "keep_alive": "10m",
                                "options": {"num_predict": 1},
                            },
                        )
                        result["warmed"] = warm.status_code == 200
                except Exception as exc:
                    logger.warning("ollama warm %s failed (%s)", keep, exc)
    except Exception as exc:
        logger.warning("ollama switch failed (%s)", exc)
    return result


INSTALL_ALLOWLIST = ("ollama",)
INSTALL_TIMEOUT = 600.0

_install_jobs: dict[str, dict[str, Any]] = {}
_install_lock = threading.Lock()


def _set_install_state(engine: str, **fields: Any) -> None:
    with _install_lock:
        job = _install_jobs.setdefault(engine, {"engine": engine, "state": "idle"})
        job.update(fields)


def _run_winget_ollama() -> None:
    import subprocess

    _set_install_state("ollama", state="running", output="")
    try:
        proc = subprocess.run(
            [
                "winget",
                "install",
                "-e",
                "--id",
                "Ollama.Ollama",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ],
            capture_output=True,
            text=True,
            timeout=INSTALL_TIMEOUT,
        )
        tail = (proc.stdout + proc.stderr)[-2000:]
        if proc.returncode == 0:
            _set_install_state("ollama", state="done", output=tail)
        else:
            _set_install_state("ollama", state="error", output=tail or f"exit {proc.returncode}")
    except FileNotFoundError:
        _set_install_state("ollama", state="error", output="winget not found on PATH")
    except Exception as exc:
        _set_install_state("ollama", state="error", output=str(exc)[:500])


def start_install(engine: str) -> dict[str, Any]:
    """Start a fixed-command engine install in the background (allowlisted only)."""
    if engine not in INSTALL_ALLOWLIST:
        allowed = ", ".join(INSTALL_ALLOWLIST)
        raise ValueError(f"Install not supported for '{engine}'. Allowed: {allowed}")
    if sys.platform != "win32":
        raise RuntimeError("One-click install is Windows-only")
    with _install_lock:
        if _install_jobs.get(engine, {}).get("state") == "running":
            return {"engine": engine, "started": False, "reason": "already running"}
    thread = threading.Thread(target=_run_winget_ollama, name="ollama-install", daemon=True)
    thread.start()
    return {"engine": engine, "started": True}


def install_status(engine: str) -> dict[str, Any]:
    if engine not in INSTALL_ALLOWLIST:
        raise ValueError(f"Unknown install engine '{engine}'")
    with _install_lock:
        job = dict(_install_jobs.get(engine, {"engine": engine, "state": "idle"}))
    return job


def onboarding_state(settings=None) -> dict[str, Any]:
    """Fresh-install starter facts: what exists, what can be installed, best path."""
    clouds = {r["id"]: is_configured(r["id"], settings) for r in PROVIDERS if r["kind"] == "cloud"}
    return {
        "locals": [
            {"id": r["id"], "label": r["label"], "port": _port_hint(r["base_url"])}
            for r in PROVIDERS
            if r["kind"] == "local"
        ],
        "clouds_configured": [pid for pid, ok in clouds.items() if ok],
        "recommendation": _recommend_path(clouds),
    }


def _port_hint(base_url: str) -> int | None:
    try:
        return int(base_url.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return None


def _recommend_path(clouds: dict[str, bool]) -> dict[str, str]:
    if any(clouds.values()):
        first = next(pid for pid, ok in clouds.items() if ok)
        return {
            "path": f"cloud:{first}",
            "reason": f"{first} key already configured — chat works immediately.",
        }
    return {
        "path": "cloud:meta",
        "reason": "Cheapest instant path: paste a Meta key (Contributor $0.20/M out). "
        "Free path: install Ollama (section 3 of the llm-guide skill) and come back.",
    }


async def ollama_state(base_url: str = "http://127.0.0.1:11434") -> dict[str, Any]:
    """Resident-first inputs: installed (/api/tags) + loaded (/api/ps) models.

    Never raises: engine down means engine=False with empty lists.
    """
    base = (base_url or "").rstrip("/") or "http://127.0.0.1:11434"
    state: dict[str, Any] = {"engine": False, "loaded": [], "installed": []}
    try:
        async with httpx.AsyncClient(timeout=LOCAL_PROBE_TIMEOUT) as client:
            tags = await client.get(base + "/api/tags")
            if tags.status_code == 200:
                try:
                    state["installed"] = _parse_model_list("ollama", tags.json())
                except Exception:
                    state["installed"] = []
            ps = await ollama_loaded(base)
            state["engine"] = bool(ps.get("engine"))
            state["loaded"] = [m.get("name", "") for m in ps.get("models", []) if m.get("name")]
    except Exception as exc:
        logger.debug("ollama state probe failed: %s", exc)
    return state


def register_llm_routes(app) -> None:
    """Mount the fleet LLM contracts (INTEGRATION.md) on the FastAPI app."""

    @app.get("/api/llm/providers")
    async def api_llm_providers() -> dict[str, Any]:
        infos = public_provider_info()
        for info in infos:
            row = get_provider(info["id"]) or {}
            if row.get("kind") == "local":
                try:
                    reachable, models = await probe_local(info["id"])
                except ValueError:
                    reachable, models = False, []
                info["detected"] = reachable
                info["models"] = models
            else:
                info["detected"] = False
        return {"providers": infos}

    @app.get("/api/llm/models")
    async def api_llm_models(provider: str) -> dict[str, Any]:
        try:
            return await list_models(provider)
        except ValueError as exc:
            return {"provider": provider, "models": [], "source": "error", "note": str(exc)}

    @app.post("/api/llm/test")
    async def api_llm_test(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except Exception:
            return {"ok": False, "models": [], "source": "error", "note": "Invalid JSON body"}
        provider = (body.get("provider") or "").strip()
        api_key = (body.get("api_key") or "").strip()
        endpoint = (body.get("endpoint") or "").strip()
        if not provider:
            return {"ok": False, "models": [], "source": "error", "note": "provider required"}
        try:
            row = require_provider(provider)
        except ValueError as exc:
            return {"ok": False, "models": [], "source": "error", "note": str(exc)}
        if endpoint and row["kind"] == "local":
            base = endpoint.rstrip("/")
            path = row["models_path"]
            try:
                async with httpx.AsyncClient(timeout=LOCAL_PROBE_TIMEOUT) as client:
                    resp = await client.get(base + path)
                    models = _parse_model_list(row["tag_style"], resp.json() if resp.status_code < 500 else {})
                    ok = resp.status_code < 500
            except Exception as exc:
                return {"ok": False, "models": [], "source": "none", "note": f"endpoint unreachable: {exc}"}
            return {"ok": ok, "models": models, "source": "live" if ok else "none"}
        try:
            result = await list_models(provider, api_key=api_key)
        except ValueError as exc:
            return {"ok": False, "models": [], "source": "error", "note": str(exc)}
        ok = result.get("source") == "live"
        return {
            "ok": ok,
            "models": result.get("models", []),
            "source": result.get("source", "none"),
            "note": result.get("note", ""),
        }

    @app.get("/api/settings/llm")
    async def api_settings_llm_get() -> dict[str, Any]:
        return {"providers": public_provider_info(), "keys_configured": keys_configured()}

    @app.post("/api/settings/llm")
    async def api_settings_llm_post(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except Exception:
            return {"ok": False, "note": "Invalid JSON body"}
        provider = (body.get("provider") or "").strip()
        api_key = body.get("api_key")
        if not provider:
            return {"ok": False, "note": "provider required"}
        try:
            row = require_provider(provider)
        except ValueError as exc:
            return {"ok": False, "note": str(exc)}
        if api_key is not None and str(api_key).strip():
            if row["kind"] != "cloud":
                return {"ok": False, "note": f"Provider '{provider}' takes no API key"}
            try:
                save_key(provider, str(api_key))
            except ValueError as exc:
                return {"ok": False, "note": str(exc)}
        # select:false leaves the active pair alone (BUG-043); selection itself
        # lives in frontend localStorage, never on the server.
        return {"ok": True, "keys_configured": keys_configured()}

    @app.delete("/api/settings/llm/key")
    async def api_settings_llm_delete(provider: str = "") -> dict[str, Any]:
        provider = (provider or "").strip()
        if not provider:
            return {"ok": False, "note": "provider query param required"}
        try:
            deleted = delete_key(provider)
        except ValueError as exc:
            return {"ok": False, "note": str(exc)}
        return {"ok": True, "deleted": deleted, "keys_configured": keys_configured()}

    @app.post("/api/llm/chat")
    async def api_llm_chat(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except Exception:
            return {"status": "error", "message": "Invalid JSON body"}
        provider = (body.get("provider") or "").strip()
        model = (body.get("model") or "").strip()
        messages = body.get("messages") or []
        if not provider or not model or not messages:
            return {"status": "error", "message": "provider, model, and messages are required"}
        try:
            text = await chat_complete(provider, model, messages)
        except (ValueError, RuntimeError) as exc:
            return {"status": "error", "message": str(exc)}
        except Exception as exc:
            logger.exception("llm chat failed")
            return {"status": "error", "message": f"provider error: {exc}"}
        return {"status": "success", "content": text}

    @app.post("/api/llm/chat/stream")
    async def api_llm_chat_stream(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        provider = ((body or {}).get("provider") or "").strip()
        model = ((body or {}).get("model") or "").strip()
        messages = (body or {}).get("messages") or []

        async def _gen():
            try:
                async for chunk in chat_stream(provider, model, messages):
                    yield chunk
            except Exception as exc:
                yield b"data: " + json.dumps({"error": str(exc)}).encode("utf-8") + b"\n\n"

        if not provider or not model or not messages:

            async def _err():
                yield (
                    b"data: "
                    + json.dumps({"error": "provider, model, and messages are required"}).encode("utf-8")
                    + b"\n\n"
                )

            return StreamingResponse(_err(), media_type="text/event-stream")
        return StreamingResponse(_gen(), media_type="text/event-stream")

    @app.get("/api/llm/onboarding")
    async def api_llm_onboarding() -> dict[str, Any]:
        return onboarding_state()

    @app.post("/api/llm/install")
    async def api_llm_install(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except Exception:
            body = {}
        engine = ((body or {}).get("engine") or "").strip()
        try:
            return start_install(engine)
        except (ValueError, RuntimeError) as exc:
            return {"engine": engine, "started": False, "reason": str(exc)}

    @app.get("/api/llm/install/status")
    async def api_llm_install_status(engine: str = "ollama") -> dict[str, Any]:
        try:
            return install_status(engine)
        except ValueError as exc:
            return {"engine": engine, "state": "error", "output": str(exc)}

    @app.get("/api/llm/gpus")
    async def api_llm_gpus() -> dict[str, Any]:
        gpus = [{"index": g["index"], "name": g["name"], "vramMb": g["total_mb"]} for g in gpu_vram()]
        return {"gpus": gpus}

    @app.get("/api/llm/ollama/state")
    async def api_llm_ollama_state() -> dict[str, Any]:
        return await ollama_state()
