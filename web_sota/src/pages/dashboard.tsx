import { Activity, Cpu, HardDrive, Server, Shield, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SystemStatus {
  service: string;
  version: string;
  status: string;
  uptime: number;
  system?: {
    cpu_usage_percent: number;
    cpu_count: number;
    memory: { percent: number; available: number; total: number };
    disk: { percent: number; free: number; total: number };
  };
}

interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_mb: number;
}

function fmtGB(bytes: number): string {
  return (bytes / 1024 / 1024 / 1024).toFixed(1);
}

function fmtUptime(secs: number): string {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function Dashboard() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [s, p] = await Promise.all([
          fetch("/api/status").then((r) => r.json()),
          fetch("/api/processes?sort_by=cpu&page_size=8").then((r) => r.json()),
        ]);
        if (cancelled) return;
        setStatus(s);
        setBackendOk(true);
        setProcesses(Array.isArray(p.processes) ? p.processes : []);
      } catch {
        if (!cancelled) setBackendOk(false);
      }
    };
    load();
    const iv = setInterval(load, 10000);
    return () => {
      cancelled = true;
      clearInterval(iv);
    };
  }, []);

  return (
    <div data-testid="dashboard" className="space-y-6">
      {/* Hero */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 p-8">
        <div className="flex items-center gap-2 mb-2">
          <span
            className={`w-2 h-2 rounded-full ${backendOk === null ? "bg-slate-500 animate-pulse" : backendOk ? "bg-emerald-500" : "bg-rose-500"}`}
            data-testid="backend-dot"
          />
          <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
            {backendOk === null
              ? "Connecting to backend..."
              : backendOk
                ? "Backend connected"
                : "Backend offline"}
          </span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          System Admin MCP
        </h1>
        <p className="text-slate-400 mt-2 max-w-2xl text-sm leading-relaxed">
          Monitor and manage this Windows machine through MCP tools: services,
          processes, volumes, NTFS file recovery, ACLs and permissions, event
          logs, disk health, and startup/taskbar management — available to
          Claude, Cursor, and other AI clients.
        </p>
        <div className="flex items-center gap-3 mt-4">
          <a
            href="#processes"
            className="text-xs font-semibold uppercase tracking-widest bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            View Processes
          </a>
          <a
            href="/tools"
            className="text-xs font-semibold uppercase tracking-widest border border-slate-700 text-slate-300 hover:bg-slate-800 px-4 py-2 rounded-lg transition-colors"
          >
            Explore Tools
          </a>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-server"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Server
            </CardTitle>
            <Server className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.status === "healthy" ? "Healthy" : "Unknown"}
            </div>
            <p className="text-xs text-slate-400">
              v{status?.version ?? "-"} · uptime{" "}
              {status ? fmtUptime(status.uptime) : "-"}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-cpu"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              CPU Load
            </CardTitle>
            <Cpu className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.system ? `${status.system.cpu_usage_percent}%` : "-"}
            </div>
            <p className="text-xs text-slate-400">
              {status?.system?.cpu_count ?? "-"} logical cores
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-memory"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Memory
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.system ? `${status.system.memory.percent}%` : "-"}
            </div>
            <p className="text-xs text-slate-400">
              {status?.system
                ? `${fmtGB(status.system.memory.available)} GB free of ${fmtGB(status.system.memory.total)}`
                : "-"}
            </p>
          </CardContent>
        </Card>

        <Card
          className="border-slate-800 bg-slate-950/50"
          data-testid="kpi-disk"
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Disk (C:)
            </CardTitle>
            <HardDrive className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.system ? `${status.system.disk.percent}%` : "-"}
            </div>
            <p className="text-xs text-slate-400">
              {status?.system
                ? `${fmtGB(status.system.disk.free)} GB free`
                : "-"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Top processes */}
        <div
          id="processes"
          className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-950/50 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white">Top Processes</h2>
            <span className="text-xs text-slate-500">
              {processes.length} by CPU · refresh 10s
            </span>
          </div>
          <div className="space-y-2">
            {processes.map((p) => (
              <div
                key={p.pid}
                className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-900/50 border border-slate-800"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">
                    {p.name}
                  </p>
                  <p className="text-[11px] text-slate-500 font-mono">
                    PID {p.pid}
                  </p>
                </div>
                <div className="flex items-center gap-6 text-xs font-mono text-slate-300">
                  <span>{p.cpu_percent?.toFixed(1)}% CPU</span>
                  <span className="w-20 text-right">
                    {p.memory_mb ? `${p.memory_mb.toFixed(0)} MB` : "-"}
                  </span>
                </div>
              </div>
            ))}
            {processes.length === 0 && (
              <p className="text-sm text-slate-500 py-8 text-center">
                No process data — is the backend running?
              </p>
            )}
          </div>
        </div>

        {/* Capabilities */}
        <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Wrench className="w-4 h-4 text-blue-500" />
            <h2 className="text-lg font-bold text-white">What this can do</h2>
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            {[
              "Services, processes & scheduled tasks",
              "NTFS file recovery & validation",
              "ACLs, permissions & ownership",
              "Disk health, defrag & cleanup",
              "Event logs & diagnostics",
              "Startup & taskbar management",
            ].map((item) => (
              <li key={item} className="flex items-center gap-2 text-xs">
                <Shield className="w-3 h-3 text-emerald-500 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
          <a
            href="/tools"
            className="mt-5 block text-center text-xs font-semibold uppercase tracking-widest bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2.5 rounded-lg transition-colors"
          >
            Browse all 44 tools
          </a>
        </div>
      </div>
    </div>
  );
}
