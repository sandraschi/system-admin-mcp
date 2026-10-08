import { RefreshCw, ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import API_BASE from "@/lib/api";

function ResultBlock({ data }: { data: unknown }) {
  if (data === null || data === undefined) return null;
  return (
    <pre className="text-xs text-slate-300 bg-slate-950 p-3 rounded border border-slate-800 whitespace-pre-wrap max-h-96 overflow-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

interface ProtectionData {
  status?: string;
  defender?: {
    status?: string;
    realtime_protection?: boolean;
    antivirus_enabled?: boolean;
    signature_last_updated?: string;
    error?: string;
  };
  vpn?: {
    status?: string;
    connected?: boolean;
    count?: number;
    profiles?: {
      name: string;
      server: string;
      tunnel: string;
      connected: boolean;
    }[];
    error?: string;
  };
  tailscale?: {
    status?: string;
    installed?: boolean;
    running?: boolean;
    backend_state?: string;
    tailnet_ips?: string[];
    self_hostname?: string;
    exit_node?: boolean;
    note?: string;
    error?: string;
  };
}

interface PortConnection {
  status: string;
  local_addr: string;
  remote_addr: string | null;
  pid: number;
  process: string;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${ok ? "bg-emerald-500" : "bg-slate-600"}`}
    />
  );
}

interface AirgapState {
  status?: string;
  airgapped?: boolean;
  firewall_outbound?: Record<string, string>;
  bluetooth?: {
    service?: { Status?: number | string; StartType?: number | string };
    adapters?: { Name?: string; Status?: string }[];
  };
  message?: string;
  error?: string;
  /** Enable/disable responses nest the fresh status here. */
  state?: AirgapState;
}

async function callAirgap(
  operation: "airgap_status" | "airgap_enable" | "airgap_disable",
  confirm = false,
): Promise<AirgapState> {
  const r = await fetch(`${API_BASE}/api/tools/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: "system_admin",
      arguments: { operation, confirm },
    }),
  });
  if (!r.ok) throw new Error(`/api/tools/call ${operation}: HTTP ${r.status}`);
  const d = await r.json();
  if (d.status !== "success") throw new Error(d.message || operation);
  return (d.result || {}) as AirgapState;
}

function AirgapSection() {
  const [state, setState] = useState<AirgapState | null>(null);
  const [armed, setArmed] = useState<"enable" | "disable" | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setState(await callAirgap("airgap_status"));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Disarm the two-step confirm after 8s without a second click.
  useEffect(() => {
    if (!armed) return;
    const t = window.setTimeout(() => setArmed(null), 8000);
    return () => window.clearTimeout(t);
  }, [armed]);

  const run = async (op: "airgap_enable" | "airgap_disable") => {
    const arm = op === "airgap_enable" ? "enable" : "disable";
    if (armed !== arm) {
      setArmed(arm);
      return;
    }
    setArmed(null);
    setBusy(true);
    setError(null);
    try {
      const next = await callAirgap(op, true);
      setState(next.state ? { ...next, ...(next.state as AirgapState) } : next);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const airgapped = !!state?.airgapped;
  const fw = state?.firewall_outbound || {};
  const btAdapters = state?.bluetooth?.adapters || [];

  return (
    <Card
      className={`backdrop-blur-xl ${airgapped ? "bg-red-950/40 border-red-700" : "bg-slate-900/50 border-slate-800"}`}
      data-testid="airgap-card"
    >
      <CardHeader>
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-red-500" />
          <CardTitle className="text-white">Airgap</CardTitle>
        </div>
        <CardDescription className="text-slate-400 text-xs">
          Cut all outside links instantly — firewall outbound BLOCK on every
          profile + Bluetooth stopped. Loopback and USB keyboards/mice keep
          working. Two clicks, never agent-implied.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <span
            data-testid="airgap-status"
            className={`text-sm font-semibold ${airgapped ? "text-red-300" : "text-emerald-300"}`}
          >
            {state
              ? airgapped
                ? "AIRGAPPED — outside links cut"
                : "Connected"
              : "Probing…"}
          </span>
          {!airgapped ? (
            <button
              type="button"
              data-testid="airgap-enable"
              disabled={busy}
              onClick={() => void run("airgap_enable")}
              className={`rounded-lg px-8 py-3 text-base font-bold uppercase tracking-widest text-white transition-colors disabled:opacity-50 ${
                armed === "enable"
                  ? "bg-red-500 hover:bg-red-400 animate-pulse"
                  : "bg-red-700 hover:bg-red-600"
              }`}
            >
              {armed === "enable" ? "Click again to confirm" : "Airgap"}
            </button>
          ) : (
            <button
              type="button"
              data-testid="airgap-disable"
              disabled={busy}
              onClick={() => void run("airgap_disable")}
              className={`rounded-lg px-8 py-3 text-base font-bold uppercase tracking-widest text-white transition-colors disabled:opacity-50 ${
                armed === "disable"
                  ? "bg-emerald-500 hover:bg-emerald-400 animate-pulse"
                  : "bg-emerald-700 hover:bg-emerald-600"
              }`}
            >
              {armed === "disable" ? "Click again to confirm" : "Reconnect"}
            </button>
          )}
        </div>
        {error && <p className="text-sm text-red-300">{error}</p>}
        <div className="grid gap-2 text-xs text-slate-400 md:grid-cols-2">
          <div>
            Firewall outbound:{" "}
            {Object.entries(fw).map(([profile, action]) => (
              <span key={profile} className="mr-2 font-mono">
                {profile}={action}
              </span>
            ))}
          </div>
          <div>
            Bluetooth:{" "}
            {btAdapters.length === 0
              ? "no adapters found"
              : btAdapters.map((a) => `${a.Name} (${a.Status})`).join(", ")}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function Security() {
  const [admins, setAdmins] = useState<unknown>(null);
  const [shares, setShares] = useState<unknown>(null);
  const [tasks, setTasks] = useState<unknown>(null);
  const [protection, setProtection] = useState<ProtectionData | null>(null);
  const [ports, setPorts] = useState<PortConnection[]>([]);
  const [portQuery, setPortQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s, t, p, n] = await Promise.all([
        fetch(`${API_BASE}/api/local-admins`).then((r) => r.json()),
        fetch(`${API_BASE}/api/smb-shares`).then((r) => r.json()),
        fetch(`${API_BASE}/api/scheduled-tasks?max_results=50`).then((r) =>
          r.json(),
        ),
        fetch(`${API_BASE}/api/protection`).then((r) => r.json()),
        fetch(`${API_BASE}/api/network-ports`).then((r) => r.json()),
      ]);
      setAdmins(a);
      setShares(s);
      setTasks(t);
      setProtection(p);
      setPorts(Array.isArray(n.connections) ? n.connections : []);
    } catch (e) {
      setAdmins({ status: "error", error: String(e) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <div className="space-y-6" data-testid="security-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Security audit
          </h1>
          <p className="text-slate-400 text-sm">
            Local admins, SMB shares, scheduled tasks, protection, ports
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchAll}
          disabled={loading}
          data-testid="security-refresh"
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      <AirgapSection />

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-500" />
            <CardTitle className="text-white">Local administrators</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Administrators group members and local users
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={admins} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <CardTitle className="text-white">SMB shares</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Shares, paths, open sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={shares} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-blue-500" />
            <CardTitle className="text-white">Scheduled tasks</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            First 50 tasks - persistence and updater review
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={tasks} />
        </CardContent>
      </Card>

      <Card
        className="bg-slate-900/50 border-slate-800 backdrop-blur-xl"
        data-testid="protection-card"
      >
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-emerald-500" />
            <CardTitle className="text-white">Protection</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Defender, Windows VPN, Tailscale — basic status (full mesh
            management lives in tailscale-mcp)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <StatusDot ok={!!protection?.defender?.realtime_protection} />
              <span className="text-slate-200 w-28">Defender</span>
              <span className="text-slate-400 text-xs">
                {protection?.defender?.status === "error"
                  ? `unreachable (${protection.defender.error || "?"})`
                  : protection?.defender?.realtime_protection
                    ? `realtime on${protection?.defender?.signature_last_updated ? ` · sig ${protection.defender.signature_last_updated}` : ""}`
                    : "realtime OFF"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot ok={!!protection?.vpn?.connected} />
              <span className="text-slate-200 w-28">Windows VPN</span>
              <span className="text-slate-400 text-xs">
                {protection?.vpn?.status === "error"
                  ? `unreachable (${protection.vpn.error || "?"})`
                  : (protection?.vpn?.count || 0) === 0
                    ? "no profiles configured"
                    : `${
                        protection?.vpn?.profiles
                          ?.filter((p) => p.connected)
                          .map((p) => p.name)
                          .join(", ") || "profiles present, none connected"
                      } (${protection?.vpn?.count} profile${protection?.vpn?.count === 1 ? "" : "s"})`}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusDot
                ok={
                  !!protection?.tailscale?.running &&
                  !!protection?.tailscale?.backend_state
                    ?.toLowerCase()
                    .startsWith("run")
                }
              />
              <span className="text-slate-200 w-28">Tailscale</span>
              <span className="text-slate-400 text-xs">
                {!protection?.tailscale?.installed
                  ? "not installed"
                  : !protection?.tailscale?.running
                    ? "installed, daemon stopped"
                    : `${protection?.tailscale?.backend_state || "unknown state"}${protection?.tailscale?.tailnet_ips?.length ? ` · ${protection.tailscale.tailnet_ips.join(", ")}` : ""}${protection?.tailscale?.exit_node ? " · exit node" : ""}`}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card
        className="bg-slate-900/50 border-slate-800 backdrop-blur-xl"
        data-testid="ports-card"
      >
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-cyan-500" />
            <CardTitle className="text-white">
              Network ports ({ports.length})
            </CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Listening + established sockets with owning process
          </CardDescription>
        </CardHeader>
        <CardContent>
          <input
            data-testid="ports-search"
            value={portQuery}
            onChange={(e) => setPortQuery(e.target.value)}
            placeholder="Filter port, address, process…"
            className="mb-2 h-8 w-64 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200"
          />
          <div className="max-h-96 overflow-auto rounded border border-slate-800">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-900">
                <tr className="text-left text-slate-400">
                  <th className="px-2 py-1">Status</th>
                  <th className="px-2 py-1">Local</th>
                  <th className="px-2 py-1">Remote</th>
                  <th className="px-2 py-1">Process</th>
                  <th className="px-2 py-1">PID</th>
                </tr>
              </thead>
              <tbody>
                {ports
                  .filter(
                    (c) =>
                      !portQuery.trim() ||
                      `${c.local_addr} ${c.remote_addr || ""} ${c.process} ${c.pid} ${c.status}`
                        .toLowerCase()
                        .includes(portQuery.trim().toLowerCase()),
                  )
                  .slice(0, 200)
                  .map((c) => (
                    <tr
                      key={`${c.status}-${c.local_addr}-${c.remote_addr || ""}-${c.pid}-${c.process}`}
                      className="border-t border-slate-800/60 text-slate-300"
                    >
                      <td className="px-2 py-1">{c.status}</td>
                      <td className="px-2 py-1 font-mono">{c.local_addr}</td>
                      <td className="px-2 py-1 font-mono">
                        {c.remote_addr || "—"}
                      </td>
                      <td className="px-2 py-1 font-mono">{c.process}</td>
                      <td className="px-2 py-1 font-mono">{c.pid}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
