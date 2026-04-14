"use client";
import { useEffect, useState } from "react";
import { Settings, Zap, Eye, BarChart3 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8200";

// ── Tab: Jobs ────────────────────────────────────────────────────────────────
function JobsTab() {
  const [triggering, setTriggering] = useState<string | null>(null);
  const jobs = [
    { id: "finnhub_rest", name: "Finnhub REST", desc: "Poll market + company news" },
    { id: "marketaux", name: "MarketAux", desc: "Poll global news" },
    { id: "tickertick", name: "TickerTick", desc: "Poll TickerTick API" },
    { id: "process_raw", name: "Process Raw", desc: "Parse raw → clean articles" },
    { id: "scrape_content", name: "Scrape Content", desc: "Fetch article body text" },
  ];
  const trigger = async (id: string) => {
    setTriggering(id);
    try {
      await fetch(`${API_BASE}/api/admin/jobs/trigger/${id}`, { method: "POST" });
    } finally {
      setTriggering(null);
    }
  };
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {jobs.map((j) => (
        <div key={j.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <h3 className="font-medium text-sm">{j.name}</h3>
          <p className="text-xs text-zinc-500 mt-1">{j.desc}</p>
          <button
            onClick={() => trigger(j.id)}
            disabled={triggering === j.id}
            className="mt-3 px-3 py-1 text-xs bg-green-600 hover:bg-green-500 rounded disabled:opacity-50 transition-colors"
          >
            {triggering === j.id ? "Running..." : "Run Now"}
          </button>
        </div>
      ))}
    </div>
  );
}

// ── Tab: Watchlist ───────────────────────────────────────────────────────────
function WatchlistTab({ settings, onUpdate }: { settings: AppSettings; onUpdate: (s: AppSettings) => void }) {
  const [input, setInput] = useState("");
  const remove = async (sym: string) => {
    const symbols = settings.watchlist.filter((s) => s !== sym);
    const res = await fetch(`${API_BASE}/api/admin/settings/watchlist`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols }),
    });
    if (res.ok) onUpdate({ ...settings, watchlist: symbols });
  };
  const add = async () => {
    const sym = input.toUpperCase().trim();
    if (!sym || sym.length > 5 || settings.watchlist.includes(sym)) return;
    const symbols = [...settings.watchlist, sym];
    const res = await fetch(`${API_BASE}/api/admin/settings/watchlist`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols }),
    });
    if (res.ok) { onUpdate({ ...settings, watchlist: symbols }); setInput(""); }
  };
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {settings.watchlist.map((s) => (
          <span key={s} className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-zinc-800 text-sm font-mono">
            {s}
            <button onClick={() => remove(s)} className="text-zinc-500 hover:text-red-400 ml-1">&times;</button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Add ticker..."
          onKeyDown={(e) => e.key === "Enter" && add()}
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm w-32 uppercase"
        />
        <button onClick={add} className="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-500 rounded transition-colors">
          Add
        </button>
      </div>
    </div>
  );
}

// ── Tab: Filters ─────────────────────────────────────────────────────────────
function FiltersTab({ settings, onUpdate }: { settings: AppSettings; onUpdate: (s: AppSettings) => void }) {
  const update = async (threshold: number, enabled: boolean) => {
    const res = await fetch(`${API_BASE}/api/admin/settings/filters`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alert_sentiment_threshold: threshold, alert_enabled: enabled }),
    });
    if (res.ok) onUpdate({ ...settings, alert_sentiment_threshold: threshold, alert_enabled: enabled });
  };
  return (
    <div className="space-y-6 max-w-md">
      <div>
        <label className="text-sm text-zinc-400">Sentiment Alert Threshold</label>
        <div className="flex items-center gap-4 mt-2">
          <input
            type="range" min="0" max="1" step="0.1"
            value={settings.alert_sentiment_threshold}
            onChange={(e) => update(parseFloat(e.target.value), settings.alert_enabled)}
            className="flex-1"
          />
          <span className="text-sm font-mono w-10">{settings.alert_sentiment_threshold}</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => update(settings.alert_sentiment_threshold, !settings.alert_enabled)}
          className={`w-10 h-5 rounded-full transition-colors ${settings.alert_enabled ? "bg-green-500" : "bg-zinc-600"}`}
        >
          <div className={`w-4 h-4 rounded-full bg-white transition-transform ${settings.alert_enabled ? "translate-x-5" : "translate-x-0.5"}`} />
        </button>
        <span className="text-sm text-zinc-400">Alerts {settings.alert_enabled ? "Enabled" : "Disabled"}</span>
      </div>
    </div>
  );
}

// ── Tab: System ──────────────────────────────────────────────────────────────
function SystemTab({ stats }: { stats: SystemStats }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Articles", value: stats.total_articles },
          { label: "Today", value: stats.articles_today },
          { label: "Scraped", value: stats.articles_scraped },
          { label: "Sources", value: Object.keys(stats.by_source).length },
        ].map((s) => (
          <div key={s.label} className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
            <p className="text-xs text-zinc-500">{s.label}</p>
            <p className="text-xl font-bold mt-1">{s.value}</p>
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h3 className="text-sm text-zinc-400 mb-3">Articles by Source</h3>
        {Object.entries(stats.by_source).map(([source, count]) => (
          <div key={source} className="flex justify-between text-sm py-1">
            <span className="capitalize">{source}</span>
            <span className="font-mono text-zinc-400">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Types ────────────────────────────────────────────────────────────────────
interface AppSettings {
  watchlist: string[];
  alert_sentiment_threshold: number;
  alert_enabled: boolean;
}

interface SystemStats {
  total_articles: number;
  articles_today: number;
  articles_scraped: number;
  by_source: Record<string, number>;
}

type TabId = "jobs" | "watchlist" | "filters" | "system";

// ── Page ─────────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const [tab, setTab] = useState<TabId>("jobs");
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/admin/settings`).then((r) => r.json()),
      fetch(`${API_BASE}/api/admin/system/stats`).then((r) => r.json()),
    ])
      .then(([s, st]) => { setSettings(s); setStats(st); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: "jobs", label: "Jobs", icon: Zap },
    { id: "watchlist", label: "Watchlist", icon: Eye },
    { id: "filters", label: "Filters", icon: Settings },
    { id: "system", label: "System", icon: BarChart3 },
  ];

  if (loading) return <div className="text-zinc-500 p-6">Loading...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Tab nav */}
      <div className="flex gap-1 border-b border-zinc-800 pb-px">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-t-lg transition-colors ${
              tab === t.id
                ? "bg-zinc-800 text-white border-b-2 border-green-500"
                : "text-zinc-400 hover:text-white"
            }`}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "jobs" && <JobsTab />}
      {tab === "watchlist" && settings && <WatchlistTab settings={settings} onUpdate={setSettings} />}
      {tab === "filters" && settings && <FiltersTab settings={settings} onUpdate={setSettings} />}
      {tab === "system" && stats && <SystemTab stats={stats} />}
    </div>
  );
}
