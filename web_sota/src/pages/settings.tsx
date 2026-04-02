import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings as SettingsIcon, Shield, Brain, Key, Zap, Save } from "lucide-react";

export function Settings() {
    return (
        <div className="space-y-8 max-w-4xl">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <SettingsIcon className="w-8 h-8 text-blue-500" />
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight text-white">System Settings</h1>
                        <p className="text-slate-400 text-sm italic">Core orchestration and intelligence configuration</p>
                    </div>
                </div>
                <Button className="bg-blue-600 hover:bg-blue-700 active:scale-95 transition-all">
                    <Save className="w-4 h-4 mr-2" /> Save Configuration
                </Button>
            </div>

            <div className="grid gap-8">
                <section className="space-y-4">
                    <div className="flex items-center gap-2 text-white font-semibold">
                        <Brain className="w-5 h-5 text-purple-500" />
                        Intelligence Engine (LLM)
                    </div>
                    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                        <CardContent className="pt-6 space-y-6">
                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label className="text-slate-300">Default Provider</Label>
                                    <Select defaultValue="google">
                                        <SelectTrigger className="bg-slate-950 border-slate-800 text-slate-100">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-slate-950 border-slate-800 text-slate-100">
                                            <SelectItem value="google">Google Gemini</SelectItem>
                                            <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                                            <SelectItem value="openai">OpenAI GPT</SelectItem>
                                            <SelectItem value="ollama">Ollama (Local)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-slate-300">Default Model</Label>
                                    <Select defaultValue="gemini-3-pro">
                                        <SelectTrigger className="bg-slate-950 border-slate-800 text-slate-100">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-slate-950 border-slate-800 text-slate-100">
                                            <SelectItem value="gemini-3-pro">Gemini 3 Pro (1M)</SelectItem>
                                            <SelectItem value="gemini-3-flash">Gemini 3 Flash (1M)</SelectItem>
                                            <SelectItem value="claude-sonnet-4">Claude 4 Sonnet</SelectItem>
                                            <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label className="text-slate-300">Gemini API Key</Label>
                                <div className="flex gap-3">
                                    <Input
                                        type="password"
                                        className="bg-slate-950 border-slate-800 text-slate-100 font-mono"
                                        placeholder="Enter key..."
                                        defaultValue="***************************"
                                    />
                                    <Button variant="outline" className="border-slate-800 bg-slate-900 text-slate-400">
                                        <Key className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </section>

                <section className="space-y-4">
                    <div className="flex items-center gap-2 text-white font-semibold">
                        <Shield className="w-5 h-5 text-orange-500" />
                        Elevation & Security
                    </div>
                    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                        <CardContent className="pt-6 space-y-4">
                            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                                <div>
                                    <div className="text-sm font-medium text-white">Auto-Elevate Bridge</div>
                                    <div className="text-xs text-slate-500">Attempt to run backend as Administrator on startup</div>
                                </div>
                                <Switch defaultChecked />
                            </div>
                            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                                <div>
                                    <div className="text-sm font-medium text-white">Audit Operations</div>
                                    <div className="text-xs text-slate-500">Log all tool execution results to local memory</div>
                                </div>
                                <Switch defaultChecked />
                            </div>
                        </CardContent>
                    </Card>
                </section>

                <section className="space-y-4">
                    <div className="flex items-center gap-2 text-white font-semibold">
                        <Zap className="w-5 h-5 text-yellow-500" />
                        Server Orchestration
                    </div>
                    <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
                        <CardContent className="pt-6 space-y-6">
                            <div className="grid gap-6 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label className="text-slate-300">Frontend Port</Label>
                                    <Input
                                        type="number"
                                        defaultValue="10860"
                                        className="bg-slate-950 border-slate-800 text-slate-100"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-slate-300">Backend Port (Bridge)</Label>
                                    <Input
                                        type="number"
                                        defaultValue="10861"
                                        className="bg-slate-950 border-slate-800 text-slate-100"
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </section>
            </div>
        </div>
    );
}
