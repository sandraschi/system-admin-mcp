import {
    Activity,
    Bot,
    Brain,
    LayoutGrid,
    MonitorPlay,
    Scan,
    Archive,
    Shield,
    Terminal
} from 'lucide-react';

export interface AppEntry {
    id: string;
    label: string;
    description: string;
    icon: any;
    url: string;
    port: number;
    tags: string[];
}

export const APPS_CATALOG: AppEntry[] = [
    {
        id: 'system-admin',
        label: 'System Admin',
        description: 'Elevated system monitoring and ops',
        icon: Shield,
        url: 'http://localhost:10860',
        port: 10860,
        tags: ['infra', 'admin', 'sota']
    },
    {
        id: 'fleet-dashboard',
        label: 'Fleet Dashboard',
        description: 'Central management hub',
        icon: LayoutGrid,
        url: 'http://localhost:10794',
        port: 10794,
        tags: ['infra', 'admin']
    },
    {
        id: 'advanced-memory',
        label: 'Advanced Memory',
        description: 'Semantic Knowledge Graph',
        icon: Brain,
        url: 'http://localhost:10704',
        port: 10704,
        tags: ['ai', 'memory']
    },
    {
        id: 'obs-mcp',
        label: 'OBS Dashboard',
        description: 'Live streaming control',
        icon: MonitorPlay,
        url: 'http://localhost:10818',
        port: 10818,
        tags: ['media', 'streaming']
    },
    {
        id: 'ocr-interface',
        label: 'OCR Interface',
        description: 'Document extraction',
        icon: Scan,
        url: 'http://localhost:10858',
        port: 10858,
        tags: ['utilities', 'ai']
    },
    {
        id: 'osc-orchestrator',
        label: 'OSC Transport',
        description: 'Real-time media relay',
        icon: Activity,
        url: 'http://localhost:10766',
        port: 10766,
        tags: ['media', 'transport']
    }
];
