import {
  Activity,
  AlertTriangle,
  AppWindow,
  Archive,
  BookOpen,
  Bot,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Cog,
  Cpu,
  FileText,
  HardDrive,
  HelpCircle,
  LayoutDashboard,
  LayoutGrid,
  Package,
  Server,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  Wrench,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/common/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  href: string;
  label: string;
  icon: typeof Server;
}

interface NavSection {
  title: string | null;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: null,
    items: [
      { href: "/", label: "Overview", icon: LayoutDashboard },
      { href: "/chat", label: "Chat", icon: Bot },
      { href: "/tools", label: "MCP Tools", icon: Terminal },
      { href: "/skills", label: "Skills", icon: BookOpen },
      { href: "/apps", label: "Apps Hub", icon: LayoutGrid },
      { href: "/status", label: "Status", icon: Activity },
    ],
  },
  {
    title: "Manage",
    items: [
      { href: "/processes", label: "Processes", icon: Cpu },
      { href: "/services", label: "Services", icon: Cog },
      { href: "/taskbar", label: "Taskbar", icon: AppWindow },
      { href: "/security", label: "Security", icon: ShieldAlert },
    ],
  },
  {
    title: "Storage",
    items: [
      { href: "/volumes", label: "Volumes", icon: HardDrive },
      { href: "/file-owner", label: "File owner", icon: ShieldCheck },
      { href: "/file-recovery", label: "File recovery", icon: Archive },
      { href: "/inventory", label: "Inventory", icon: Package },
    ],
  },
  {
    title: "Diagnostics",
    items: [
      {
        href: "/crash-postmortem",
        label: "Crash postmortem",
        icon: AlertTriangle,
      },
      { href: "/maintenance", label: "Maintenance", icon: Wrench },
      { href: "/logs", label: "Logs", icon: FileText },
    ],
  },
  {
    title: "System",
    items: [
      { href: "/settings", label: "Settings", icon: Settings },
      { href: "/help", label: "Help", icon: HelpCircle },
    ],
  },
];

const STORAGE_KEY = "system-admin-sidebar-sections";

function loadOpenSections(): Record<string, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Record<string, boolean>;
  } catch {
    /* ignore corrupt state */
  }
  return {};
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const [openSections, setOpenSections] =
    useState<Record<string, boolean>>(loadOpenSections);

  const isOpen = (title: string | null) =>
    title === null || openSections[title] !== false;

  // Auto-expand the section holding the active route
  useEffect(() => {
    for (const section of NAV_SECTIONS) {
      if (
        section.title &&
        section.items.some((i) => i.href === location.pathname)
      ) {
        setOpenSections((prev) => {
          if (prev[section.title as string] !== false) return prev;
          const next = { ...prev, [section.title as string]: true };
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
          } catch {
            /* ignore */
          }
          return next;
        });
      }
    }
  }, [location.pathname]);

  const toggleSection = (title: string) => {
    setOpenSections((prev) => {
      const next = { ...prev, [title]: !(prev[title] !== false) };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  };

  const renderItem = (item: NavItem) => {
    const isActive = location.pathname === item.href;
    return (
      <Link
        key={item.href}
        to={item.href}
        className={cn(
          "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
          isActive ? "bg-slate-800 text-white" : "text-slate-300",
          collapsed ? "justify-center" : "justify-start",
        )}
      >
        <item.icon
          className={cn(
            "h-5 w-5",
            !collapsed && "mr-3",
            isActive && "text-blue-400",
          )}
        />
        {!collapsed && <span>{item.label}</span>}

        {/* Tooltip for collapsed mode */}
        {collapsed && (
          <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-sm text-white group-hover:block z-50 whitespace-nowrap">
            {item.label}
          </div>
        )}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
        <div className="flex items-center gap-2 font-semibold text-slate-100">
          <Server className="h-6 w-6 text-blue-500" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300">
              System-admin MCP
            </span>
          )}
        </div>
        {/* Collapse toggle at top per fleet sidebar standard */}
        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {collapsed
          ? NAV_SECTIONS.flatMap((s) => s.items).map(renderItem)
          : NAV_SECTIONS.map((section) =>
              section.title === null ? (
                <div key="top" className="space-y-1">
                  {section.items.map(renderItem)}
                </div>
              ) : (
                <div key={section.title} className="space-y-1 pt-2">
                  <button
                    type="button"
                    onClick={() => toggleSection(section.title as string)}
                    className="flex w-full items-center justify-between rounded-md px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 transition-colors"
                  >
                    <span>{section.title}</span>
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 transition-transform",
                        !isOpen(section.title) && "-rotate-90",
                      )}
                    />
                  </button>
                  {isOpen(section.title) && (
                    <div className="space-y-1">
                      {section.items.map(renderItem)}
                    </div>
                  )}
                </div>
              ),
            )}
      </nav>
    </aside>
  );
}
