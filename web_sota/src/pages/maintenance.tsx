import { RefreshCw, Wrench } from "lucide-react";
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
import API_BASE from "@/lib/api";

function ResultBlock({ data }: { data: unknown }) {
  if (data === null || data === undefined) return null;
  return (
    <pre className="text-xs text-slate-300 bg-slate-950 p-3 rounded border border-slate-800 whitespace-pre-wrap max-h-96 overflow-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function useSection(fetcher: () => Promise<unknown>) {
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const run = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetcher());
    } catch (e) {
      setData({ status: "error", error: String(e) });
    } finally {
      setLoading(false);
    }
  }, [fetcher]);
  return { data, loading, run };
}

const get = (path: string) => () =>
  fetch(`${API_BASE}${path}`).then((r) => r.json());

export function Maintenance() {
  const [firmwareData, setFirmwareData] = useState<unknown>(null);
  const [updatesData, setUpdatesData] = useState<unknown>(null);
  const [pathData, setPathData] = useState<unknown>(null);

  const loadAuto = useCallback(async () => {
    const load = async (url: string, set: (d: unknown) => void) => {
      try {
        const res = await fetch(`${API_BASE}${url}`);
        set(await res.json());
      } catch (e) {
        set({ status: "error", error: String(e) });
      }
    };
    await Promise.all([
      load("/api/firmware-posture", setFirmwareData),
      load("/api/update-status", setUpdatesData),
      load("/api/path-dross", setPathData),
    ]);
  }, []);

  useEffect(() => {
    loadAuto();
  }, [loadAuto]);

  const [driverFilter, setDriverFilter] = useState("");
  const [driversData, setDriversData] = useState<unknown>(null);
  const [driversLoading, setDriversLoading] = useState(false);
  const shadows = useSection(get("/api/shadow-copies"));
  const reliability = useSection(get("/api/reliability-history?days_back=7"));
  const winget = useSection(get("/api/winget-outdated?max_results=30"));

  const runDrivers = useCallback(async () => {
    setDriversLoading(true);
    try {
      const q = driverFilter.trim()
        ? `?class_filter=${encodeURIComponent(driverFilter.trim())}&max_results=100`
        : "?max_results=100";
      const res = await fetch(`${API_BASE}/api/drivers${q}`);
      setDriversData(await res.json());
    } catch (e) {
      setDriversData({ status: "error", error: String(e) });
    } finally {
      setDriversLoading(false);
    }
  }, [driverFilter]);

  return (
    <div className="space-y-6" data-testid="maintenance-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Maintenance
          </h1>
          <p className="text-slate-400 text-sm">
            Firmware, updates, drivers, backups, PATH
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={loadAuto}
          data-testid="maintenance-refresh"
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-amber-500" />
            <CardTitle className="text-white">Firmware posture</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            SVM, TPM, Secure Boot, VBS, BIOS
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={firmwareData} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-blue-500" />
            <CardTitle className="text-white">Update status</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Last patch, pending reboot, uptime
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={updatesData} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-emerald-500" />
            <CardTitle className="text-white">Drivers</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Signed driver inventory, optional class filter
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={driverFilter}
              onChange={(e) => setDriverFilter(e.target.value)}
              placeholder="Class filter, e.g. Display (blank = all)"
              className="bg-slate-950 border-slate-800 text-slate-100 flex-1"
            />
            <Button
              onClick={runDrivers}
              disabled={driversLoading}
              data-testid="maintenance-load-drivers"
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              {driversLoading ? "..." : "Load"}
            </Button>
          </div>
          <ResultBlock data={driversData} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-purple-500" />
            <CardTitle className="text-white">Winget upgrades</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Slow - takes up to a minute
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            onClick={winget.run}
            disabled={winget.loading}
            data-testid="maintenance-load-winget"
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {winget.loading ? "Scanning..." : "Scan upgrades"}
          </Button>
          <ResultBlock data={winget.data} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-cyan-500" />
            <CardTitle className="text-white">Shadow copies</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            VSS shadows - needs elevation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            onClick={shadows.run}
            disabled={shadows.loading}
            data-testid="maintenance-load-shadows"
            className="bg-cyan-600 hover:bg-cyan-700 text-white"
          >
            {shadows.loading ? "..." : "Load"}
          </Button>
          <ResultBlock data={shadows.data} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-rose-500" />
            <CardTitle className="text-white">Reliability history</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Last 7 days of Reliability Monitor records
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button
            onClick={reliability.run}
            disabled={reliability.loading}
            data-testid="maintenance-load-reliability"
            className="bg-rose-600 hover:bg-rose-700 text-white"
          >
            {reliability.loading ? "..." : "Load"}
          </Button>
          <ResultBlock data={reliability.data} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-slate-400" />
            <CardTitle className="text-white">PATH audit</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Missing dirs and duplicates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={pathData} />
        </CardContent>
      </Card>
    </div>
  );
}
