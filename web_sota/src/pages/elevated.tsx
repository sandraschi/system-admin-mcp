import {
  Cpu,
  HardDrive,
  Lock,
  RotateCcw,
  Server,
  ShieldAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function Elevated() {
  const systems = [
    {
      id: "services",
      label: "Windows Services",
      icon: Server,
      color: "text-blue-500",
      count: 142,
    },
    {
      id: "processes",
      label: "Active Processes",
      icon: Cpu,
      color: "text-green-500",
      count: 86,
    },
    {
      id: "volumes",
      label: "Disk Management",
      icon: HardDrive,
      color: "text-purple-500",
      count: 4,
    },
    {
      id: "security",
      label: "Security Context",
      icon: Lock,
      color: "text-orange-500",
      status: "Elevated",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <ShieldAlert className="w-8 h-8 text-orange-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Elevated Operations
          </h1>
          <p className="text-slate-400 text-sm">
            Privileged system management and orchestration
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {systems.map((sys) => (
          <Card
            key={sys.id}
            className="bg-slate-900/50 border-slate-800 backdrop-blur-xl"
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                {sys.label}
              </CardTitle>
              <sys.icon className={`w-4 h-4 ${sys.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {sys.count || sys.status}
              </div>
              <Button
                variant="link"
                className="p-0 h-auto text-[10px] text-blue-500 hover:text-blue-400 mt-2"
              >
                Manage Instance →
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="bg-slate-900/50 border-slate-800 overflow-hidden">
          <CardHeader className="border-b border-slate-800 bg-slate-950/50">
            <CardTitle className="text-white text-lg">
              Substrate Control
            </CardTitle>
            <CardDescription className="text-slate-500">
              Global system-level directives
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800 group hover:border-blue-500/30 transition-all">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <Server className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">
                    Restart Core API Bridge
                  </div>
                  <div className="text-xs text-slate-500">
                    Warm reboot of port 10861
                  </div>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800"
              >
                <RotateCcw className="w-3 h-3 mr-2" /> Action
              </Button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-950 border border-slate-800 group hover:border-orange-500/30 transition-all">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-orange-500/10">
                  <Lock className="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <div className="text-sm font-medium text-white">
                    Elevate Session Permissions
                  </div>
                  <div className="text-xs text-slate-500">
                    Request UAC elevation for current PID
                  </div>
                </div>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 text-orange-400 border-orange-500/20"
              >
                <ShieldAlert className="w-3 h-3 mr-2" /> Elevate
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="border-b border-slate-800 bg-slate-950/50">
            <CardTitle className="text-white text-lg">
              System Logs (Live)
            </CardTitle>
            <CardDescription className="text-slate-500">
              Kernel and process events
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="p-4 font-mono text-[10px] space-y-1 h-[200px] overflow-auto scrollbar-thin scrollbar-thumb-slate-800">
              <div className="text-slate-500">
                [03:41:07] [INFO] system_admin_mcp starting elevated bridge...
              </div>
              <div className="text-blue-400">
                [03:41:08] [DEBUG] Bound to port 10861 successfully.
              </div>
              <div className="text-slate-500">
                [03:41:09] [INFO] Memory substrate analysis: 64GB DDR4 detected.
              </div>
              <div className="text-green-400">
                [03:41:10] [SUCCESS] FastMCP 2.14.3 tools registered (12 items).
              </div>
              <div className="text-slate-500">
                [03:41:12] [INFO] CPU affinity set to all 24 logical cores.
              </div>
              <div className="text-orange-400">
                [03:41:15] [WARN] NVIDIA RTX 4090 VRAM access throttled by
                driver.
              </div>
              <div className="text-slate-500">
                [03:41:16] [INFO] Initializing WMI bridge for service
                enumeration.
              </div>
              <div className="text-white">_</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
