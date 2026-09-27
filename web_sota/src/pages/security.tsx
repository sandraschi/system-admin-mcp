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

export function Security() {
  const [admins, setAdmins] = useState<unknown>(null);
  const [shares, setShares] = useState<unknown>(null);
  const [tasks, setTasks] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s, t] = await Promise.all([
        fetch(`${API_BASE}/api/local-admins`).then((r) => r.json()),
        fetch(`${API_BASE}/api/smb-shares`).then((r) => r.json()),
        fetch(`${API_BASE}/api/scheduled-tasks?max_results=50`).then((r) =>
          r.json(),
        ),
      ]);
      setAdmins(a);
      setShares(s);
      setTasks(t);
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
            Local admins, SMB shares, scheduled tasks
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
    </div>
  );
}
