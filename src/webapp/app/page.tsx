import { getArticleStats, getLatestArticles, getSentimentTrend, getTopTickers, getArticlesByHour } from "@/lib/api";
import { formatSentiment, formatMarketCap, marketCapColor, sentimentColor } from "@/lib/utils";
import type { Article, ArticleStats, SentimentTrendPoint, TopTicker, HourlyBucket } from "@/types";
import { Activity, BarChart3, Newspaper, TrendingUp } from "lucide-react";
import { SentimentTrendChart } from "@/components/charts/sentiment-trend-chart";
import { ArticlesPerHourChart } from "@/components/charts/articles-per-hour-chart";
import { TopTickersChart } from "@/components/charts/top-tickers-chart";
import { CategoryDonutChart } from "@/components/charts/category-donut-chart";
import { KpiCard } from "@/components/dashboard/kpi-card";

async function getData() {
  try {
    const [stats, latest, sentimentTrend, topTickers, byHour] = await Promise.all([
      getArticleStats(),
      getLatestArticles(20),
      getSentimentTrend(7),
      getTopTickers(10),
      getArticlesByHour(24),
    ]);
    return { stats, latest, sentimentTrend, topTickers, byHour };
  } catch {
    return {
      stats: { total_count: 0, by_source: {}, avg_sentiment: null, articles_today: 0 } as ArticleStats,
      latest: [] as Article[],
      sentimentTrend: [] as SentimentTrendPoint[],
      topTickers: [] as TopTicker[],
      byHour: [] as HourlyBucket[],
    };
  }
}

export default async function DashboardPage() {
  const { stats, latest, sentimentTrend, topTickers, byHour } = await getData();

  // Compute category distribution from latest articles
  const categoryCounts: Record<string, number> = {};
  latest.forEach((a) => {
    const cat = a.category || "general";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });
  const categoryData = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Articles Today" value={stats.articles_today} icon={<Newspaper className="h-5 w-5" />} live />
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

      {/* Charts 2x2 grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Sentiment Trend (7d)">
          <SentimentTrendChart data={sentimentTrend} />
        </ChartCard>

        <ChartCard title="Articles per Hour (24h)">
          <ArticlesPerHourChart data={byHour} />
        </ChartCard>

        <ChartCard title="Top Tickers">
          <TopTickersChart data={topTickers} />
        </ChartCard>

        <ChartCard title="Category Breakdown">
          <CategoryDonutChart data={categoryData} />
        </ChartCard>
      </div>

      {/* Latest articles */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="text-sm font-medium text-zinc-400 mb-3">Latest Articles</h2>
        <div className="space-y-2 max-h-64 overflow-auto">
          {latest.slice(0, 8).map((a) => (
            <div key={a.id} className="flex items-start gap-2 text-sm">
              <span className={`shrink-0 mt-0.5 text-xs font-mono ${sentimentColor(a.sentiment_label)}`}>
                {a.sentiment_label?.charAt(0).toUpperCase() || "N"}
              </span>
              {a.market_cap !== null && (
                <span className={`shrink-0 mt-0.5 text-xs font-mono ${marketCapColor(a.market_cap)}`}>
                  {formatMarketCap(a.market_cap)}
                </span>
              )}
              <span className="truncate">{a.headline}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass-card rounded-lg p-4">
      <h2 className="text-sm font-medium text-zinc-400 mb-3">{title}</h2>
      {children}
    </div>
  );
}
