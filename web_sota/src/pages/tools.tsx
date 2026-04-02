import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Terminal, Play, Loader2, Search, Code2 } from "lucide-react";

export function Tools() {
    const [tools, setTools] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [results, setResults] = useState<Record<string, any>>({});
    const [executing, setExecuting] = useState<Record<string, boolean>>({});

    useEffect(() => {
        fetch('/api/tools')
            .then(res => res.json())
            .then(data => {
                setTools(data);
                setLoading(false);
            })
            .catch(err => console.error("Failed to fetch tools", err));
    }, []);

    const callTool = async (name: string, args: any = {}) => {
        setExecuting(prev => ({ ...prev, [name]: true }));
        try {
            const res = await fetch('/api/tools/call', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, arguments: args })
            });
            const data = await res.json();
            setResults(prev => ({ ...prev, [name]: data }));
        } catch (err) {
            setResults(prev => ({ ...prev, [name]: { status: 'error', message: String(err) } }));
        } finally {
            setExecuting(prev => ({ ...prev, [name]: false }));
        }
    };

    const filteredTools = tools.filter(t =>
        t.name.toLowerCase().includes(search.toLowerCase()) ||
        t.description.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Terminal className="w-8 h-8 text-blue-500" />
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">MCP Tools</h1>
                        <p className="text-slate-400 text-sm">Dynamic service discovery and tool execution</p>
                    </div>
                </div>
                <div className="relative w-64">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
                    <Input
                        placeholder="Search tools..."
                        className="pl-9 bg-slate-900/50 border-slate-800 text-slate-300"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
                </div>
            ) : (
                <div className="grid gap-6">
                    {filteredTools.map(tool => (
                        <Card key={tool.name} className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                            <CardHeader className="flex flex-row items-start justify-between">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <CardTitle className="text-white font-mono">{tool.name}</CardTitle>
                                        <Badge variant="outline" className="border-blue-500/30 text-blue-400 text-[10px]">
                                            FastMCP 2.14.3
                                        </Badge>
                                    </div>
                                    <CardDescription className="text-slate-400 italic">
                                        {tool.description || "No description provided."}
                                    </CardDescription>
                                </div>
                                <Button
                                    size="sm"
                                    onClick={() => callTool(tool.name)}
                                    disabled={executing[tool.name]}
                                    className="bg-blue-600 hover:bg-blue-700 text-white transition-all active:scale-95"
                                >
                                    {executing[tool.name] ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                                    Execute
                                </Button>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {Object.keys(tool.parameters?.properties || {}).length > 0 && (
                                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                                        <div className="text-[10px] uppercase font-bold text-slate-500 mb-2 flex items-center gap-1">
                                            <Code2 className="w-3 h-3" /> Parameters
                                        </div>
                                        <div className="grid gap-3 sm:grid-cols-2">
                                            {Object.entries(tool.parameters.properties).map(([param, details]: [string, any]) => (
                                                <div key={param} className="space-y-1.5">
                                                    <Label className="text-xs text-slate-300">{param}</Label>
                                                    <Input
                                                        disabled
                                                        placeholder={details.type}
                                                        className="h-8 bg-slate-900 border-slate-800 text-slate-500 text-xs"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {results[tool.name] && (
                                    <div className="space-y-2">
                                        <div className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1">
                                            <Terminal className="w-3 h-3" /> Last Result
                                        </div>
                                        <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 overflow-auto max-h-48 font-mono">
                                            {JSON.stringify(results[tool.name], null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
