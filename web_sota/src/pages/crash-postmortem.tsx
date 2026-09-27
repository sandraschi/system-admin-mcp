import { AlertTriangle, FileText, RefreshCw, Terminal } from "lucide-react";
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

export function CrashPostmortem() {
  const [dumps, setDumps] = useState<unknown>(null);
  const [loadingDumps, setLoadingDumps] = useState(false);
  const [daysBack, setDaysBack] = useState("7");
  const [history, setHistory] = useState<unknown>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [dumpPath, setDumpPath] = useState("");
  const [triage, setTriage] = useState<unknown>(null);
  const [loadingTriage, setLoadingTriage] = useState(false);
  const [timeoutSecs, setTimeoutSecs] = useState("120");
  const [windbg, setWindbg] = useState<unknown>(null);
  const [loadingWindbg, setLoadingWindbg] = useState(false);

  const fetchDumps = useCallback(async () => {
    setLoadingDumps(true);
    try {
      const res = await fetch(`${API_BASE}/api/crash/dumps`);
      setDumps(await res.json());
    } catch (e) {
      setDumps({ status: "error", error: String(e) });
    } finally {
      setLoadingDumps(false);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    setHistory(null);
    try {
      const days = Number.parseInt(daysBack, 10) || 7;
      const res = await fetch(
        `${API_BASE}/api/crash/bugcheck-history?days_back=${days}&max_results=50`,
      );
      setHistory(await res.json());
    } catch (e) {
      setHistory({ status: "error", error: String(e) });
    } finally {
      setLoadingHistory(false);
    }
  }, [daysBack]);

  const runTriage = useCallback(async () => {
    setLoadingTriage(true);
    setTriage(null);
    try {
      const res = await fetch(`${API_BASE}/api/crash/analyze-minidump`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dump_path: dumpPath.trim() || null }),
      });
      setTriage(await res.json());
    } catch (e) {
      setTriage({ status: "error", error: String(e) });
    } finally {
      setLoadingTriage(false);
    }
  }, [dumpPath]);

  const runWindbg = useCallback(async () => {
    setLoadingWindbg(true);
    setWindbg(null);
    try {
      const res = await fetch(`${API_BASE}/api/crash/windbg`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dump_path: dumpPath.trim() || null,
          timeout_seconds: Number.parseInt(timeoutSecs, 10) || 120,
        }),
      });
      setWindbg(await res.json());
    } catch (e) {
      setWindbg({ status: "error", error: String(e) });
    } finally {
      setLoadingWindbg(false);
    }
  }, [dumpPath, timeoutSecs]);

  useEffect(() => {
    fetchDumps();
  }, [fetchDumps]);

  return (
    <div className="space-y-6" data-testid="crash-postmortem-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Crash postmortem
          </h1>
          <p className="text-slate-400 text-sm">
            Dump inventory, bugcheck correlation, minidump triage, WinDbg
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchDumps}
          disabled={loadingDumps}
          data-testid="crash-refresh-dumps"
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${loadingDumps ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <CardTitle className="text-white">Dump inventory</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            MEMORY.DMP, Minidump, LiveKernelReports, WER, dump config
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResultBlock data={dumps} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-500" />
            <CardTitle className="text-white">Bugcheck history</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            IDs 41 / 1001 / 6008 / 1074 - needs elevation for event logs
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={daysBack}
              onChange={(e) => setDaysBack(e.target.value)}
              placeholder="Days back (7)"
              className="bg-slate-950 border-slate-800 text-slate-100 w-40"
            />
            <Button
              onClick={fetchHistory}
              disabled={loadingHistory}
              data-testid="crash-load-history"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loadingHistory ? "..." : "Load"}
            </Button>
          </div>
          <ResultBlock data={history} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-500" />
            <CardTitle className="text-white">Minidump triage</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            SDK-free parse - blank path uses the newest minidump
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={dumpPath}
              onChange={(e) => setDumpPath(e.target.value)}
              placeholder="C:\Windows\Minidump\....dmp (blank = newest)"
              className="bg-slate-950 border-slate-800 text-slate-100 flex-1"
            />
            <Button
              onClick={runTriage}
              disabled={loadingTriage}
              data-testid="crash-run-triage"
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              {loadingTriage ? "..." : "Analyze"}
            </Button>
          </div>
          <ResultBlock data={triage} />
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-purple-500" />
            <CardTitle className="text-white">WinDbg !analyze</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Needs Debugging Tools (cdb.exe) - full dump capable
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              value={timeoutSecs}
              onChange={(e) => setTimeoutSecs(e.target.value)}
              placeholder="Timeout s (120)"
              className="bg-slate-950 border-slate-800 text-slate-100 w-40"
            />
            <Button
              onClick={runWindbg}
              disabled={loadingWindbg}
              data-testid="crash-run-windbg"
              className="bg-purple-600 hover:bg-purple-700 text-white"
            >
              {loadingWindbg ? "..." : "Run !analyze"}
            </Button>
          </div>
          <ResultBlock data={windbg} />
        </CardContent>
      </Card>
    </div>
  );
}
