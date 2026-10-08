import { AppWindow, BellRing } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import API_BASE from "@/lib/api";

interface TaskbarWindow {
  hwnd: number;
  title: string;
  pid: number;
  process: string;
  exe: string;
  autostart: boolean;
  startup_name?: string;
  startup_location?: string;
}

interface TrayIcon {
  area: string;
  tooltip: string;
  source: string;
  confidence: string;
  autostart: boolean;
  startup_name?: string;
  startup_location?: string;
  process_guess: { pid: number; process: string; exe: string } | null;
}

async function callOp(operation: string): Promise<Record<string, unknown>> {
  const r = await fetch(`${API_BASE}/api/tools/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "system_admin", arguments: { operation } }),
  });
  if (!r.ok) throw new Error(`/api/tools/call ${operation}: HTTP ${r.status}`);
  return r.json();
}

function matches(q: string, ...fields: (string | undefined)[]): boolean {
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  return fields.some((f) => (f || "").toLowerCase().includes(needle));
}

function AutostartBadge({
  autostart,
  name,
  location,
}: {
  autostart: boolean;
  name?: string;
  location?: string;
}) {
  if (!autostart) return null;
  return (
    <span
      title={`Autostarts via ${name || "?"} (${location || "?"})`}
      className="rounded bg-amber-900/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-amber-200"
    >
      Autostart
    </span>
  );
}

/** Taskbar buttons + tray icons: who is running, who autostarts. */
export function Taskbar() {
  const [windows, setWindows] = useState<TaskbarWindow[]>([]);
  const [icons, setIcons] = useState<TrayIcon[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [autoOnly, setAutoOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [w, t] = await Promise.all([
        callOp("list_taskbar_windows"),
        callOp("list_tray_icons"),
      ]);
      if (w.status !== "success")
        throw new Error(String(w.error || "windows failed"));
      setWindows((w.windows as TaskbarWindow[]) || []);
      if (t.status === "success") {
        setIcons((t.icons as TrayIcon[]) || []);
        setNote(typeof t.note === "string" ? t.note : "");
      } else {
        setIcons([]);
        setNote(typeof t.note === "string" ? t.note : String(t.error || ""));
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const winList = windows.filter(
    (w) =>
      (!autoOnly || w.autostart) && matches(query, w.title, w.process, w.exe),
  );
  const iconList = icons.filter(
    (i) =>
      (!autoOnly || i.autostart) &&
      matches(query, i.tooltip, i.process_guess?.process, i.process_guess?.exe),
  );

  return (
    <div className="space-y-6" data-testid="taskbar-page">
      <div className="flex items-center gap-3 flex-wrap">
        <AppWindow className="w-8 h-8 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Taskbar
          </h1>
          <p className="text-slate-400 text-sm">
            Buttons, tray icons, and who autostarts them
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <input
            data-testid="taskbar-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search title, process, exe…"
            className="h-9 w-64 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm text-slate-200"
          />
          <label className="flex items-center gap-1.5 text-xs text-slate-300">
            <input
              type="checkbox"
              data-testid="taskbar-autostart-only"
              checked={autoOnly}
              onChange={(e) => setAutoOnly(e.target.checked)}
              className="accent-amber-500"
            />
            Autostart only
          </label>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-slate-300">Reading taskbar…</p>}

      {error && (
        <div
          data-testid="taskbar-error"
          className="flex items-center justify-between rounded border border-red-700/50 bg-red-950/40 p-3 text-sm text-red-200"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded bg-red-900/60 px-2 py-0.5 hover:bg-red-800"
          >
            Retry
          </button>
        </div>
      )}

      {note && <p className="text-xs text-slate-500">{note}</p>}

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-200">
          Taskbar buttons ({winList.length})
        </h2>
        <div className="space-y-1" data-testid="taskbar-windows">
          {winList.map((w) => (
            <div
              key={w.hwnd}
              className="flex items-center gap-3 rounded border border-slate-800 bg-slate-900/60 px-3 py-2"
            >
              <span className="min-w-0 flex-1 truncate text-sm text-slate-100">
                {w.title}
              </span>
              <span className="font-mono text-xs text-slate-400">
                {w.process}
              </span>
              <AutostartBadge
                autostart={w.autostart}
                name={w.startup_name}
                location={w.startup_location}
              />
            </div>
          ))}
          {!loading && winList.length === 0 && (
            <p className="text-sm text-slate-300">No windows match.</p>
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-200">
          <BellRing className="h-4 w-4 text-slate-400" />
          Tray icons ({iconList.length})
        </h2>
        <div className="space-y-1" data-testid="taskbar-tray">
          {iconList.map((icon) => (
            <div
              key={`${icon.area}-${icon.process_guess?.pid ?? "na"}-${icon.tooltip || icon.process_guess?.process || "unknown"}`}
              className="flex items-center gap-3 rounded border border-slate-800/60 bg-slate-900/30 px-3 py-2"
            >
              <span className="min-w-0 flex-1 truncate text-sm text-slate-100">
                {icon.tooltip || "(no tooltip)"}
              </span>
              <span className="font-mono text-xs text-slate-400">
                {icon.process_guess?.process || "unknown owner"}
              </span>
              {icon.confidence !== "exact" && icon.process_guess && (
                <span className="text-[10px] uppercase tracking-wider text-slate-500">
                  {icon.confidence} guess
                </span>
              )}
              <AutostartBadge
                autostart={icon.autostart}
                name={icon.startup_name}
                location={icon.startup_location}
              />
            </div>
          ))}
          {!loading && iconList.length === 0 && (
            <p className="text-sm text-slate-300">No tray icons readable.</p>
          )}
        </div>
      </section>
    </div>
  );
}
