import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { pollInstallStatus, startInstall } from "@/lib/llm";

type Phase = "idle" | "starting" | "running" | "done" | "error";

/**
 * One-click Ollama install (backend allowlist, winget, background job).
 * Polls /api/llm/install/status until terminal; on done, prompts reload
 * so provider detection re-runs.
 */
export function InstallOllamaButton({ onDone }: { onDone?: () => void }) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [note, setNote] = useState("");
  const timer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current !== null) window.clearInterval(timer.current);
    };
  }, []);

  const poll = () => {
    timer.current = window.setInterval(() => {
      pollInstallStatus("ollama")
        .then((s) => {
          if (s.state === "done") {
            if (timer.current !== null) window.clearInterval(timer.current);
            setPhase("done");
            setNote("Installed — reload to detect it.");
            onDone?.();
          } else if (s.state === "error") {
            if (timer.current !== null) window.clearInterval(timer.current);
            setPhase("error");
            setNote(s.output || "Install failed — see backend logs.");
          } else {
            setPhase("running");
            setNote("Installing Ollama via winget…");
          }
        })
        .catch((e: unknown) => {
          if (timer.current !== null) window.clearInterval(timer.current);
          setPhase("error");
          setNote(e instanceof Error ? e.message : String(e));
        });
    }, 4000);
  };

  const start = () => {
    setPhase("starting");
    setNote("Starting installer…");
    startInstall("ollama")
      .then((r) => {
        if (!r.started) {
          setPhase("error");
          setNote(r.reason || "Installer refused to start.");
          return;
        }
        poll();
      })
      .catch((e: unknown) => {
        setPhase("error");
        setNote(e instanceof Error ? e.message : String(e));
      });
  };

  if (phase === "done") {
    return (
      <span className="text-xs text-emerald-300">
        {note}{" "}
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="underline hover:text-emerald-200"
        >
          Reload
        </button>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2">
      <Button
        type="button"
        disabled={phase === "starting" || phase === "running"}
        onClick={start}
        data-testid="llm-install-ollama"
        className="h-8 text-xs bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50"
      >
        {phase === "idle" ? "Install Ollama" : "Installing…"}
      </Button>
      {note && <span className="text-xs text-slate-400">{note}</span>}
    </span>
  );
}
