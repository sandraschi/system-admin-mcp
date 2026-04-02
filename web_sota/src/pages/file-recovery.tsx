import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Archive, Loader2 } from "lucide-react";

export function FileRecovery() {
    const [originalPath, setOriginalPath] = useState("");
    const [outputDir, setOutputDir] = useState("");
    const [result, setResult] = useState<Record<string, unknown> | null>(null);
    const [loading, setLoading] = useState(false);

    const runRecovery = async () => {
        if (!originalPath.trim() || !outputDir.trim()) return;
        setLoading(true);
        setResult(null);
        try {
            const res = await fetch("/api/recover_file", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    original_path: originalPath.trim(),
                    output_dir: outputDir.trim(),
                }),
            });
            const data = await res.json();
            setResult(data.status === "success" ? (data.result as Record<string, unknown>) : { error: data.message });
        } catch (e) {
            setResult({ error: String(e) });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white">File recovery</h1>
                <p className="text-slate-400 text-sm">Recover deleted file from NTFS (recover_file). Admin required.</p>
            </div>

            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                <CardHeader>
                    <div className="flex items-center gap-2">
                        <Archive className="w-5 h-5 text-amber-500" />
                        <CardTitle className="text-white">Recover file</CardTitle>
                    </div>
                    <CardDescription className="text-slate-400 text-xs">Original path of deleted file and directory to save recovered file</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-sm text-slate-400">Original path (deleted file)</label>
                        <Input
                            value={originalPath}
                            onChange={(e) => setOriginalPath(e.target.value)}
                            placeholder="D:\\path\\to\\deleted.txt"
                            className="bg-slate-950 border-slate-800 text-slate-100 font-mono"
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm text-slate-400">Output directory</label>
                        <Input
                            value={outputDir}
                            onChange={(e) => setOutputDir(e.target.value)}
                            placeholder="C:\\Recovered"
                            className="bg-slate-950 border-slate-800 text-slate-100 font-mono"
                        />
                    </div>
                    <Button
                        onClick={runRecovery}
                        disabled={loading || !originalPath.trim() || !outputDir.trim()}
                        className="bg-amber-600 hover:bg-amber-700"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        Run recovery
                    </Button>
                    {result !== null && (
                        <pre className="p-4 rounded-md bg-slate-950 border border-slate-800 text-xs text-slate-300 overflow-x-auto mt-4">
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
