import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RefreshCw, Cpu, Search, X } from "lucide-react";

interface ProcessRow {
    pid: number;
    name: string;
    cpu_percent?: number;
    memory_mb?: number;
    status?: string;
}

export function Processes() {
    const [processes, setProcesses] = useState<ProcessRow[]>([]);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState("");
    const [detailPid, setDetailPid] = useState<number | null>(null);
    const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
    const [detailLoading, setDetailLoading] = useState(false);

    const fetchProcesses = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/processes");
            if (res.ok) {
                const data = await res.json();
                setProcesses(Array.isArray(data?.processes) ? data.processes : data ?? []);
            } else {
                setProcesses([]);
            }
        } catch {
            setProcesses([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchProcesses();
    }, []);

    const filtered = processes.filter(
        (p) =>
            !filter ||
            p.name.toLowerCase().includes(filter.toLowerCase()) ||
            String(p.pid).includes(filter)
    );

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Processes</h1>
                    <p className="text-slate-400 text-sm">Running processes and resource usage</p>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchProcesses}
                    disabled={loading}
                    className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
                >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                        <div className="flex items-center gap-2">
                            <Cpu className="w-5 h-5 text-blue-500" />
                            <CardTitle className="text-white">Process list</CardTitle>
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
                        Click a row to view process detail (analyze_process)
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
                                </tr>
                            </thead>
                            <tbody>
                                {filtered.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                                            {loading ? "Loading..." : "No processes returned. Implement GET /api/processes on the backend."}
                                        </td>
                                    </tr>
                                )}
                                {filtered.slice(0, 100).map((p) => (
                                    <tr
                                        key={p.pid}
                                        onClick={() => openDetail(p.pid)}
                                        className="border-b border-slate-800/50 hover:bg-slate-800/30 text-slate-300 cursor-pointer"
                                    >
                                        <td className="px-4 py-2 font-mono text-slate-400">{p.pid}</td>
                                        <td className="px-4 py-2 truncate max-w-[200px]" title={p.name}>
                                            {p.name}
                                        </td>
                                        <td className="px-4 py-2 text-right">{p.cpu_percent != null ? `${p.cpu_percent.toFixed(1)}%` : "—"}</td>
                                        <td className="px-4 py-2 text-right">{p.memory_mb != null ? `${p.memory_mb.toFixed(0)} MB` : "—"}</td>
                                        <td className="px-4 py-2 text-slate-400">{p.status ?? "—"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {filtered.length > 100 && (
                        <p className="text-xs text-slate-500 mt-2">Showing first 100 of {filtered.length}</p>
                    )}
                </CardContent>
            </Card>

            {detailPid !== null && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={() => setDetailPid(null)}>
                    <Card
                        className="bg-slate-900 border-slate-700 w-full max-w-2xl max-h-[85vh] overflow-hidden"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <CardHeader className="flex flex-row items-center justify-between border-b border-slate-800">
                            <CardTitle className="text-white">Process {detailPid}</CardTitle>
                            <Button variant="ghost" size="icon" onClick={() => setDetailPid(null)} className="text-slate-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-4 overflow-y-auto max-h-[70vh]">
                            {detailLoading ? (
                                <p className="text-slate-500">Loading...</p>
                            ) : detail ? (
                                <pre className="text-xs text-slate-300 whitespace-pre-wrap break-words">
                                    {JSON.stringify(detail, null, 2)}
                                </pre>
                            ) : null}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
