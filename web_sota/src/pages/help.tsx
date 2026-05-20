import {
  Cpu,
  HelpCircle,
  Lock,
  Settings,
  ShieldAlert,
  Terminal,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Help() {
  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center gap-3">
        <HelpCircle className="w-8 h-8 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            System Admin Documentation
          </h1>
          <p className="text-slate-400 text-sm">
            Elevated system operations & monitoring protocols
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl border-l-4 border-l-blue-500">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Terminal className="w-5 h-5" />
              Core Capabilities
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-400">
            <p>
              • **System Monitoring**: Real-time CPU, Memory, and Disk tracking
              via PSUtil.
            </p>
            <p>
              • **Process Management**: Elevated control over system processes
              and services.
            </p>
            <p>
              • **WMI Integration**: Direct access to Windows Management
              Instrumentation.
            </p>
            <p>
              • **Elevated Shell**: Secure execution of administrative
              PowerShell commands.
            </p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl border-l-4 border-l-orange-500">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <ShieldAlert className="w-5 h-5" />
              Safety Protocols
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-400">
            <p>
              • **Permission Check**: Most tools require full Administrator
              privileges.
            </p>
            <p>
              • **Conflict Resolution**: Ports 10860/10861 are reserved for this
              hub.
            </p>
            <p>
              • **Verification**: Use the Status page to confirm backend
              connectivity before running ops.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-white">Advanced Workflows</h2>
        <div className="grid gap-4">
          <div className="flex gap-4 p-4 rounded-lg bg-slate-900/30 border border-slate-800">
            <Lock className="w-10 h-10 text-slate-600 shrink-0" />
            <div>
              <h3 className="font-medium text-slate-100">
                Elevated Process Control
              </h3>
              <p className="text-sm text-slate-500 mt-1">
                Manage system-critical processes. Ensure you have identified the
                PID correctly before termination to avoid system instability.
              </p>
            </div>
          </div>
          <div className="flex gap-4 p-4 rounded-lg bg-slate-900/30 border border-slate-800">
            <Cpu className="w-10 h-10 text-slate-600 shrink-0" />
            <div>
              <h3 className="font-medium text-slate-100">
                Performance Profiling
              </h3>
              <p className="text-sm text-slate-500 mt-1">
                Utilize the Dashboard for high-granularity performance
                snapshots. Data is pulled directly from the hardware substrate
                via the Python bridge.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-blue-500/10 border border-blue-500/20">
        <div className="flex gap-3">
          <Settings className="w-6 h-6 text-blue-400 shrink-0" />
          <div>
            <h3 className="font-bold text-blue-400">Self-Healing Registry</h3>
            <p className="text-blue-300/80 text-sm mt-1">
              The `start.ps1` script automatically handles port cleanup and
              backend synchronization. If you encounter connectivity issues,
              restart the service via the provided launcher.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
