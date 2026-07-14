import { FolderOpen, HardDrive, RefreshCw } from "lucide-react";
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
  const [volumes, setVolumes] = useState<
    { drive: string; type: number }[]
  >([]);
  const [path, setPath] = useState("C:\\");
  const [usage, setUsage] = useState<Record<string, unknown> | null>(null);
  const [loadingVolumes, setLoadingVolumes] = useState(false);
  const [loadingUsage, setLoadingUsage] = useState(false);

  const fetchVolumes = useCallback(async () => {
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
  }, []);

  const fetchDiskUsage = useCallback(async () => {
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
      setUsage(
        data.status === "success"
          ? (data.result as Record<string, unknown>)
          : { error: data.message },
      );
    } catch (e) {
      setUsage({ error: String(e) });
    } finally {
      setLoadingUsage(false);
    }
  }, [path]);

  useEffect(() => {
    fetchVolumes();
  }, [fetchVolumes]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Volumes
          </h1>
          <p className="text-slate-400 text-sm">
            Drive listing and disk usage
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchVolumes}
          disabled={loadingVolumes}
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${loadingVolumes ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-emerald-500" />
            <CardTitle className="text-white">Volume list</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            System drives and their types
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-slate-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 text-left text-slate-400">
                  <th className="px-4 py-3 font-medium">Drive</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                </tr>
              </thead>
              <tbody>
                {volumes.length === 0 && (
                  <tr>
                    <td
                      colSpan={2}
                      className="px-4 py-8 text-center text-slate-500"
                    >
                      {loadingVolumes
                        ? "Loading..."
                        : "No volumes returned."}
                    </td>
                  </tr>
                )}
                {volumes.map((v) => (
                  <tr
                    key={v.drive}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 text-slate-300"
                  >
                    <td className="px-4 py-2 font-mono text-slate-400">
                      {v.drive}
                    </td>
                    <td className="px-4 py-2">
                      {DRIVE_TYPE_NAMES[v.type] ?? "Unknown"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-blue-500" />
            <CardTitle className="text-white">Disk usage</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Check disk usage for a path
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="bg-slate-950 border-slate-800 text-slate-100 flex-1"
            />
            <Button
              onClick={fetchDiskUsage}
              disabled={loadingUsage}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loadingUsage ? "..." : "Check"}
            </Button>
          </div>
          {usage && (
            <pre className="text-xs text-slate-300 bg-slate-950 p-3 rounded border border-slate-800 whitespace-pre-wrap">
              {JSON.stringify(usage, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
