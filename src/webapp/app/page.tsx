import { getArticleStats, getLatestArticles, getSentimentTrend, getTopTickers, getArticlesByHour } from "@/lib/api";
import { formatSentiment, formatMarketCap, marketCapColor } from "@/lib/utils";
import type { Article, ArticleStats, SentimentTrendPoint, TopTicker, HourlyBucket } from "@/types";
import { Activity, BarChart3, Newspaper, TrendingUp } from "lucide-react";
import { SentimentTrendChart } from "@/components/charts/sentiment-trend-chart";
import { ArticlesPerHourChart } from "@/components/charts/articles-per-hour-chart";
import { TopTickersChart } from "@/components/charts/top-tickers-chart";
import { CategoryDonutChart } from "@/components/charts/category-donut-chart";


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

function sentimentLabel(v: number | null) {
  if (v === null) return null;
  if (v > 0.2) return "bullish";
  if (v < -0.2) return "bearish";
  return null;
}

function SentimentDot({ label }: { label: string | null }) {
  const color = label === "bullish" ? "bg-[#4edea3]" : label === "bearish" ? "bg-[#ffb4ab]" : "bg-[#bbcac6]";
  return <span className={`inline-block w-2 h-2 rounded-full shrink-0 mt-1.5 ${color}`} />;
}

function McapBadge({ value }: { value: number | null }) {
  if (value === null) return null;
  return (
    <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#222a3d] ${marketCapColor(value)}`}>
      {formatMarketCap(value)}
    </span>
  );
}

export default async function DashboardPage() {
  const { stats, latest, sentimentTrend, topTickers, byHour } = await getData();
  const now = new Date();

  const categoryCounts: Record<string, number> = {};
  latest.forEach((a) => {
    const cat = a.category || "general";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });
  const categoryData = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));

  const sourceCount = Object.keys(stats.by_source).length;
  const sentLbl = sentimentLabel(stats.avg_sentiment);
  const avgSentClass = sentLbl === "bullish" ? "text-[#4edea3]" : sentLbl === "bearish" ? "text-[#ffb4ab]" : "text-[#dae2fd]";

  return (
    <div className="space-y-6 p-6 bg-[#0b1326] min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#dae2fd]">Terminal Dashboard</h1>
          <p className="text-xs text-[#bbcac6] mt-0.5">Real-time stock news intelligence</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#4edea3] animate-pulse" />
          <span className="text-xs text-[#4edea3] font-mono">LIVE</span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-[#bbcac6]">Articles Today</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#4edea3]/15 text-[#4edea3] font-mono">+12%</span>
          </div>
          <div className="flex items-end gap-2">
            <span className="font-mono text-3xl text-[#dae2fd]">{stats.articles_today}</span>
            <Newspaper className="h-4 w-4 text-[#bbcac6] mb-1.5" />
          </div>
        </div>

        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between">
          <span className="text-xs uppercase tracking-wider text-[#bbcac6]">Total Articles</span>
          <div className="flex items-end gap-2">
            <span className="font-mono text-3xl text-[#dae2fd]">{stats.total_count.toLocaleString()}</span>
            <BarChart3 className="h-4 w-4 text-[#bbcac6] mb-1.5" />
          </div>
        </div>

        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between">
          <span className="text-xs uppercase tracking-wider text-[#bbcac6]">Avg Sentiment</span>
          <div className="flex items-end gap-2">
            <span className={`font-mono text-3xl ${avgSentClass}`}>{formatSentiment(stats.avg_sentiment)}</span>
            <TrendingUp className="h-4 w-4 text-[#bbcac6] mb-1.5" />
          </div>
        </div>

        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between">
          <span className="text-xs uppercase tracking-wider text-[#bbcac6]">Active Sources</span>
          <div className="flex items-end gap-2">
            <span className="font-mono text-3xl text-[#dae2fd]">{sourceCount}</span>
            <div className="flex items-center gap-1 mb-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4edea3] animate-pulse" />
              <Activity className="h-4 w-4 text-[#bbcac6]" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts 2-column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[
          { title: "Sentiment Trend (7D)", chart: <SentimentTrendChart data={sentimentTrend} /> },
          { title: "Volume (24H)", chart: <ArticlesPerHourChart data={byHour} /> },
          { title: "Top Tickers", chart: <TopTickersChart data={topTickers} /> },
          { title: "Category Breakdown", chart: <CategoryDonutChart data={categoryData} /> },
        ].map(({ title, chart }) => (
          <div key={title} className="bg-[#171f33] rounded-lg p-4 border border-[#3c4947]/15">
            <h2 className="text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold mb-3">{title}</h2>
            {chart}
          </div>
        ))}
      </div>

      {/* Live Terminal Feed */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#4fdbc8] animate-pulse" />
          <h2 className="text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold">Live Terminal Feed</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e]">
                {["", "Ticker", "Cap", "Headline", "Sentiment", "Time"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left first:w-6">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {latest.slice(0, 12).map((a) => {
                const lbl = a.sentiment_label;
                const scoreClass = lbl === "bullish" ? "text-[#4edea3]" : lbl === "bearish" ? "text-[#ffb4ab]" : "text-[#bbcac6]";
                const diff = now.getTime() - new Date(a.published_at).getTime();
                const m = Math.floor(diff / 60000);
                const timeAgo = m < 1 ? "now" : m < 60 ? `${m}m` : `${Math.floor(m / 60)}h`;
                return (
                  <tr key={a.id} className="border-t border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-3"><SentimentDot label={lbl} /></td>
                    <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8] text-xs">
                      {a.tickers[0] || "—"}
                    </td>
                    <td className="px-4 py-3"><McapBadge value={a.market_cap} /></td>
                    <td className="px-4 py-3 text-[#dae2fd] max-w-xs truncate text-xs">{a.headline}</td>
                    <td className={`px-4 py-3 font-mono text-xs ${scoreClass}`}>
                      {a.sentiment !== null ? (a.sentiment > 0 ? "+" : "") + a.sentiment.toFixed(2) : "—"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[#bbcac6]">{timeAgo}</td>
                  </tr>
                );
              })}
              {latest.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-[#bbcac6] text-xs">No articles found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
