import { AlertTriangle, RefreshCw, Skull, Sprout } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import API_BASE from "@/lib/api";

interface Candidate {
  pid: number;
  name: string;
  create_time: number;
  rule: string;
  reason: string;
  auto_ok: boolean;
  age_s: number;
  rss_mb: number;
  cpu_percent: number;
  parent: string;
  window_title: string;
  cmdline: string;
}

interface Pressure {
  level: "ok" | "warn" | "critical";
  memory_percent: number;
  available_gb: number;
  total_gb: number;
}

interface ScanResult {
  status: string;
  error?: string;
  pressure?: Pressure;
  summary?: {
    candidates: number;
    reclaimable_mb: number;
    auto_eligible: number;
    by_rule: Record<string, { count: number; rss_mb: number }>;
  };
  candidates?: Candidate[];
}

interface KillResult {
  status: string;
  error?: string;
  killed?: Array<{ pid: number; name: string; rule: string; rss_mb: number }>;
  skipped?: Array<{ pid: number; reason: string }>;
  freed_mb_estimate?: number;
}

const RULE_HELP: Record<string, string> = {
  orphan_engine:
    "Headless engine whose launcher is gone (only rule the sweep may kill)",
  orphan_dev: "Idle dev tool whose parent is gone",
  duplicate_app: "Extra instances of a single-use app",
  duplicate_game: "Several windows of the same Godot project",
  orphan_game: "Godot game window left open, launcher gone",
  stale_headless: "Headless process running for hours",
  shell_debris: "Idle console with no parent and no children",
  unregistered_port: "Dev server on a port not in WEBAPP_PORTS.md",
};

function age(s: number): string {
  if (s >= 86400)
    return `${Math.floor(s / 86400)}d ${Math.floor((s % 86400) / 3600)}h`;
  if (s >= 3600)
    return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 60)}m`;
}

export function Weeder() {
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [result, setResult] = useState<KillResult | null>(null);
  const [confirming, setConfirming] = useState(false);

  const runScan = useCallback(async () => {
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch(`${API_BASE}/api/weeder/scan`);
      const data: ScanResult = await r.json();
      setScan(data);
      // Preselect only the auto-eligible ones; everything else is opt-in.
      setSelected(
        new Set(
          (data.candidates ?? []).filter((c) => c.auto_ok).map((c) => c.pid),
        ),
      );
    } catch (e) {
      setScan({ status: "error", error: String(e) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    runScan();
  }, [runScan]);

  const candidates = scan?.candidates ?? [];
  const selectedMb = useMemo(
    () =>
      candidates
        .filter((c) => selected.has(c.pid))
        .reduce((a, c) => a + c.rss_mb, 0),
    [candidates, selected],
  );

  const toggle = (pid: number) => {
    setConfirming(false);
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid);
      else next.add(pid);
      return next;
    });
  };

  const selectRule = (rule: string) => {
    setConfirming(false);
    setSelected(
      new Set(candidates.filter((c) => c.rule === rule).map((c) => c.pid)),
    );
  };

  const killSelected = async () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setConfirming(false);
    setLoading(true);
    try {
      const targets = candidates
        .filter((c) => selected.has(c.pid))
        .map((c) => ({ pid: c.pid, create_time: c.create_time }));
      const r = await fetch(`${API_BASE}/api/weeder/kill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ targets, confirm: true }),
      });
      setResult(await r.json());
    } catch (e) {
      setResult({ status: "error", error: String(e) });
    } finally {
      setLoading(false);
    }
    runScan();
  };

  const p = scan?.pressure;
  const pressureColor =
    p?.level === "critical"
      ? "border-red-500/60 bg-red-950/30"
      : p?.level === "warn"
        ? "border-amber-500/60 bg-amber-950/30"
        : "border-emerald-500/40 bg-emerald-950/20";

  return (
    <div className="space-y-6" data-testid="weeder-page">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Sprout className="h-6 w-6 text-emerald-400" />
          <div>
            <h1 className="text-2xl font-bold">RAM Weeder</h1>
            <p className="text-sm text-slate-300">
              Leaked processes found by rule. Nothing is killed until you select
              it and confirm.
            </p>
          </div>
        </div>
        <Button onClick={runScan} disabled={loading} data-testid="weeder-scan">
          <RefreshCw
            className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`}
          />
          Scan
        </Button>
      </div>

      {scan?.status === "error" && (
        <div className="rounded border border-red-500/60 p-3 text-sm text-red-300">
          {scan.error}
        </div>
      )}

      {p && (
        <div
          className={`rounded border p-4 ${pressureColor}`}
          data-testid="weeder-pressure"
        >
          <div className="flex items-center gap-2 text-base font-semibold">
            {p.level !== "ok" && <AlertTriangle className="h-5 w-5" />}
            Memory {p.memory_percent}% used ({p.available_gb} of {p.total_gb} GB
            free)
            <span className="ml-2 text-sm uppercase">{p.level}</span>
          </div>
          {scan?.summary && (
            <div className="mt-1 text-sm text-slate-300">
              {scan.summary.candidates} candidates, about{" "}
              {Math.round(scan.summary.reclaimable_mb).toLocaleString()} MB
              reclaimable, {scan.summary.auto_eligible} eligible for the
              automatic sweep.
            </div>
          )}
        </div>
      )}

      {scan?.summary && Object.keys(scan.summary.by_rule).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(scan.summary.by_rule).map(([rule, v]) => (
            <button
              key={rule}
              type="button"
              onClick={() => selectRule(rule)}
              title={RULE_HELP[rule] ?? rule}
              className="rounded border border-slate-600 px-3 py-1 text-sm hover:bg-slate-800"
            >
              {rule}: {v.count} ({Math.round(v.rss_mb).toLocaleString()} MB)
            </button>
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Candidates</CardTitle>
          <CardDescription>
            Click a rule above to select all of its candidates. Every kill is
            re-checked (same process, rule still matches), takes the whole
            process tree, and is written to the mutation audit log.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {candidates.length === 0 ? (
            <p className="text-sm text-slate-300">No leaked processes found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-slate-300">
                  <tr>
                    <th className="p-2" />
                    <th className="p-2">Process</th>
                    <th className="p-2">Rule</th>
                    <th className="p-2 text-right">MB</th>
                    <th className="p-2 text-right">Age</th>
                    <th className="p-2">Parent</th>
                    <th className="p-2">Why</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((c) => (
                    <tr
                      key={c.pid}
                      className="border-t border-slate-800 align-top"
                    >
                      <td className="p-2">
                        <input
                          type="checkbox"
                          aria-label={`select ${c.name} ${c.pid}`}
                          checked={selected.has(c.pid)}
                          onChange={() => toggle(c.pid)}
                        />
                      </td>
                      <td className="p-2" title={c.cmdline}>
                        <div className="font-medium">{c.name}</div>
                        <div className="text-xs text-slate-400">
                          pid {c.pid}
                          {c.window_title ? ` | ${c.window_title}` : ""}
                        </div>
                      </td>
                      <td className="p-2">
                        {c.rule}
                        {c.auto_ok && (
                          <span className="ml-1 rounded bg-emerald-800 px-1 text-xs">
                            auto
                          </span>
                        )}
                      </td>
                      <td className="p-2 text-right">
                        {Math.round(c.rss_mb).toLocaleString()}
                      </td>
                      <td className="p-2 text-right">{age(c.age_s)}</td>
                      <td className="p-2 text-xs">{c.parent}</td>
                      <td className="p-2 text-xs">{c.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4 flex items-center gap-3">
            <Button
              onClick={killSelected}
              disabled={loading || selected.size === 0}
              className={confirming ? "bg-red-700 hover:bg-red-800" : ""}
              data-testid="weeder-kill"
            >
              <Skull className="mr-2 h-4 w-4" />
              {confirming
                ? `Really kill ${selected.size} (about ${Math.round(selectedMb).toLocaleString()} MB)?`
                : `Kill selected (${selected.size})`}
            </Button>
            {confirming && (
              <Button onClick={() => setConfirming(false)} variant="outline">
                Cancel
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Last action</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {result.error && <p className="text-red-300">{result.error}</p>}
            {(result.killed ?? []).map((k) => (
              <p key={`k${k.pid}`}>
                killed {k.name} (pid {k.pid}, {k.rule}, {Math.round(k.rss_mb)}{" "}
                MB)
              </p>
            ))}
            {(result.skipped ?? []).map((s) => (
              <p key={`s${s.pid}`} className="text-amber-300">
                skipped pid {s.pid}: {s.reason}
              </p>
            ))}
            {result.freed_mb_estimate !== undefined && (
              <p className="font-medium">
                about {Math.round(result.freed_mb_estimate).toLocaleString()} MB
                freed
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
