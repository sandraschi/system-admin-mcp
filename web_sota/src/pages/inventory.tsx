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
    </div>
  );
}
