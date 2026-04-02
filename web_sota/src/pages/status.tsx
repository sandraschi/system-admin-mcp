import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, Activity, Cpu, Database, HardDrive, ShieldCheck, Clock } from "lucide-react";

export function Status() {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchStatus = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/status');
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (err) {
            console.error("Failed to fetch system status", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const timer = setInterval(fetchStatus, 5000);
        return () => clearInterval(timer);
    }, []);

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
                    <h1 className="text-3xl font-bold tracking-tight text-white">System Status</h1>
                    <p className="text-slate-400 text-sm">Real-time health monitoring for System Admin MCP</p>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchStatus}
                    disabled={loading}
                    className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
                >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Connection</CardTitle>
                        <ShieldCheck className={`h-4 w-4 ${stats ? 'text-green-500' : 'text-slate-600'}`} />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats ? 'ONLINE' : 'OFFLINE'}</div>
                        <p className="text-xs text-slate-500 mt-1">Backend Bridge @ 10861</p>
                    </CardContent>
                </Card>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Processor</CardTitle>
                        <Cpu className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.system?.cpu_usage_percent || '0'}%</div>
                        <p className="text-xs text-slate-500 mt-1">CPU Utilization</p>
                    </CardContent>
                </Card>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Memory</CardTitle>
                        <Database className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats?.system?.memory?.percent || '0'}%</div>
                        <p className="text-xs text-slate-500 mt-1">RAM Usage</p>
                    </CardContent>
                </Card>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Uptime</CardTitle>
                        <Clock className="h-4 w-4 text-orange-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{stats ? formatUptime(stats.uptime) : '0h 0m'}</div>
                        <p className="text-xs text-slate-500 mt-1">Service Life</p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <HardDrive className="w-5 h-5 text-blue-500" />
                            <CardTitle className="text-white">Storage Overview</CardTitle>
                        </div>
                        <CardDescription className="text-slate-400 text-xs">Root partition disk space</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-slate-300">Used Space</span>
                                <span className="text-white">{stats ? formatBytes(stats.system.disk.used) : '0 GB'}</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                <div
                                    className="bg-blue-500 h-full transition-all duration-1000"
                                    style={{ width: `${stats?.system?.disk?.percent || 0}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-xs text-slate-500">
                                <span>Total: {stats ? formatBytes(stats.system.disk.total) : '0 GB'}</span>
                                <span>{stats?.system?.disk?.percent || 0}%</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                    <CardHeader>
                        <div className="flex items-center gap-2">
                            <Activity className="w-5 h-5 text-green-500" />
                            <CardTitle className="text-white">Service Health</CardTitle>
                        </div>
                        <CardDescription className="text-slate-400 text-xs">Sub-system availability</CardDescription>
                    </CardHeader>
                    <CardContent className="grid grid-cols-2 gap-4">
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-sm text-slate-300">FastAPI</span>
                        </div>
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-sm text-slate-300">PSUtil</span>
                        </div>
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                            <span className="text-sm text-slate-300">WMI Bridge</span>
                        </div>
                        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                            <span className="text-sm text-slate-300">Elevated Ops</span>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
