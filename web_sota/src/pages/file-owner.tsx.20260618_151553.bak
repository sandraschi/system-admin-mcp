import { Loader2, Shield } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function FileOwner() {
  const [path, setPath] = useState("");
  const [result, setResult] = useState<{
    owner?: string;
    sid?: string;
    file?: string;
    error?: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchOwner = async () => {
    if (!path.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/file_owner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: path.trim() }),
      });
      const data = await res.json();
      if (data.status === "success" && data.result) {
        setResult(
          data.result as { owner?: string; sid?: string; file?: string },
        );
      } else {
        setResult({ error: data.message || "Failed" });
      }
    } catch (e) {
      setResult({ error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          File owner
        </h1>
        <p className="text-slate-400 text-sm">
          Get file or directory owner and SID (get_file_owner)
        </p>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-orange-500" />
            <CardTitle className="text-white">Lookup owner</CardTitle>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Requires path to existing file or folder
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="C:\\Windows or /etc"
              className="bg-slate-950 border-slate-800 text-slate-100 font-mono"
            />
            <Button
              onClick={fetchOwner}
              disabled={loading || !path.trim()}
              className="bg-slate-800 hover:bg-slate-700"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Get owner"
              )}
            </Button>
          </div>
          {result !== null && (
            <div className="p-4 rounded-md bg-slate-950 border border-slate-800 space-y-2 text-sm">
              {result.error ? (
                <p className="text-red-400">{result.error}</p>
              ) : (
                <>
                  <p className="text-slate-300">
                    <span className="text-slate-500">Owner:</span>{" "}
                    {result.owner ?? "—"}
                  </p>
                  <p className="text-slate-300 font-mono text-xs break-all">
                    <span className="text-slate-500">SID:</span>{" "}
                    {result.sid ?? "—"}
                  </p>
                  {result.file && (
                    <p className="text-slate-500 text-xs">
                      Path: {result.file}
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
