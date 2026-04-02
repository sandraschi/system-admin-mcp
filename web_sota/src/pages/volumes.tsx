import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RefreshCw, HardDrive, FolderOpen } from "lucide-react";

const DRIVE_TYPE_NAMES: Record<number, string> = {
    0: "Unknown",
    1: "No root",
    2: "Removable",
    3: "Fixed",
    4: "Remote",
    5: "CD-ROM",
    6: "RAM disk",
};

export function Volumes() {
    const [volumes, setVolumes] = useState<{ drive: string; type: number }[]>([]);
    const [path, setPath] = useState("C:\\");
    const [usage, setUsage] = useState<Record<string, unknown> | null>(null);
    const [loadingVolumes, setLoadingVolumes] = useState(false);
    const [loadingUsage, setLoadingUsage] = useState(false);

    const fetchVolumes = async () => {
        setLoadingVolumes(true);
        try {
            const res = await fetch("/api/volumes");
            const data = await res.json();
            setVolumes(Array.isArray(data?.volumes) ? data.volumes : []);
        } catch {
            setVolumes([]);
        } finally {
            setLoadingVolumes(false);
        }
    };

    const fetchDiskUsage = async () => {
        if (!path.trim()) return;
        setLoadingUsage(true);
        setUsage(null);
        try {
            const res = await fetch("/api/disk_usage", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path: path.trim() }),
            });
            const data = await res.json();
            setUsage(data.status === "success" ? (data.result as Record<string, unknown>) : { error: data.message });
        } catch (e) {
            setUsage({ error: String(e) });
        } finally {
            setLoadingUsage(false);
        }
    };

    useEffect(() => {
        fetchVolumes();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Volumes</h1>
                    <p className="text-slate-400 text-sm">Drives and disk usage (list_volumes, get_disk_usage)</p>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchVolumes}
                    disabled={loadingVolumes}
                    className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800"
                >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loadingVolumes ? "animate-spin" : ""}`} />
                    Refresh
                </Button>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <HardDrive className="w-5 h-5 text-blue-500" />
                        <CardTitle className="text-white">Drives</CardTitle>
                    </div>
                    <CardDescription className="text-slate-400 text-xs">list_volumes</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-wrap gap-3">
                        {loadingVolumes ? (
                            <span className="text-slate-500">Loading...</span>
                        ) : volumes.length === 0 ? (
                            <span className="text-slate-500">No volumes (or API error)</span>
                        ) : (
                            volumes.map((v) => (
                                <div
                                    key={v.drive}
                                    className="px-4 py-2 rounded-lg bg-slate-950 border border-slate-800 font-mono text-slate-300"
                                >
                                    {v.drive} — {DRIVE_TYPE_NAMES[v.type] ?? `Type ${v.type}`}
                                </div>
                            ))
                        )}
                    </div>
                </CardContent>
            </Card>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <FolderOpen className="w-5 h-5 text-emerald-500" />
                        <CardTitle className="text-white">Disk usage by path</CardTitle>
                    </div>
                    <CardDescription className="text-slate-400 text-xs">get_disk_usage(path)</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-2">
                        <Input
                            value={path}
                            onChange={(e) => setPath(e.target.value)}
                            placeholder="C:\\ or /"
                            className="bg-slate-950 border-slate-800 text-slate-100 font-mono"
                        />
                        <Button
                            onClick={fetchDiskUsage}
                            disabled={loadingUsage || !path.trim()}
                            className="bg-slate-800 hover:bg-slate-700"
                        >
                            {loadingUsage ? "..." : "Get usage"}
                        </Button>
                    </div>
                    {usage !== null && (
                        <pre className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-300 overflow-x-auto">
                            {JSON.stringify(usage, null, 2)}
                        </pre>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
