import { FileText, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function Logs() {
  const [lines, setLines] = useState<string[]>([]);
  const [source, setSource] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [tail, setTail] = useState(200);
  const bottomRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/logs?tail=${tail}`);
      const data = await res.json();
      setLines(Array.isArray(data?.lines) ? data.lines : []);
      setSource(data?.source ?? "");
      setMessage(data?.message ?? "");
    } catch {
      setLines([]);
      setMessage("Request failed");
    } finally {
      setLoading(false);
    }
  }, [tail]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Logs</h1>
          <p className="text-slate-400 text-sm">
            SystemAdminMCP bridge and service logs
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="log-tail" className="text-slate-400 text-sm">
            Tail
          </label>
          <select
            id="log-tail"
            value={tail}
            onChange={(e) => setTail(Number(e.target.value))}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm"
          >
            <option value={50}>50</option>
            <option value={200}>200</option>
            <option value={500}>500</option>
            <option value={1000}>1000</option>
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchLogs}
            disabled={loading}
            className="border-slate-800 bg-slate-900/50 text-slate-300"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-500" />
            <CardTitle className="text-white">Log output</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            {source || "—"} {message ? `(${message})` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[60vh] overflow-y-auto rounded-md border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap">
            {lines.length === 0 && !loading && (
              <span className="text-slate-500">
                No lines (empty or log dir missing)
              </span>
            )}
            {lines.map((line) => (
              <div
                key={line.slice(0, 40)}
                className="leading-relaxed"
              >
                {line}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
