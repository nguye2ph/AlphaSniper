import { getArticleStats, getSources } from "@/lib/api";
import type { Source } from "@/types";

export default async function SourcesPage() {
  let sources: Source[] = [];
  let stats;
  try {
    [sources, stats] = await Promise.all([getSources(), getArticleStats()]);
  } catch {
    stats = { total_count: 0, by_source: {}, avg_sentiment: null, articles_today: 0 };
  }

  // Merge source metadata with article counts from stats
  const sourceData = [
    { name: "finnhub", type: "api + websocket", url: "https://finnhub.io", count: stats.by_source["finnhub"] || 0 },
    { name: "marketaux", type: "api", url: "https://marketaux.com", count: stats.by_source["marketaux"] || 0 },
    { name: "sec_edgar", type: "rss", url: "https://sec.gov", count: stats.by_source["sec_edgar"] || 0 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Data Sources</h1>

      {/* Source cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sourceData.map((s) => (
          <div key={s.name} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium capitalize">{s.name.replace("_", " ")}</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
                active
              </span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-500">Type</span>
                <span className="text-zinc-300">{s.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Articles</span>
                <span className="text-zinc-300 font-mono">{s.count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">URL</span>
                <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 text-xs hover:underline">
                  {s.url}
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary table */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="text-sm font-medium text-zinc-400 mb-3">Collection Summary</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-500">
              <th className="text-left py-2">Source</th>
              <th className="text-right py-2">Articles</th>
              <th className="text-right py-2">% Total</th>
            </tr>
          </thead>
          <tbody>
            {sourceData.map((s) => (
              <tr key={s.name} className="border-b border-zinc-800/50">
                <td className="py-2 capitalize">{s.name.replace("_", " ")}</td>
                <td className="text-right font-mono">{s.count}</td>
                <td className="text-right font-mono text-zinc-500">
                  {stats.total_count > 0 ? ((s.count / stats.total_count) * 100).toFixed(1) : 0}%
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="text-zinc-300 font-medium">
              <td className="py-2">Total</td>
              <td className="text-right font-mono">{stats.total_count}</td>
              <td className="text-right font-mono">100%</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
