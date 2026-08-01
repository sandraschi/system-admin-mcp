import {
  Bot,
  Brain,
  Download,
  Eraser,
  Send,
  Sparkles,
  User,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const HISTORY_KEY = "system-admin-chat-history";
const PERSONALITY_KEY = "system-admin-chat-personality";
const MAX_HISTORY = 100;

const PERSONALITIES: Record<string, string> = {
  SysAdmin:
    "You are a Windows system administrator. Focus on services, processes, scheduled tasks, and system health. Provide clear diagnostic steps and remediation actions.",
  "Security Hardener":
    "You are a security hardening specialist. Prioritize Windows security configurations, ACL audits, threat detection, and system hardening best practices.",
  "Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
  Custom: "Custom prompt \u2014 editable below.",
};

const EXAMPLE_PROMPTS = [
  {
    group: "Services",
    prompts: [
      "List running services",
      "Restart the spooler service",
      "Show failed services",
    ],
  },
  {
    group: "Processes",
    prompts: [
      "Show top CPU processes",
      "Find process by name",
      "Kill process with PID 1234",
    ],
  },
  {
    group: "Tasks",
    prompts: [
      "List scheduled tasks",
      "Check disk health",
      "Show system information",
    ],
  },
];

export function Chat() {
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(PERSONALITY_KEY) || "SysAdmin",
  );
  const [messages, setMessages] = useState<
    { id: string; role: "user" | "assistant"; content: string }[]
  >(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
      return Array.isArray(saved) ? saved : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("llama3.2:3b");
  const msgIdRef = useRef(0);
  const [models, setModels] = useState<string[]>([]);
  const [providerOk, setProviderOk] = useState<boolean | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
  }, [messages]);
  useEffect(() => {
    localStorage.setItem(PERSONALITY_KEY, personality);
  }, [personality]);
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/llm/discover")
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        const found = (d.providers || []).find(
          (p: { name: string }) => p.name === provider,
        );
        setProviderOk(!!found?.detected);
        setModels(found?.models?.length ? found.models : ["llama3.2:3b"]);
      })
      .catch(() => {
        if (!cancelled) setProviderOk(false);
      });
    return () => {
      cancelled = true;
    };
  }, [provider]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text) return;
    const userMsg = {
      id: `m${msgIdRef.current++}`,
      role: "user" as const,
      content: text,
    };
    setMessages((prev) => {
      const next = [...prev, userMsg];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
    setInput("");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, provider, model }),
      });
      const data = await res.json();
      if (!res.ok || data.status !== "success") {
        throw new Error(data.message || `HTTP ${res.status}`);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `m${msgIdRef.current++}`,
          role: "assistant",
          content: data.response,
        },
      ]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setMessages((prev) => [
        ...prev,
        {
          id: `m${msgIdRef.current++}`,
          role: "assistant",
          content: `LLM unavailable: ${msg}\n\nStart Ollama (port 11434) or LM Studio (port 1234) to enable chat.`,
        },
      ]);
    }
  }, [input, provider, model]);

  const exportChat = () => {
    const text = messages
      .map((m) => `[${m.role.toUpperCase()}] ${m.content}`)
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "system-admin-chat.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div
      data-testid="chat-page"
      className="flex flex-col h-[calc(100vh-120px)] space-y-4"
    >
      <div
        data-testid="chat-controls"
        className="flex items-center justify-between flex-wrap gap-2"
      >
        <div className="flex items-center gap-3">
          <Bot className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold text-white">AI Command</h1>
            <p className="text-slate-400 text-xs italic">
              Multi-model system orchestration bridge
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">
            skill:system-admin-expert
          </span>
          <select
            data-testid="personality-select"
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
          >
            {Object.keys(PERSONALITIES).map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <button
            type="button"
            data-testid="chat-export"
            onClick={exportChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Export"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-clear"
            onClick={clearChat}
            disabled={messages.length === 0}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30"
            title="Clear"
          >
            <Eraser className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-4 p-2 bg-slate-900/50 border border-slate-800 rounded-xl flex-wrap">
        <div className="flex items-center gap-2">
          <span
            data-testid="llm-provider-status"
            className={`w-2 h-2 rounded-full ${providerOk === null ? "bg-slate-500 animate-pulse" : providerOk ? "bg-emerald-500" : "bg-rose-500"}`}
          />
          <select
            data-testid="llm-provider-select"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="w-[150px] h-8 bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded px-2"
          >
            <option value="ollama">Ollama (Local)</option>
            <option value="lm_studio">LM Studio</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <select
            data-testid="llm-model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-[200px] h-8 bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded px-2"
          >
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">
          {providerOk === null
            ? "Detecting provider..."
            : providerOk
              ? `${provider} connected`
              : "No local LLM detected"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6">
        {messages.length === 0 ? (
          <div className="text-center text-slate-500 py-8 text-sm">
            Ask about services, processes, disk health, event logs, or security
            — powered by your local LLM (Ollama or LM Studio).
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`p-2 rounded-xl h-fit border shadow-lg ${msg.role === "assistant" ? "bg-blue-500/10 border-blue-500/20 text-blue-400" : "bg-slate-800/50 border-slate-700 text-slate-300"}`}
              >
                {msg.role === "assistant" ? (
                  <Sparkles className="w-4 h-4" />
                ) : (
                  <User className="w-4 h-4" />
                )}
              </div>
              <div
                className={`max-w-[80%] space-y-1 ${msg.role === "user" ? "text-right" : ""}`}
              >
                <div className="text-xs font-bold text-slate-500 uppercase tracking-tighter">
                  {msg.role === "assistant"
                    ? "System Intelligence"
                    : "Operator"}{" "}
                  \u2022{" "}
                  {new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
                <div
                  className={`p-4 rounded-3xl text-sm leading-relaxed ${msg.role === "assistant" ? "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none border-l-4 border-l-blue-500" : "bg-blue-600 text-white rounded-tr-none"} shadow-2xl`}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={scrollRef} />
      </div>

      <div data-testid="example-prompts" className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((group) => (
          <div key={group.group} className="flex flex-wrap items-center gap-1">
            <span className="text-xs text-slate-500 mr-1">{group.group}:</span>
            {group.prompts.map((p) => (
              <button
                type="button"
                key={p}
                onClick={() => setInput(p)}
                className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded"
              >
                {p}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="border-t border-slate-800 bg-slate-950/50 p-6">
        <div className="relative flex items-center gap-3">
          <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
            <Brain className="w-5 h-5 text-purple-500" />
          </div>
          <input
            data-testid="chat-input"
            className="flex-1 bg-slate-900/50 border border-slate-800 text-slate-100 placeholder:text-slate-500 rounded-2xl h-12 px-4 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Type a system directive..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            type="button"
            data-testid="chat-send"
            onClick={send}
            disabled={!input.trim()}
            className="absolute right-1 w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
