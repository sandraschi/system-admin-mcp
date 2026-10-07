/**
 * Global LLM state (fleet WEBAPP_SOTA_STANDARDS.md §III + §VI).
 * Provider/model selection lives here — not in per-page useState —
 * so Chat and Settings share one source of truth.
 * Persistence keys: localStorage llm_provider / llm_model (never keys).
 */
import { create } from "zustand";
import { fetchGpuMessage, fetchProviders } from "@/lib/provider";

export const FALLBACK_MODEL = "llama3.2:3b";

interface LlmState {
  providers: Record<string, string[]>;
  detected: Record<string, boolean>;
  selectedProvider: string;
  selectedModel: string;
  status: "probing" | "ready" | "error";
  loadError: string | null;
  gpuMessage: string | null;
  gpuStatus: "probing" | "ready";
  load: () => Promise<void>;
  selectProvider: (provider: string) => void;
  selectModel: (model: string) => void;
}

function modelsFor(
  providers: Record<string, string[]>,
  provider: string,
): string[] {
  const key = provider === "ollama" ? "ollama" : "lm_studio";
  return providers[key] || [];
}

export const useLlmStore = create<LlmState>()((set, get) => ({
  providers: {},
  detected: {},
  selectedProvider: localStorage.getItem("llm_provider") || "ollama",
  selectedModel: localStorage.getItem("llm_model") || "",
  status: "probing",
  loadError: null,
  gpuMessage: null,
  gpuStatus: "probing",

  load: async () => {
    if (get().status === "ready") return;
    try {
      const infos = await fetchProviders();
      const providers: Record<string, string[]> = {};
      const detected: Record<string, boolean> = {};
      for (const p of infos) {
        providers[p.name] = p.models;
        detected[p.name] = p.detected;
      }
      const savedP = localStorage.getItem("llm_provider") || "ollama";
      const savedM = localStorage.getItem("llm_model") || "";
      const models = modelsFor(providers, savedP);
      set({
        providers,
        detected,
        selectedProvider: savedP,
        selectedModel:
          savedM && models.includes(savedM)
            ? savedM
            : models[0] || FALLBACK_MODEL,
        status: "ready",
        loadError: null,
      });
    } catch (err) {
      set({
        providers: { ollama: [FALLBACK_MODEL] },
        selectedModel: localStorage.getItem("llm_model") || FALLBACK_MODEL,
        status: "error",
        loadError: String(err),
      });
    }
    void fetchGpuMessage().then((msg) => {
      if (msg) set({ gpuMessage: msg, gpuStatus: "ready" });
      else set({ gpuStatus: "ready" });
    });
  },

  selectProvider: (provider: string) => {
    localStorage.setItem("llm_provider", provider);
    localStorage.setItem("llm_model", "");
    set({ selectedProvider: provider, selectedModel: "" });
  },

  selectModel: (model: string) => {
    localStorage.setItem("llm_model", model);
    set({ selectedModel: model });
  },
}));

/** Models for the currently selected provider (settings/chat dropdowns). */
export function useProviderModels(): string[] {
  const providers = useLlmStore((s) => s.providers);
  const selectedProvider = useLlmStore((s) => s.selectedProvider);
  return modelsFor(providers, selectedProvider);
}
