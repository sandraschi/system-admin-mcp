import { Cpu, Download, RefreshCw, Search, Skull, X } from "lucide-react";
import { download, toCsv } from "@/common/export";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface ProcessRow {
  pid: number;
  name: string;
  cpu_percent?: number;
  memory_mb?: number;
  memory_percent?: number;
  status?: string;
  username?: string;
}

interface DetailData {
  pid?: number;
  name?: string;
  exe?: string;
  cmdline?: string[];
  status?: string;
  username?: string;
  cpu_percent?: number;
  memory_percent?: number;
  num_threads?: number;
  num_handles?: number;
  create_time?: number;
  ppid?: number;
  parent?: number;
  children?: number[];
  connections?: Array<{
    fd?: number;
    family?: string;
    type?: string;
    laddr?: { ip?: string; port?: number };
    raddr?: { ip?: string; port?: number } | null;
    status?: string;
  }>;
}

const SORT_OPTIONS = [
  { value: "cpu", label: "CPU %" },
  { value: "memory", label: "Memory" },
  { value: "name", label: "Name" },
  { value: "pid", label: "PID" },
];

type KillPreset = { label: string; targets: string[]; color: string };
const KILL_PRESETS: KillPreset[] = [
  { label: "Kill Python", targets: ["python.exe", "python3.exe"], color: "bg-yellow-600 hover:bg-yellow-700" },
  { label: "Kill Node", targets: ["node.exe"], color: "bg-green-700 hover:bg-green-800" },
  { label: "Kill Consoles", targets: ["conhost.exe", "cmd.exe", "powershell.exe", "pwsh.exe", "WindowsTerminal.exe"], color: "bg-blue-700 hover:bg-blue-800" },
  { label: "Kill Browsers", targets: ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"], color: "bg-orange-600 hover:bg-orange-700" },
  { label: "Kill VS Code", targets: ["Code.exe"], color: "bg-indigo-600 hover:bg-indigo-700" },
];

export function Processes() {
  const [processes, setProcesses] = useState<ProcessRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [sortBy, setSortBy] = useState("cpu");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;
  const [detailPid, setDetailPid] = useState<number | null>(null);
  const [detail, setDetail] = useState<DetailData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [killing, setKilling] = useState<string | null>(null);
  const [killResult, setKillResult] = useState<string | null>(null);

  const fetchProcesses = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ sort_by: sortBy, page: String(page), page_size: String(pageSize) });
      const res = await fetch(`/api/processes?${qs}`);
      if (res.ok) {
        const data = await res.json();
        setProcesses(Array.isArray(data?.processes) ? data.processes : []);
        setTotal(data?.total ?? 0);
      } else {
        setProcesses([]);
        setTotal(0);
      }
    } catch {
      setProcesses([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [sortBy, page]);

  useEffect(() => {
    fetchProcesses();
  }, [fetchProcesses]);

  const handleSortChange = (value: string) => {
    setSortBy(value);
    setPage(1);
  };

  const openDetail = useCallback(async (pid: number) => {
    setDetailPid(pid);
    setDetailLoading(true);
    setDetail(null);
    try {
      const res = await fetch(`/api/processes/${pid}`);
      if (res.ok) {
        const data = await res.json();
        setDetail((data?.process ?? data) as DetailData);
      }
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const closeDetail = useCallback(() => {
    setDetailPid(null);
    setDetail(null);
  }, []);

  const killByName = useCallback(async (label: string, targets: string[]) => {
    setKilling(label);
    setKillResult(null);
    const killed: number[] = [];
    const errors: string[] = [];
    for (const p of processes) {
      if (targets.some((t) => p.name.toLowerCase() === t.toLowerCase())) {
        try {
          const res = await fetch("/api/tools/call", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: "system_admin", arguments: { operation: "kill_process", pid: p.pid, force: false } }),
          });
          const data = await res.json();
          if (data.status === "success") killed.push(p.pid);
          else errors.push(`${p.pid}: ${data.message ?? "failed"}`);
        } catch {
          errors.push(`${p.pid}: request failed`);
        }
      }
    }
    setKillResult(`Killed ${killed.length} process(es)${errors.length ? `, ${errors.length} error(s)` : ""}`);
    setKilling(null);
    fetchProcesses();
  }, [processes, fetchProcesses]);

  const filtered = processes.filter(
    (p) =>
      !filter ||
      p.name.toLowerCase().includes(filter.toLowerCase()) ||
      String(p.pid).includes(filter),
  );

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Processes
          </h1>
          <p className="text-slate-400 text-sm">
            Running processes and resource usage
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label htmlFor="sort-by" className="text-xs text-slate-400">Sort by</label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchProcesses}
            disabled={loading}
            className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <div className="flex gap-1">
            <button
              type="button"
              title="Export CSV"
              onClick={() => download(`processes-${Date.now()}.csv`, toCsv(processes as unknown as Record<string, unknown>[]))}
              className="p-1.5 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <Card className="bg-slate-900/50 border-slate-800/60 backdrop-blur-xl">
        <CardHeader className="py-3">
          <div className="flex items-center gap-2">
            <Skull className="w-4 h-4 text-red-400" />
            <CardTitle className="text-white text-sm">Quick Kill</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pb-3 pt-0">
          <div className="flex flex-wrap gap-2">
            {KILL_PRESETS.map((p) => (
              <Button
                key={p.label}
                size="sm"
                disabled={killing === p.label}
                onClick={() => killByName(p.label, p.targets)}
                className={`${p.color} text-white text-xs border-0`}
              >
                {killing === p.label ? "Killing..." : p.label}
              </Button>
            ))}
            {killResult && (
              <span className="text-xs text-slate-400 self-center ml-2">
                {killResult}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-white">Process list</CardTitle>
              {!loading && (
                <span className="text-xs text-slate-500 ml-2">
                  ({total} total)
                </span>
              )}
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Filter by name or PID..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="pl-9 bg-slate-950 border-slate-800 text-slate-100"
              />
            </div>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Click a row to view process detail — connections, threads, handles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-slate-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 text-left text-slate-400">
                  <th className="px-4 py-3 font-medium">PID</th>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium text-right">CPU %</th>
                  <th className="px-4 py-3 font-medium text-right">Memory</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">User</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-8 text-center text-slate-500"
                    >
                      {loading ? "Loading..." : "No processes returned."}
                    </td>
                  </tr>
                )}
                {filtered.map((p) => (
                  <tr
                    key={p.pid}
                    onClick={() => openDetail(p.pid)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        openDetail(p.pid);
                      }
                    }}
                    tabIndex={0}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 text-slate-300 cursor-pointer"
                  >
                    <td className="px-4 py-2 font-mono text-slate-400">
                      {p.pid}
                    </td>
                    <td
                      className="px-4 py-2 truncate max-w-[200px]"
                      title={p.name}
                    >
                      {p.name}
                    </td>
                    <td className="px-4 py-2 text-right font-mono">
                      {p.cpu_percent != null
                        ? `${p.cpu_percent.toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="px-4 py-2 text-right font-mono">
                      {p.memory_mb != null
                        ? `${p.memory_mb.toFixed(0)} MB`
                        : "—"}
                    </td>
                    <td className="px-4 py-2 text-slate-400">
                      {p.status ?? "—"}
                    </td>
                    <td className="px-4 py-2 text-slate-500 text-xs truncate max-w-[120px]">
                      {p.username ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4">
            <p className="text-xs text-slate-500">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="border-slate-800 text-slate-400"
              >
                Prev
              </Button>
              <span className="flex items-center text-xs text-slate-500 px-2">
                {page} / {totalPages || 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="border-slate-800 text-slate-400"
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {detailPid !== null && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Process detail"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={closeDetail}
          onKeyDown={(e) => {
            if (e.key === "Escape") closeDetail();
          }}
        >
          <Card
            className="bg-slate-900 border-slate-700 w-full max-w-2xl max-h-[85vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
          >
            <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800">
              <CardTitle className="text-white">
                {detail?.name ?? `Process ${detailPid}`}
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={closeDetail}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </Button>
            </CardHeader>
            <CardContent className="p-4 overflow-y-auto max-h-[70vh]">
              {detailLoading ? (
                <p className="text-slate-500">Loading...</p>
              ) : detail ? (
                <div className="space-y-4 text-sm">
                  <Section title="Overview" cols={2}>
                    <Field label="PID" value={detail.pid} />
                    <Field label="Name" value={detail.name} />
                    <Field label="Status" value={detail.status} />
                    <Field label="User" value={detail.username} />
                    <Field label="PPID" value={detail.ppid} />
                    <Field label="Parent" value={detail.parent} />
                    <Field label="Threads" value={detail.num_threads} />
                    <Field label="Handles" value={detail.num_handles} />
                    <Field
                      label="CPU"
                      value={
                        detail.cpu_percent != null
                          ? `${detail.cpu_percent.toFixed(1)}%`
                          : null
                      }
                    />
                    <Field
                      label="Memory"
                      value={
                        detail.memory_percent != null
                          ? `${detail.memory_percent.toFixed(1)}%`
                          : null
                      }
                    />
                    <Field
                      label="Started"
                      value={
                        detail.create_time
                          ? new Date(
                              detail.create_time * 1000,
                            ).toLocaleString()
                          : null
                      }
                    />
                  </Section>

                  {detail.exe && (
                    <Section title="Executable">
                      <div className="text-slate-300 break-all font-mono text-xs">
                        {detail.exe}
                      </div>
                    </Section>
                  )}

                  {detail.cmdline && detail.cmdline.length > 0 && (
                    <Section title="Command Line">
                      <div className="text-slate-300 break-all font-mono text-xs max-h-24 overflow-y-auto">
                        {detail.cmdline.join(" ")}
                      </div>
                    </Section>
                  )}

                  {detail.children && detail.children.length > 0 && (
                    <Section title={`Children (${detail.children.length})`}>
                      <div className="flex flex-wrap gap-1">
                        {detail.children.map((c) => (
                          <span
                            key={c}
                            className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-300 font-mono"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    </Section>
                  )}

                  {detail.connections && detail.connections.length > 0 && (
                    <Section
                      title={`Network Connections (${detail.connections.length})`}
                    >
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {detail.connections.map((c) => (
                          <div
                            key={`${c.laddr?.ip}:${c.laddr?.port}->${c.raddr?.ip}:${c.raddr?.port}-${c.status}`}
                            className="text-xs font-mono text-slate-400 bg-slate-950/50 rounded p-1"
                          >
                            {c.family === "AddressFamily.AF_INET"
                              ? "IPv4"
                              : c.family}{" "}
                            {c.type === "SocketKind.SOCK_STREAM"
                              ? "TCP"
                              : c.type}{" "}
                            {c.laddr?.ip}:{c.laddr?.port}
                            {c.raddr
                              ? ` → ${c.raddr.ip}:${c.raddr.port}`
                              : ""}{" "}
                            <span className="text-slate-500">
                              [{c.status}]
                            </span>
                          </div>
                        ))}
                      </div>
                    </Section>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function Section({
  title,
  children,
  cols,
}: {
  title: string;
  children: React.ReactNode;
  cols?: number;
}) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
        {title}
      </h3>
      <div
        className={
          cols
            ? `grid grid-cols-${cols} gap-x-4 gap-y-1`
            : "space-y-1"
        }
      >
        {children}
      </div>
    </div>
  );
}

function Field({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  if (value == null) return null;
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-200 font-mono text-right truncate max-w-[200px]">
        {String(value)}
      </span>
    </div>
  );
}
