/**
 * Fleet LLM client (WEBAPP_SOTA_STANDARDS.md §VI.10 + INTEGRATION.md).
 * Backend proxy only — the browser never holds keys or talks to providers.
 * Local engine URLs are 127.0.0.1 (never localhost: LM Studio 404s IPv6).
 */
import API_BASE from "@/lib/api";

export interface ProviderCard {
  id: string;
  label: string;
  kind: "local" | "cloud";
  base_url: string;
  needs_key: boolean;
  key_env: string | null;
  configured: boolean;
  detected?: boolean;
  models?: string[];
}

export interface GpuInfo {
  index: number;
  name: string;
  vramMb: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export async function fetchProviderCards(): Promise<ProviderCard[]> {
  const r = await fetch(`${API_BASE}/api/llm/providers`);
  if (!r.ok) throw new Error(`/api/llm/providers: HTTP ${r.status}`);
  const d = await r.json();
  return d.providers || [];
}

export async function fetchProviderModels(provider: string): Promise<{
  models: string[];
  source: string;
  key_missing?: boolean;
  note?: string;
}> {
  const r = await fetch(
    `${API_BASE}/api/llm/models?provider=${encodeURIComponent(provider)}`,
  );
  if (!r.ok) throw new Error(`/api/llm/models: HTTP ${r.status}`);
  return r.json();
}

export async function testProvider(
  provider: string,
  apiKey?: string,
): Promise<{ ok: boolean; models: string[]; source: string; note?: string }> {
  const r = await fetch(`${API_BASE}/api/llm/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, api_key: apiKey || "" }),
  });
  if (!r.ok) throw new Error(`/api/llm/test: HTTP ${r.status}`);
  return r.json();
}

export async function saveProviderKey(
  provider: string,
  apiKey: string,
): Promise<{
  ok: boolean;
  note?: string;
  keys_configured?: Record<string, boolean>;
}> {
  const r = await fetch(`${API_BASE}/api/settings/llm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, api_key: apiKey, select: false }),
  });
  if (!r.ok) throw new Error(`/api/settings/llm: HTTP ${r.status}`);
  return r.json();
}

export async function deleteProviderKey(
  provider: string,
): Promise<{ ok: boolean }> {
  const r = await fetch(
    `${API_BASE}/api/settings/llm/key?provider=${encodeURIComponent(provider)}`,
    { method: "DELETE" },
  );
  if (!r.ok) throw new Error(`DELETE key: HTTP ${r.status}`);
  return r.json();
}

export async function fetchKeysConfigured(): Promise<Record<string, boolean>> {
  const r = await fetch(`${API_BASE}/api/settings/llm`);
  if (!r.ok) throw new Error(`/api/settings/llm: HTTP ${r.status}`);
  const d = await r.json();
  return d.keys_configured || {};
}

/** Non-streaming chat via the backend proxy. */
export async function chatOnce(
  provider: string,
  model: string,
  messages: ChatMessage[],
): Promise<string> {
  const r = await fetch(`${API_BASE}/api/llm/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, model, messages }),
  });
  const d = await r.json();
  if (!r.ok || d.status !== "success") {
    throw new Error(d.message || `HTTP ${r.status}`);
  }
  return d.content;
}

/** Streaming chat: calls onToken per text delta (OpenAI-style SSE). */
export async function streamChat(
  provider: string,
  model: string,
  messages: ChatMessage[],
  onToken: (text: string) => void,
): Promise<void> {
  const r = await fetch(`${API_BASE}/api/llm/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, model, messages }),
  });
  if (!r.ok || !r.body) {
    // Fall back to non-streaming so chat never hard-fails on SSE issues.
    onToken(await chatOnce(provider, model, messages));
    return;
  }
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() || "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (!payload || payload === "[DONE]") continue;
      try {
        const obj = JSON.parse(payload);
        if (typeof obj.error === "string" && obj.error) {
          throw new Error(obj.error);
        }
        const text =
          obj.choices?.[0]?.delta?.content || obj.content || obj.text || "";
        if (text) onToken(text);
      } catch (e) {
        if (e instanceof Error && e.message !== payload) throw e;
      }
    }
  }
}

export async function fetchGpus(): Promise<GpuInfo[]> {
  try {
    const r = await fetch(`${API_BASE}/api/llm/gpus`);
    if (!r.ok) return [];
    const d = await r.json();
    return Array.isArray(d.gpus) ? d.gpus : [];
  } catch {
    return [];
  }
}

export async function fetchOllamaState(): Promise<{
  engine: boolean;
  loaded: string[];
  installed: string[];
}> {
  try {
    const r = await fetch(`${API_BASE}/api/llm/ollama/state`);
    if (!r.ok) return { engine: false, loaded: [], installed: [] };
    const d = await r.json();
    return {
      engine: !!d.engine,
      loaded: Array.isArray(d.loaded) ? d.loaded : [],
      installed: Array.isArray(d.installed) ? d.installed : [],
    };
  } catch {
    return { engine: false, loaded: [], installed: [] };
  }
}

// --- Resident-first + target-GPU model preference (vendored logic from
// templates/llm-detect/model-preference.ts; data comes from the backend) ---

export const FLEET_MODEL_PREFERENCE = [
  "qwen3.8:27b",
  "gemma4:12b",
  "qwen2.5-coder:32b-instruct-q4_K_M",
  "deepseek-r1:32b",
  "gemma4:26b",
  "qwen2.5-coder:14b",
  "llama3.1:8b",
  "qwen2.5-coder:7b",
  "mistral:7b",
  "llama3.2:3b",
] as const;

const MODEL_TIER_MIN_VRAM_MB: Record<string, number> = {
  "qwen3.8:27b": 20000,
  "gemma4:12b": 20000,
  "qwen2.5-coder:32b-instruct-q4_K_M": 32000,
  "deepseek-r1:32b": 32000,
  "gemma4:26b": 32000,
  "qwen2.5-coder:14b": 20000,
  "llama3.1:8b": 20000,
  "qwen2.5-coder:7b": 14000,
  "mistral:7b": 14000,
  "llama3.2:3b": 14000,
};

/** Target GPU: secondary card (index > 0) — primary holds resident Glimmer. */
export function pickTargetGpu(
  gpus: GpuInfo[],
  preferred?: number,
): GpuInfo | null {
  if (gpus.length === 0) return null;
  if (preferred !== undefined) {
    const hit = gpus.find((g) => g.index === preferred);
    if (hit) return hit;
  }
  return gpus.find((g) => g.index > 0) ?? gpus[0];
}

export function fitsTarget(model: string, target: GpuInfo | null): boolean {
  if (!target?.vramMb) return true;
  const minVram = MODEL_TIER_MIN_VRAM_MB[model];
  if (minVram === undefined) return true;
  return target.vramMb >= minVram;
}

/** One-click engine install (allowlisted only, background job on the backend). */
export async function startInstall(
  engine: string,
): Promise<{ engine: string; started: boolean; reason?: string }> {
  const r = await fetch(`${API_BASE}/api/llm/install`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ engine }),
  });
  if (!r.ok) throw new Error(`/api/llm/install: HTTP ${r.status}`);
  return r.json();
}

export async function pollInstallStatus(
  engine: string,
): Promise<{ engine: string; state: string; output?: string }> {
  const r = await fetch(
    `${API_BASE}/api/llm/install/status?engine=${encodeURIComponent(engine)}`,
  );
  if (!r.ok) throw new Error(`/api/llm/install/status: HTTP ${r.status}`);
  return r.json();
}

/** Resident-first default: loaded beats installed; unfit models skipped. */
export function pickPreferredModel(
  loaded: string[],
  installed: string[],
  targetGpu?: GpuInfo | null,
): string {
  const order = FLEET_MODEL_PREFERENCE.filter(
    (m) => installed.includes(m) && fitsTarget(m, targetGpu ?? null),
  );
  const resident = new Set(loaded);
  for (const m of order) {
    if (resident.has(m)) return m;
  }
  return order[0] ?? "";
}
