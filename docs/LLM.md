# LLM Providers — system-admin-mcp

Fleet contracts (WEBAPP_SOTA_STANDARDS.md §VI.10, INTEGRATION.md). The browser
never holds keys and never talks to providers — everything goes through the
FastAPI backend (`src/system_admin_mcp/llm_providers.py`, vendored from the
arxiv-mcp pilot with a local keystore shim).

## Providers (16)

Local (free): `ollama` (:11434, native `/api/chat`), `lmstudio` (:1234),
`vllm` (:8000). Cloud (paid, keyed): `openai`, `anthropic`, `deepseek`,
`openrouter`, `meta` (Contributor pilot default), `google` (OpenAI-compat),
`groq`, `mistral`, `together`, `fireworks`, `cohere`, `xai`, `perplexity`.

## Key rules (HIGH gate)

- Keys live in `data/llm_keys.json` (0600, gitignored) or env (`OPENAI_API_KEY`,
  … — env wins). `SYSTEMADMIN_LLM_KEYSTORE` overrides the path (tests).
- Never in localStorage, GET responses, logs, URLs, or the bundle. Verified by
  `test_no_key_bytes_leaked`.
- `POST /api/settings/llm` accepts write-only `api_key` (+ `select: false`
  leaves the active pair alone, BUG-043); empty key = no-op (never wipes).
  `DELETE /api/settings/llm/key?provider=` clears.

## Endpoints

| Method + path | Purpose |
|---|---|
| `GET /api/llm/providers` | Registry + live local detection + `configured` flags (no key bytes) |
| `GET /api/llm/models?provider=` | Live list when reachable/keyed; curated + `key_missing` otherwise (BUG-042: never report curated as success) |
| `POST /api/llm/test` | Validate `{provider, api_key?, endpoint?}` without saving |
| `GET/POST /api/settings/llm`, `DELETE …/key` | Key management (see above) |
| `POST /api/llm/chat` | `{provider, model, messages}` → `{content}` (Ollama via native `/api/chat` with `num_ctx` cap; others OpenAI-style) |
| `POST /api/llm/chat/stream` | OpenAI-style SSE; Chat uses `streamChat()` from `lib/llm.ts` |
| `GET /api/llm/onboarding` | Starter facts + cheapest-first recommendation |
| `POST /api/llm/install`, `GET …/status` | One-click Ollama via winget (allowlisted, background job) |
| `GET /api/llm/gpus` | `[{index, name, vramMb}]` from nvidia-smi (dual-GPU placement) |
| `GET /api/llm/ollama/state` | `{engine, loaded, installed}` (resident-first inputs) |

Legacy `/api/chat` (`{query, provider, model}`) is retained for existing
clients. `/api/v1/diagnostics` is test-only (CUA-NSIS smoke); the dashboard
fetches `/api/status` + `/api/processes` directly.

## Dual-GPU placement (§VI.8) + resident-first (§VI.9)

- Target GPU defaults to the secondary card (primary 4090 holds resident
  Glimmer); persisted as `llm_gpu`; Settings shows `llm-gpu-select` only when
  2+ cards exist. Model dropdowns hide tiers exceeding target VRAM
  (`fitsTarget` in `lib/llm.ts`, table mirrors `detect.py` TIERS).
- Default model resolves resident-first: loaded preferred model → installed
  preferred → saved choice (when still installed and fitting). Never evicts
  a resident model (the Headers-Timeout failure mode).
- Single-GPU/non-NVIDIA degrades to old behavior (no select, no filtering).

## Frontend map

- `lib/llm.ts` — proxy calls, `streamChat`, preference helpers (vendored logic).
- `lib/provider.ts` — legacy discover helper (local pair only).
- `store/llm.ts` — single source: providers, clouds, keys, GPUs, target, loaded.
- Settings: active-pair row, provider cards (`llm-provider-card-{id}`,
  `llm-key-{id}`, `llm-test-{id}`), GPU select.
- Dashboard hero: `onboarding-cue` red CTA when nothing is usable.
