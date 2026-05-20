import { ExternalLink, LayoutGrid } from "lucide-react";
import { APPS_CATALOG } from "@/common/apps-catalog";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function Apps() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <LayoutGrid className="w-8 h-8 text-blue-500" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Apps Hub
          </h1>
          <p className="text-slate-400 text-sm">
            Centralized SOTA fleet navigation
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {APPS_CATALOG.map((app) => (
          <a
            key={app.id}
            href={app.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block group"
          >
            <Card className="h-full bg-slate-900/50 border-slate-800 backdrop-blur-xl transition-all duration-300 group-hover:bg-slate-800 group-hover:border-blue-500/50 group-hover:scale-[1.02] active:scale-95">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                    <app.icon className="w-5 h-5 text-blue-400" />
                  </div>
                  <ExternalLink className="w-4 h-4 text-slate-600 transition-colors group-hover:text-blue-500" />
                </div>
                <CardTitle className="text-white mt-4">{app.label}</CardTitle>
                <CardDescription className="text-slate-400 text-xs mt-1">
                  {app.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {app.tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="secondary"
                      className="bg-slate-800 text-slate-400 text-[10px] capitalize"
                    >
                      {tag}
                    </Badge>
                  ))}
                  <Badge
                    variant="outline"
                    className="border-slate-700 text-slate-500 text-[10px]"
                  >
                    Port {app.port}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </a>
        ))}
      </div>

      <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs">
        <strong>Discovery Protocol:</strong> Applications shown are registered
        in the SOTA master inventory. Links open in a new tab to preserve the
        admin session.
      </div>
    </div>
  );
}
