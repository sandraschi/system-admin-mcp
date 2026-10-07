/**
 * Global LLM state (fleet WEBAPP_SOTA_STANDARDS.md §III + §VI).
 * Provider/model selection lives here — not in per-page useState —
 * so Chat and Settings share one source of truth.
 * Persistence keys: localStorage llm_provider / llm_model / llm_gpu (never keys).
 */
import { create } from "zustand";
import type { GpuInfo } from "@/lib/llm";
import {
  fetchGpus,
  fetchOllamaState,
  fetchProviderCards,
  type ProviderCard,
  pickPreferredModel,
  pickTargetGpu,
} from "@/lib/llm";
import { fetchGpuMessage, fetchProviders } from "@/lib/provider";

export const FALLBACK_MODEL = "llama3.2:3b";
export const GPU_KEY = "llm_gpu";

interface LlmState {
  providers: Record<string, string[]>;
  detected: Record<string, boolean>;
  selectedProvider: string;
  selectedModel: string;
  status: "probing" | "ready" | "error";
  loadError: string | null;
  gpuMessage: string | null;
  gpuStatus: "probing" | "ready";
  // Cloud stack (§VI.10)
  cards: ProviderCard[];
  keysConfigured: Record<string, boolean>;
  cardsStatus: "probing" | "ready" | "error";
  // Dual-GPU placement (§VI.8) + resident-first (§VI.9)
  gpus: GpuInfo[];
  targetGpuIndex: number | null;
  ollamaLoaded: string[];
  ollamaInstalled: string[];
  load: () => Promise<void>;
  loadCards: () => Promise<void>;
  loadGpus: () => Promise<void>;
  selectProvider: (provider: string) => void;
  selectModel: (model: string) => void;
  setTargetGpu: (index: number) => void;
}

function modelsFor(
  providers: Record<string, string[]>,
  provider: string,
): string[] {
  const key = provider === "ollama" ? "ollama" : "lm_studio";
  return providers[key] || [];
}

function storedTargetGpus(gpus: GpuInfo[]): number | null {
  const raw = localStorage.getItem(GPU_KEY);
  if (raw !== null) {
    const idx = Number(raw);
    if (gpus.some((g) => g.index === idx)) return idx;
  }
  return pickTargetGpu(gpus)?.index ?? null;
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
  cards: [],
  keysConfigured: {},
  cardsStatus: "probing",
  gpus: [],
  targetGpuIndex: null,
  ollamaLoaded: [],
  ollamaInstalled: [],

  load: async () => {
    if (get().status === "ready") return;
    try {
      const [infos, gpus, ollama] = await Promise.all([
        fetchProviders(),
        fetchGpus(),
        fetchOllamaState(),
      ]);
      const providers: Record<string, string[]> = {};
      const detected: Record<string, boolean> = {};
      for (const p of infos) {
        providers[p.name] = p.models;
        detected[p.name] = p.detected;
      }
      const savedP = localStorage.getItem("llm_provider") || "ollama";
      const savedM = localStorage.getItem("llm_model") || "";
      const target = pickTargetGpu(gpus, storedTargetGpus(gpus) ?? undefined);
      const models = modelsFor(providers, savedP);
      let model = savedM && models.includes(savedM) ? savedM : "";
      if (!model && (savedP === "ollama" || !savedP)) {
        // Resident-first (§VI.9): a loaded preferred model wins, never evicted.
        model =
          pickPreferredModel(ollama.loaded, ollama.installed, target) ||
          models[0] ||
          FALLBACK_MODEL;
        if (model) localStorage.setItem("llm_model", model);
      }
      if (!model) model = models[0] || FALLBACK_MODEL;
      set({
        providers,
        detected,
        selectedProvider: savedP,
        selectedModel: model,
        status: "ready",
        loadError: null,
        gpus,
        targetGpuIndex: target?.index ?? null,
        ollamaLoaded: ollama.loaded,
        ollamaInstalled: ollama.installed,
      });
    } catch (err) {
      set({
        providers: { ollama: [FALLBACK_MODEL] },
        selectedModel: localStorage.getItem("llm_model") || FALLBACK_MODEL,
        status: "error",
        loadError: String(err),
      });
    }
    void fetchGpuMessage().then((msg: string | null) => {
      if (msg) set({ gpuMessage: msg, gpuStatus: "ready" });
      else set({ gpuStatus: "ready" });
    });
  },

  loadCards: async () => {
    try {
      const cards = await fetchProviderCards();
      const keys: Record<string, boolean> = {};
      for (const c of cards) {
        if (c.kind === "cloud") keys[c.id] = c.configured;
      }
      set({ cards, keysConfigured: keys, cardsStatus: "ready" });
    } catch {
      set({ cardsStatus: "error" });
    }
  },

  loadGpus: async () => {
    const [gpus, state] = await Promise.all([fetchGpus(), fetchOllamaState()]);
    set({
      gpus,
      targetGpuIndex: storedTargetGpus(gpus),
      ollamaLoaded: state.loaded,
      ollamaInstalled: state.installed,
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

  setTargetGpu: (index: number) => {
    localStorage.setItem(GPU_KEY, String(index));
    set({ targetGpuIndex: index });
  },
}));

/** Models for the currently selected provider (settings/chat dropdowns). */
export function useProviderModels(): string[] {
  const providers = useLlmStore((s) => s.providers);
  const selectedProvider = useLlmStore((s) => s.selectedProvider);
  return modelsFor(providers, selectedProvider);
}

/** Resolved target GPU card (null on single/absent GPU setups). */
export function useTargetGpu(): GpuInfo | null {
  const gpus = useLlmStore((s) => s.gpus);
  const targetGpuIndex = useLlmStore((s) => s.targetGpuIndex);
  if (gpus.length === 0) return null;
  return pickTargetGpu(gpus, targetGpuIndex ?? undefined);
}

/** True when at least one path can answer: local detected or cloud keyed. */
export function useLlmUsable(): boolean {
  const detected = useLlmStore((s) => s.detected);
  const keysConfigured = useLlmStore((s) => s.keysConfigured);
  return (
    Object.values(detected).some(Boolean) ||
    Object.values(keysConfigured).some(Boolean)
  );
}
