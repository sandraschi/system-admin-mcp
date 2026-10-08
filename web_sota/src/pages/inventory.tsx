import { Package, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import API_BASE from "@/lib/api";

interface ToolItem {
  id: string;
  label: string;
  category: string;
  found: boolean;
  version: string | null;
  path: string | null;
  running: boolean;
  source: string | null;
  install: string | null;
}

const CATEGORY_NAMES: Record<string, string> = {
  dev: "Development",
  ai: "Local AI",
  tcom: "Comms & remote",
  office: "Office",
  admin: "Admin essentials",
};

const CATEGORY_ORDER = ["dev", "ai", "tcom", "office", "admin"];

function str(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

interface SoftwareItem {
  DisplayName?: string;
  DisplayVersion?: string;
  Publisher?: string;
  InstallDate?: string;
}

async function callOp(
  operation: string,
): Promise<{ status?: string; [key: string]: unknown }> {
  const res = await fetch(`${API_BASE}/api/tools/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "system_admin", arguments: { operation } }),
  });
  const data = await res.json();
  if (data.status !== "success") throw new Error(data.message || operation);
  return (data.result || {}) as { status?: string; [key: string]: unknown };
}

function SysinfoSection() {
  const [hw, setHw] = useState<Record<string, unknown> | null>(null);
  const [os, setOs] = useState<Record<string, unknown> | null>(null);
  const [perf, setPerf] = useState<Record<string, unknown> | null>(null);
  const [software, setSoftware] = useState<SoftwareItem[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      callOp("get_hardware_info"),
      callOp("get_os_info"),
      callOp("get_performance_metrics"),
      callOp("get_installed_software"),
    ])
      .then(([h, o, p, s]) => {
        if (cancelled) return;
        setHw(h);
        setOs(o);
        setPerf(p);
        const list = (s.software || s.installed_software || s.programs) as
          | SoftwareItem[]
          | undefined;
        setSoftware(Array.isArray(list) ? list : []);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const swList = software.filter(
    (s) =>
      !query.trim() ||
      `${s.DisplayName || ""} ${s.Publisher || ""}`
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
  );

  const rows: [string, unknown][] = [
    [
      "OS",
      `${str(os?.name)} ${str(os?.version)} (${str(os?.windows_edition)})`,
    ],
    ["Build", str(os?.build_number)],
    [
      "CPU",
      `${str((hw?.cpu as Record<string, unknown> | undefined)?.physical_cores)}C/${str((hw?.cpu as Record<string, unknown> | undefined)?.logical_cores)}T @ ${str((hw?.cpu as Record<string, unknown> | undefined)?.frequency_mhz)} MHz`,
    ],
    ["Boot", str(os?.last_boot)],
  ];

  return (
    <Card
      className="bg-slate-900/50 border-slate-800 backdrop-blur-xl"
      data-testid="sysinfo-card"
    >
      <CardHeader>
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-sky-500" />
          <CardTitle className="text-white">System</CardTitle>
        </div>
        <CardDescription className="text-slate-400 text-xs">
          Hardware, OS, live performance, installed software
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-red-300">{error}</p>}
        <div className="grid gap-2 md:grid-cols-2">
          {rows.map(([k, v]) => (
            <div key={k} className="flex gap-2 text-sm">
              <span className="w-20 shrink-0 text-slate-500">{k}</span>
              <span className="text-slate-200">{str(v)}</span>
            </div>
          ))}
          <div className="flex gap-2 text-sm">
            <span className="w-20 shrink-0 text-slate-500">CPU now</span>
            <span className="text-slate-200">
              {str(
                (perf?.cpu as Record<string, unknown> | undefined)?.percent ??
                  (perf?.cpu as number | undefined),
              )}
              %
            </span>
          </div>
          <div className="flex gap-2 text-sm">
            <span className="w-20 shrink-0 text-slate-500">Memory</span>
            <span className="text-slate-200">
              {str(
                (perf?.memory as Record<string, unknown> | undefined)?.percent,
              )}
              %
            </span>
          </div>
        </div>
        <div>
          <input
            data-testid="sysinfo-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search ${software.length} installed programs…`}
            className="mb-2 h-8 w-64 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-slate-200"
          />
          <div className="max-h-64 overflow-auto rounded border border-slate-800">
            <table className="w-full text-xs">
              <tbody>
                {swList.slice(0, 100).map((s) => (
                  <tr
                    key={`${s.DisplayName}-${s.DisplayVersion}-${s.Publisher}-${s.InstallDate}`}
                    className="border-t border-slate-800/60 text-slate-300"
                  >
                    <td className="px-2 py-1">{s.DisplayName || "—"}</td>
                    <td className="px-2 py-1 font-mono text-slate-500">
                      {s.DisplayVersion || ""}
                    </td>
                    <td className="px-2 py-1 text-slate-500">
                      {s.Publisher || ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function Inventory() {
  const [found, setFound] = useState<ToolItem[]>([]);
  const [missing, setMissing] = useState<ToolItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchToolbox = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/admin-toolbox`);
      const data = await res.json();
      if (data.status !== "success") throw new Error(data.error ?? "unknown");
      setFound(Array.isArray(data.found) ? data.found : []);
      setMissing(Array.isArray(data.missing) ? data.missing : []);
    } catch (e) {
      setError(String(e));
      setFound([]);
      setMissing([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchToolbox();
  }, [fetchToolbox]);

  const byCategory = (items: ToolItem[], cat: string) =>
    items.filter((t) => t.category === cat);

  return (
    <div className="space-y-6" data-testid="inventory-page">
      {" "}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Toolbox inventory
          </h1>
          <p className="text-slate-400 text-sm">
            {found.length} of {found.length + missing.length} admin-relevant
            apps detected
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchToolbox}
          disabled={loading}
          data-testid="inventory-refresh"
          className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
        >
          <RefreshCw
            className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>
      {error && (
        <Card className="bg-red-950/30 border-red-900">
          <CardContent className="pt-4 text-sm text-red-300">
            {error}
          </CardContent>
        </Card>
      )}
      {CATEGORY_ORDER.map((cat) => {
        const present = byCategory(found, cat);
        const absent = byCategory(missing, cat);
        if (present.length === 0 && absent.length === 0) return null;
        return (
          <Card
            key={cat}
            className="bg-slate-900/50 border-slate-800 backdrop-blur-xl"
          >
            <CardHeader>
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-emerald-500" />
                <CardTitle className="text-white">
                  {CATEGORY_NAMES[cat] ?? cat}
                </CardTitle>
              </div>
              <CardDescription className="text-slate-400 text-xs">
                {present.length} installed
                {absent.length > 0 && `, ${absent.length} missing`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border border-slate-800 overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/80 text-left text-slate-400">
                      <th className="px-4 py-3 font-medium">App</th>
                      <th className="px-4 py-3 font-medium">Version</th>
                      <th className="px-4 py-3 font-medium">State</th>
                      <th className="px-4 py-3 font-medium">Get it</th>
                    </tr>
                  </thead>
                  <tbody>
                    {present.map((t) => (
                      <tr
                        key={t.id}
                        className="border-b border-slate-800/50 hover:bg-slate-800/30 text-slate-300"
                      >
                        <td className="px-4 py-2">
                          {t.label}
                          {t.running && (
                            <span className="ml-2 text-[10px] uppercase text-emerald-400">
                              running
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2 font-mono text-xs text-slate-400">
                          {t.version ?? "-"}
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-400">
                          {t.source ?? "found"}
                        </td>
                        <td className="px-4 py-2 text-xs text-slate-500">-</td>
                      </tr>
                    ))}
                    {absent.map((t) => (
                      <tr
                        key={t.id}
                        className="border-b border-slate-800/50 hover:bg-slate-800/30 text-slate-500"
                      >
                        <td className="px-4 py-2">{t.label}</td>
                        <td className="px-4 py-2">-</td>
                        <td className="px-4 py-2 text-xs">missing</td>
                        <td className="px-4 py-2 font-mono text-xs text-slate-400">
                          {t.install?.includes(".")
                            ? `winget install ${t.install}`
                            : (t.install ?? "-")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        );
      })}
      <SysinfoSection />
    </div>
  );
}
