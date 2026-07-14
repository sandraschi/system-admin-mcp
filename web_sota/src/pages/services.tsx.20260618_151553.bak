import { Download, RefreshCw, Search, Server } from "lucide-react";
import { download, toCsv } from "@/common/export";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface ServiceRow {
  name: string;
  display_name?: string;
  status: string;
  startup_type?: string;
}

export function Services() {
  const [services, setServices] = useState<ServiceRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 50;

  const fetchServices = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      const res = await fetch(`/api/services?${qs}`);
      if (res.ok) {
        const data = await res.json();
        setServices(
          Array.isArray(data?.services) ? data.services : (data ?? []),
        );
        setTotal(data?.total ?? 0);
      } else {
        setServices([]);
        setTotal(0);
      }
    } catch {
      setServices([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchServices();
  }, [fetchServices]);

  const filtered = services.filter(
    (s) =>
      !filter ||
      s.name.toLowerCase().includes(filter.toLowerCase()) ||
      s.display_name?.toLowerCase().includes(filter.toLowerCase()),
  );

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Services
          </h1>
          <p className="text-slate-400 text-sm">
            Windows services and startup configuration
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            title="Export CSV"
            onClick={() => download(`services-${Date.now()}.csv`, toCsv(services as unknown as Record<string, unknown>[]))}
            className="p-2 rounded text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchServices}
            disabled={loading}
            className="border-slate-800 bg-slate-900/50 text-slate-300 hover:bg-slate-800 transition-all active:scale-95"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-xl">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-emerald-500" />
              <CardTitle className="text-white">Service list</CardTitle>
              {!loading && (
                <span className="text-xs text-slate-500 ml-2">
                  ({total} total)
                </span>
              )}
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Filter by name..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="pl-9 bg-slate-950 border-slate-800 text-slate-100"
              />
            </div>
          </div>
          <CardDescription className="text-slate-400 text-xs">
            Windows services loaded via system_admin(operation="list_services")
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border border-slate-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80 text-left text-slate-400">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Display name</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Startup type</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-4 py-8 text-center text-slate-500"
                    >
                      {loading
                        ? "Loading..."
                        : "No services returned."}
                    </td>
                  </tr>
                )}
                {filtered.map((s) => (
                  <tr
                    key={s.name}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30 text-slate-300"
                  >
                    <td
                      className="px-4 py-2 font-mono text-slate-400 truncate max-w-[180px]"
                      title={s.name}
                    >
                      {s.name}
                    </td>
                    <td
                      className="px-4 py-2 truncate max-w-[220px]"
                      title={s.display_name ?? ""}
                    >
                      {s.display_name ?? "—"}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={
                          s.status?.toLowerCase() === "running"
                            ? "text-emerald-400"
                            : "text-slate-400"
                        }
                      >
                        {s.status ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-400">
                      {s.startup_type ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between mt-4">
            <p className="text-xs text-slate-500">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="border-slate-800 text-slate-400"
              >
                Prev
              </Button>
              <span className="flex items-center text-xs text-slate-500 px-2">
                {page} / {totalPages || 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="border-slate-800 text-slate-400"
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
