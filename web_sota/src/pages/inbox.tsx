import { Inbox } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

interface CritError {
  time?: string;
  source?: string;
  id?: number;
  type?: string;
  message?: string;
}

interface InboxSections {
  critical_errors?: CritError[];
  critical_errors_error?: string;
  blocked_mutations?: Record<string, unknown>[];
  blocked_mutations_error?: string;
  health?: Record<string, unknown>;
  health_error?: string;
  crash_dumps?: Record<string, unknown>;
  crash_dumps_error?: string;
}

interface InboxBody {
  status: string;
  sections: InboxSections;
}

/** Attention feed: critical event-log errors, blocked mutations, reboot + crash state. Live from GET /api/inbox. */
export function InboxPage() {
  const [data, setData] = useState<InboxBody | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch("/api/inbox");
      if (!r.ok) throw new Error(`/api/inbox: HTTP ${r.status}`);
      setData((await r.json()) as InboxBody);
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

  const s = data?.sections;
  const empty =
    s &&
    (s.critical_errors?.length ?? 0) === 0 &&
    (s.blocked_mutations?.length ?? 0) === 0 &&
    !s.health?.pending_reboot &&
    (s.crash_dumps?.minidumps as number | undefined) === 0;

  return (
    <div className="space-y-6" data-testid="inbox-page">
      <div className="flex items-center gap-3">
        <Inbox className="h-8 w-8 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Inbox
          </h1>
          <p className="text-sm text-slate-300">
            Everything on this machine that needs your attention.
          </p>
        </div>
        <button
          type="button"
          data-testid="inbox-refresh"
          onClick={() => void load()}
          className="ml-auto rounded bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <p className="text-sm text-slate-300">Checking system state…</p>
      )}

      {error && (
        <div
          data-testid="inbox-error"
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

      {data && empty && !loading && (
        <p className="text-sm text-slate-300" data-testid="inbox-empty">
          All quiet — no critical errors, no blocked mutations, no pending
          reboot, no crash dumps.
        </p>
      )}

      {s && (s.critical_errors?.length ?? 0) > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-200">
            Critical event-log errors ({s.critical_errors?.length})
          </h2>
          <div className="space-y-1" data-testid="inbox-errors">
            {s.critical_errors?.map((e) => (
              <div
                key={`${e.source ?? "src"}-${e.id ?? "noid"}-${e.time ?? ""}`}
                className="rounded border border-slate-800 bg-slate-900/60 px-3 py-2"
              >
                <div className="flex items-center gap-2 text-sm">
                  <span className="rounded bg-red-900/60 px-1.5 py-0.5 font-mono text-sm text-red-200">
                    {e.type ?? "Error"}
                  </span>
                  <span className="font-mono text-sm text-slate-300">
                    {e.source} #{e.id}
                  </span>
                  <span className="ml-auto font-mono text-sm text-slate-300">
                    {e.time}
                  </span>
                </div>
                <p className="mt-1 truncate text-sm text-slate-200">
                  {e.message}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {s && (s.blocked_mutations?.length ?? 0) > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-200">
            Blocked mutations ({s.blocked_mutations?.length})
          </h2>
          <div className="space-y-1" data-testid="inbox-blocked">
            {s.blocked_mutations?.map((r) => (
              <pre
                key={JSON.stringify(r)}
                className="overflow-x-auto rounded border border-amber-700/40 bg-amber-950/20 px-3 py-2 font-mono text-sm text-amber-200"
              >
                {JSON.stringify(r, null, 1)}
              </pre>
            ))}
          </div>
        </section>
      )}

      {s?.health && Object.keys(s.health).length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-200">
            Reboot / health
          </h2>
          <div
            className="rounded border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-200"
            data-testid="inbox-health"
          >
            {s.health.pending_reboot ? (
              <span className="text-amber-200">
                Reboot pending — schedule a restart.
              </span>
            ) : (
              <span>No reboot pending.</span>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
