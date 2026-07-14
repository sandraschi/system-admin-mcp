import {
  Activity,
  Clock,
  Cpu,
  Database,
  HardDrive,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function Status() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/status");
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {
      // ignore fetch errors
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 5000);
    return () => clearInterval(timer);
  }, [fetchStatus]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
  };

  const formatUptime = (seconds: number) => {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${d}d ${h}h ${m}m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            System Status
          </h1>
          <p className="text-slate-400 text-sm">
            Real-time system health and performance
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchStatus}
          disabled={loading}
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      {!stats && loading && (
        <p className="text-slate-400">Loading system status...</p>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <Cpu className="w-5 h-5 text-cyan-500" />
              <CardTitle className="text-white text-lg">CPU</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">
                {stats.system?.cpu_usage_percent?.toFixed(1) ?? "?"}%
              </p>
              <CardDescription>Usage</CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <Database className="w-5 h-5 text-purple-500" />
              <CardTitle className="text-white text-lg">Memory</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">
                {stats.system?.memory?.percent?.toFixed(1) ?? "?"}%
              </p>
              <CardDescription>
                {formatBytes(stats.system?.memory?.used ?? 0)} /{" "}
                {formatBytes(stats.system?.memory?.total ?? 0)}
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <HardDrive className="w-5 h-5 text-emerald-500" />
              <CardTitle className="text-white text-lg">Disk (C:)</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">
                {stats.system?.disk?.percent?.toFixed(1) ?? "?"}%
              </p>
              <CardDescription>
                {formatBytes(stats.system?.disk?.used ?? 0)} /{" "}
                {formatBytes(stats.system?.disk?.total ?? 0)}
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <ShieldCheck className="w-5 h-5 text-green-500" />
              <CardTitle className="text-white text-lg">Service</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">
                {stats.status ?? "?"}
              </p>
              <CardDescription>v{stats.version ?? "?"}</CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <Activity className="w-5 h-5 text-yellow-500" />
              <CardTitle className="text-white text-lg">System</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold text-white">
                {stats.system?.cpu_count ?? "?"} cores
              </p>
              <CardDescription>CPU count</CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
            <CardHeader className="flex flex-row items-center gap-2 pb-2">
              <Clock className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-white text-lg">Uptime</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold text-white">
                {formatUptime(stats.uptime ?? 0)}
              </p>
              <CardDescription>Service running</CardDescription>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
