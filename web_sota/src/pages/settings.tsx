import { Settings as SettingsIcon, Shield, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import API_BASE from "@/lib/api";

function LLMSettings() {
  const [providers, setProviders] = useState<
    Record<string, { name: string }[]>
  >({});
  const [detected, setDetected] = useState<Record<string, boolean>>({});
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  useEffect(() => {
    fetch(`${API_BASE}/api/llm/discover`)
      .then((r) => r.json())
      .then((d) => {
        const byName: Record<string, { name: string }[]> = {};
        const det: Record<string, boolean> = {};
        for (const p of d.providers || []) {
          byName[p.name] = (p.models || []).map((m: string) => ({ name: m }));
          det[p.name] = !!p.detected;
        }
        setProviders(byName);
        setDetected(det);
        const savedP = localStorage.getItem("llm_provider") || "ollama";
        const savedM = localStorage.getItem("llm_model") || "";
        setSelectedProvider(savedP);
        const models =
          byName[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
        setSelectedModel(
          savedM && models.some((m: { name: string }) => m.name === savedM)
            ? savedM
            : models[0]?.name || "",
        );
      })
      .catch(() => {
        setProviders({ ollama: [{ name: "llama3.2:3b" }] });
        setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
      });
  }, []);
  const save = (p: string, m: string) => {
    localStorage.setItem("llm_provider", p);
    localStorage.setItem("llm_model", m);
  };
  const models =
    providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <span
          className={`w-2 h-2 rounded-full ${detected[selectedProvider] ? "bg-emerald-500" : "bg-slate-600"}`}
        />
        {detected[selectedProvider]
          ? `${selectedProvider} detected`
          : `${selectedProvider} not detected`}
      </div>
      <select
        data-testid="llm-provider-select"
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-sm text-slate-200"
        value={selectedProvider}
        onChange={(e) => {
          setSelectedProvider(e.target.value);
          save(e.target.value, "");
        }}
      >
        <option value="ollama">Ollama</option>
        <option value="lm_studio">LM Studio</option>
      </select>
      <select
        data-testid="llm-model-select"
        className="h-9 w-full rounded-md border border-slate-700 bg-slate-950 px-3 text-sm text-slate-200"
        value={selectedModel}
        onChange={(e) => {
          setSelectedModel(e.target.value);
          save(selectedProvider, e.target.value);
        }}
      >
        {models.map((m) => (
          <option key={m.name} value={m.name}>
            {m.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export function Settings() {
  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <SettingsIcon className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              System Settings
            </h1>
            <p className="text-slate-400 text-sm italic">
              Backend status and local LLM provider configuration
            </p>
          </div>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700 active:scale-95 transition-all">
          Save Configuration
        </Button>
      </div>

      <div className="grid gap-8">
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-white font-semibold">
            Intelligence Engine (LLM)
          </div>
          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardContent className="pt-6">
              <LLMSettings />
            </CardContent>
          </Card>
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2 text-white font-semibold">
            <Shield className="w-5 h-5 text-orange-500" />
            Elevation & Security
          </div>
          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div>
                  <div className="text-sm font-medium text-white">
                    Auto-Elevate Bridge
                  </div>
                  <div className="text-xs text-slate-500">
                    Attempt to run backend as Administrator on startup
                  </div>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div>
                  <div className="text-sm font-medium text-white">
                    Audit Operations
                  </div>
                  <div className="text-xs text-slate-500">
                    Log all tool execution results to local memory
                  </div>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2 text-white font-semibold">
            <Zap className="w-5 h-5 text-yellow-500" />
            Server Orchestration
          </div>
          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardContent className="pt-6 space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label className="text-slate-300">Frontend Port</Label>
                  <Input
                    type="number"
                    defaultValue="10860"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">
                    Backend Port (Bridge)
                  </Label>
                  <Input
                    type="number"
                    defaultValue="10861"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
