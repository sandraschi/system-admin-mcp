import { useCallback, useEffect, useRef, useState } from "react";
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

function levelOf(line: string): string {
  const m = line.match(/\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b/);
  return m ? m[1] : "";
}

function lineKey(line: string, index: number): string {
  let hash = 0;
  for (let i = 0; i < line.length; i++) {
    hash = (hash * 31 + line.charCodeAt(i)) | 0;
  }
  return `${hash.toString(36)}-${index}`;
}

const LEVEL_STYLES: Record<string, string> = {
  ERROR: "text-red-400",
  CRITICAL: "text-red-400",
  WARNING: "text-amber-400",
  INFO: "text-blue-300",
  DEBUG: "text-slate-400",
};

export default function Logging() {
  const [lines, setLines] = useState<string[]>([]);
  const [source, setSource] = useState("");
  const [message, setMessage] = useState("");
  const [tail, setTail] = useState("200");
  const [file, setFile] = useState("");
  const [search, setSearch] = useState("");
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const lineCountRef = useRef(0);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("tail", tail || "200");
      if (file.trim()) params.set("file", file.trim());
      const r = await fetch(`${API_BASE}/api/logs?${params}`);
      const d = await r.json();
      setLines(Array.isArray(d.lines) ? d.lines : []);
      setSource(d.source ?? "");
      setMessage(d.message ?? "");
    } catch (e) {
      setError(String(e));
      setLines([]);
    } finally {
      setLoading(false);
    }
  }, [tail, file]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    if (!live) return;
    const iv = setInterval(fetchLogs, 3000);
    return () => clearInterval(iv);
  }, [live, fetchLogs]);

  // Scroll to bottom when new lines arrive (no dep array: cheap ref check)
  useEffect(() => {
    if (lines.length !== lineCountRef.current) {
      lineCountRef.current = lines.length;
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  });

  const q = search.trim().toLowerCase();
  const shown = q ? lines.filter((l) => l.toLowerCase().includes(q)) : lines;

  return (
    <div className="space-y-6" data-testid="logs-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Logs</h1>
        <p className="text-slate-400 text-sm">
          Backend log files{source ? ` - ${source}` : ""}
        </p>
      </div>

      {message && (
        <Card className="bg-amber-950/30 border-amber-900">
          <CardContent className="pt-4 text-sm text-amber-300">
            {message}
          </CardContent>
        </Card>
      )}
      {error && (
        <Card className="bg-red-950/30 border-red-900">
          <CardContent className="pt-4 text-sm text-red-300">
            {error}
          </CardContent>
        </Card>
      )}

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-white">Viewer</CardTitle>
          <CardDescription className="text-slate-400 text-sm">
            Raw backend log tail with search and level highlight
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Input
              value={file}
              onChange={(e) => setFile(e.target.value)}
              placeholder="Log file name (blank = newest)"
              className="bg-slate-950 border-slate-800 text-slate-100 w-64"
            />
            <Input
              value={tail}
              onChange={(e) => setTail(e.target.value)}
              placeholder="Tail lines (200)"
              className="bg-slate-950 border-slate-800 text-slate-100 w-36"
            />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter text..."
              className="bg-slate-950 border-slate-800 text-slate-100 flex-1 min-w-40"
            />
            <Button
              onClick={fetchLogs}
              disabled={loading}
              data-testid="logs-refresh"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {loading ? "..." : "Load"}
            </Button>
            <Button
              variant="outline"
              size="default"
              onClick={() => setLive(!live)}
              data-testid="logs-live"
              className={`border-slate-800 ${live ? "bg-emerald-600 text-white hover:bg-emerald-700" : "bg-slate-900/50 text-slate-300 hover:bg-slate-800"}`}
            >
              {live ? "LIVE" : "Watch"}
            </Button>
          </div>

          <div className="rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-sm leading-relaxed max-h-[60vh] overflow-auto">
            {shown.length === 0 && !loading && (
              <div className="text-slate-400 text-center py-12">
                No log lines{q ? ` matching "${search}"` : ""}.
              </div>
            )}
            {shown.map((line, i) => {
              const lvl = levelOf(line);
              return (
                <div
                  key={lineKey(line, i)}
                  className="py-0.5 hover:bg-slate-900/60 rounded px-1 break-all text-slate-200"
                >
                  {lvl && (
                    <span className={`font-bold mr-2 ${LEVEL_STYLES[lvl]}`}>
                      {lvl}
                    </span>
                  )}
                  {line}
                </div>
              );
            })}
            <div ref={endRef} />
          </div>
          <p className="text-sm text-slate-400">
            {shown.length} of {lines.length} lines
            {q ? ` matching filter` : ""}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
