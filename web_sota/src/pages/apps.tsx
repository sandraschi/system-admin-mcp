import { LayoutGrid } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface FleetApp {
  port: number;
  name: string;
  description: string;
}

interface FleetApps {
  success: boolean;
  known: FleetApp[];
  experimental: FleetApp[];
  count?: number;
  registry?: string;
  note?: string;
}

/** Fleet app discovery: live from GET /api/fleet/apps (registry-filtered). */
export function Apps() {
  const [data, setData] = useState<FleetApps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/fleet/apps");
      if (!r.ok) throw new Error(`/api/fleet/apps: HTTP ${r.status}`);
      setData((await r.json()) as FleetApps);
    } catch (err) {
      setError(String(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6" data-testid="apps-page">
      <div className="flex items-center gap-3">
        <LayoutGrid className="w-8 h-8 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Apps Hub
          </h1>
          <p className="text-slate-400 text-sm">
            Centralized SOTA fleet navigation
          </p>
        </div>
        <button
          type="button"
          data-testid="apps-refresh"
          onClick={() => void load()}
          className="ml-auto rounded bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <p className="text-sm text-slate-300">Discovering fleet apps…</p>
      )}

      {error && (
        <div
          data-testid="apps-error"
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

      {data?.note && (
        <p className="text-sm text-slate-300" data-testid="apps-note">
          {data.note}
        </p>
      )}

      {data && data.known.length === 0 && !loading && (
        <p className="text-sm text-slate-300">
          Registry contained no entries. Start the backend and retry.
        </p>
      )}

      {data && data.known.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-200">
            Registered ({data.known.length})
          </h2>
          <div
            className="grid gap-3 md:grid-cols-2 lg:grid-cols-3"
            data-testid="apps-known"
          >
            {data.known.map((app) => (
              <a
                key={`${app.port}-${app.name}`}
                href={`http://127.0.0.1:${app.port}/`}
                target="_blank"
                rel="noopener noreferrer"
                className={`block rounded-lg border p-3 transition-colors ${
                  app.name === "system-admin-mcp"
                    ? "border-blue-500/50 bg-blue-950/20 hover:bg-blue-900/30"
                    : "border-slate-800 bg-slate-900/60 hover:bg-slate-800"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-14 font-mono text-sm text-blue-400">
                    {app.port}
                  </span>
                  <span className="min-w-0 flex-1 truncate font-mono text-sm text-slate-100">
                    {app.name}
                  </span>
                </div>
                {app.description && (
                  <p className="mt-1 truncate text-sm text-slate-400">
                    {app.description}
                  </p>
                )}
              </a>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-200">
          Experimental (not in registry)
        </h2>
        {data && data.experimental.length > 0 ? (
          <div className="space-y-1" data-testid="apps-experimental">
            {data.experimental.map((app) => (
              <div
                key={`${app.port}-${app.name}`}
                className="flex items-center gap-3 rounded border border-slate-800/60 bg-slate-900/30 px-3 py-2"
              >
                <span className="w-14 font-mono text-sm text-slate-300">
                  {app.port}
                </span>
                <span className="font-mono text-sm text-slate-200">
                  {app.name}
                </span>
                <span className="truncate text-sm text-slate-400">
                  {app.description}
                </span>
              </div>
            ))}
          </div>
        ) : (
          !loading && (
            <p
              className="text-sm text-slate-300"
              data-testid="apps-experimental-empty"
            >
              None detected.
            </p>
          )
        )}
      </section>
    </div>
  );
}
