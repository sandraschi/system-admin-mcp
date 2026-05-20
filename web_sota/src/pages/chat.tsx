import { Bot, Brain, Send, Settings2, Sparkles, User, Zap } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function Chat() {
  const [message, setMessage] = useState("");
  const [provider, setProvider] = useState("google");
  const [model, setModel] = useState("gemini-3-pro");

  const chatHistory = [
    {
      id: 1,
      type: "bot",
      text: "Systems online. Substrate monitoring active. How can I assist with your orchestration today?",
      time: "03:42:01",
    },
    {
      id: 2,
      type: "user",
      text: "Check the status of the scanner service.",
      time: "03:42:15",
    },
    {
      id: 3,
      type: "bot",
      text: "The Canon LiDE 400 bridge is currently idling. All ports are clear. CPU utilization for the bridge is < 1%.",
      time: "03:42:18",
    },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-2xl font-bold text-white">AI Command</h1>
            <p className="text-slate-400 text-xs italic">
              Multi-model system orchestration bridge
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 p-2 bg-slate-900/50 border border-slate-800 rounded-xl">
          <div className="flex items-center gap-2">
            <Select value={provider} onValueChange={setProvider}>
              <SelectTrigger className="w-[120px] h-8 bg-slate-950 border-slate-800 text-xs text-slate-300 transition-all hover:bg-slate-900">
                <SelectValue placeholder="Provider" />
              </SelectTrigger>
              <SelectContent className="bg-slate-950 border-slate-800 text-slate-300">
                <SelectItem value="google">Google</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="ollama">Ollama (Local)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="w-[160px] h-8 bg-slate-950 border-slate-800 text-xs text-slate-300 transition-all hover:bg-slate-900">
                <SelectValue placeholder="Model" />
              </SelectTrigger>
              <SelectContent className="bg-slate-950 border-slate-800 text-slate-300">
                <SelectItem value="gemini-3-pro">Gemini 3 Pro</SelectItem>
                <SelectItem value="gemini-3-flash">Gemini 3 Flash</SelectItem>
                <SelectItem value="claude-opus-4-6">Claude Opus 4.6</SelectItem>
                <SelectItem value="llama-3-3-70b">Llama 3.3 (70B)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button
            size="icon"
            variant="ghost"
            className="h-8 w-8 text-slate-500 hover:text-blue-400 transition-colors"
          >
            <Settings2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <Card className="flex-1 bg-slate-900/30 border-slate-800 backdrop-blur-xl flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
          {chatHistory.map((chat) => (
            <div
              key={chat.id}
              className={`flex gap-4 ${chat.type === "user" ? "flex-row-reverse" : ""}`}
            >
              <div
                className={`p-2 rounded-xl h-fit border shadow-lg ${
                  chat.type === "bot"
                    ? "bg-blue-500/10 border-blue-500/20 text-blue-400"
                    : "bg-slate-800/50 border-slate-700 text-slate-300"
                }`}
              >
                {chat.type === "bot" ? (
                  <Sparkles className="w-4 h-4" />
                ) : (
                  <User className="w-4 h-4" />
                )}
              </div>
              <div
                className={`max-w-[80%] space-y-1 ${chat.type === "user" ? "text-right" : ""}`}
              >
                <div
                  className={`text-xs font-bold text-slate-500 uppercase tracking-tighter`}
                >
                  {chat.type === "bot"
                    ? "System Intelligence"
                    : "Sandra Schipal"}{" "}
                  • {chat.time}
                </div>
                <div
                  className={`p-4 rounded-3xl text-sm leading-relaxed ${
                    chat.type === "bot"
                      ? "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none border-l-4 border-l-blue-500"
                      : "bg-blue-600 text-white rounded-tr-none"
                  } shadow-2xl`}
                >
                  {chat.text}
                </div>
              </div>
            </div>
          ))}
        </CardContent>

        <div className="p-6 border-t border-slate-800 bg-slate-950/50">
          <div className="relative flex items-center gap-3">
            <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
              <Brain className="w-5 h-5 text-purple-500" />
            </div>
            <Input
              className="bg-slate-900/50 border-slate-800 text-slate-100 placeholder:text-slate-500 rounded-2xl h-12 pr-12 focus-visible:ring-blue-500 transition-all"
              placeholder="Type a system directive..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <Button
              className="absolute right-1 w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-700 active:scale-95 transition-all group"
              size="icon"
            >
              <Send className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Button>
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500 px-2 uppercase font-bold tracking-widest">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3 text-yellow-500" /> FastMCP Latency:
                42ms
              </span>
              <span className="flex items-center gap-1 text-slate-600 opacity-50">
                Context Tokens: 1.2M
              </span>
            </div>
            <div className="flex items-center gap-2">Ready for Directives</div>
          </div>
        </div>
      </Card>
    </div>
  );
}
