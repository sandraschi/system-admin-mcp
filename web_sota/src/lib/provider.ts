/**
 * LLM provider probing (fleet WEBAPP_SOTA_STANDARDS.md §VI).
 * Backend proxy only — the browser never talks to providers directly.
 * Local engine URLs are 127.0.0.1 (never localhost: LM Studio 404s IPv6).
 */
import API_BASE from "@/lib/api";

export interface LlmProviderInfo {
  name: string;
  base: string;
  detected: boolean;
  models: string[];
}

export async function fetchProviders(): Promise<LlmProviderInfo[]> {
  const r = await fetch(`${API_BASE}/api/llm/discover`);
  if (!r.ok) throw new Error(`/api/llm/discover: HTTP ${r.status}`);
  const d = await r.json();
  return (d.providers || []).map(
    (p: {
      name: string;
      base?: string;
      detected?: boolean;
      models?: string[];
    }) => ({
      name: p.name,
      base: p.base || "",
      detected: !!p.detected,
      models: p.models || [],
    }),
  );
}

/** Best-effort GPU summary via the get_gpu_info tool (null when unavailable). */
export async function fetchGpuMessage(): Promise<string | null> {
  try {
    const r = await fetch(`${API_BASE}/api/tools/call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "get_gpu_info", arguments: {} }),
    });
    const d = await r.json();
    const msg: string | undefined = d?.result?.message || d?.message;
    return d?.status === "success" && msg ? msg : null;
  } catch {
    return null;
  }
}
