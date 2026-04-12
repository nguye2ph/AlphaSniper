import { getArticleStats, getLatestArticles } from "@/lib/api";
import { formatSentiment, sentimentColor } from "@/lib/utils";
import type { Article, ArticleStats } from "@/types";
import { Activity, BarChart3, Newspaper, TrendingUp } from "lucide-react";

async function getData(): Promise<{ stats: ArticleStats; latest: Article[] }> {
  try {
    const [stats, latest] = await Promise.all([
      getArticleStats(),
      getLatestArticles(20),
    ]);
    return { stats, latest };
  } catch {
    return {
      stats: { total_count: 0, by_source: {}, avg_sentiment: null, articles_today: 0 },
      latest: [],
    };
  }
}

export default async function DashboardPage() {
  const { stats, latest } = await getData();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Articles Today" value={stats.articles_today} icon={<Newspaper className="h-5 w-5" />} />
        <KpiCard title="Total Articles" value={stats.total_count} icon={<BarChart3 className="h-5 w-5" />} />
        <KpiCard
          title="Avg Sentiment"
          value={formatSentiment(stats.avg_sentiment)}
          icon={<TrendingUp className="h-5 w-5" />}
          valueClass={sentimentColor(
            stats.avg_sentiment !== null
              ? stats.avg_sentiment > 0.2 ? "bullish" : stats.avg_sentiment < -0.2 ? "bearish" : null
              : null
          )}
        />
        <KpiCard title="Active Sources" value={Object.keys(stats.by_source).length} icon={<Activity className="h-5 w-5" />} />
      </div>

      {/* Source breakdown + Latest articles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Articles by Source</h2>
          <div className="space-y-2">
            {Object.entries(stats.by_source).map(([source, count]) => (
              <div key={source} className="flex justify-between items-center">
                <span className="text-sm capitalize">{source}</span>
                <span className="text-sm font-mono text-zinc-400">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Latest Articles</h2>
          <div className="space-y-2 max-h-64 overflow-auto">
            {latest.slice(0, 8).map((a) => (
              <div key={a.id} className="flex items-start gap-2 text-sm">
                <span className={`shrink-0 mt-0.5 text-xs font-mono ${sentimentColor(a.sentiment_label)}`}>
                  {a.sentiment_label?.charAt(0).toUpperCase() || "N"}
                </span>
                <span className="truncate">{a.headline}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function KpiCard({ title, value, icon, valueClass = "text-white" }: {
  title: string; value: string | number; icon: React.ReactNode; valueClass?: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-400">{title}</span>
        <span className="text-zinc-500">{icon}</span>
      </div>
      <p className={`text-2xl font-bold mt-2 ${valueClass}`}>{value}</p>
    </div>
  );
}
