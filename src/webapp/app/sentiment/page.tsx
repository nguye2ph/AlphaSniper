import { getArticles, getArticleStats, getSentimentTrend } from "@/lib/api";
import { formatSentiment, sentimentColor } from "@/lib/utils";
import type { Article, ArticleStats, SentimentTrendPoint } from "@/types";
import { SentimentTrendChart } from "@/components/charts/sentiment-trend-chart";
import { SentimentDistributionChart } from "@/components/charts/sentiment-distribution-chart";

function sentimentDot(label: string | null) {
  if (label === "bullish") return "bg-[#4edea3]";
  if (label === "bearish") return "bg-[#ffb4ab]";
  return "bg-[#bbcac6]";
}

function KpiCard({ title, value, sub }: { title: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between border border-[#3c4947]/15">
      <p className="text-xs uppercase tracking-wider text-[#bbcac6] font-sans">{title}</p>
      <div>
        <p className="font-mono text-3xl text-[#dae2fd]">{value}</p>
        {sub && <p className="text-xs text-[#bbcac6] mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export default async function SentimentPage() {
  let stats: ArticleStats = { total_count: 0, by_source: {}, avg_sentiment: null, articles_today: 0 };
  let articles: Article[] = [];
  let sentimentTrend: SentimentTrendPoint[] = [];
  try {
    [stats, articles, sentimentTrend] = await Promise.all([
      getArticleStats(),
      getArticles({ limit: 200 }),
      getSentimentTrend(7),
    ]);
  } catch {
    // defaults already set
  }

  // Top movers: tickers with most extreme avg sentiment
  const tickerSentiments: Record<string, number[]> = {};
  articles.forEach((a) => {
    if (a.sentiment !== null) {
      a.tickers.forEach((t) => {
        if (!tickerSentiments[t]) tickerSentiments[t] = [];
        tickerSentiments[t].push(a.sentiment!);
      });
    }
  });

  const topMovers = Object.entries(tickerSentiments)
    .map(([symbol, sents]) => ({
      symbol,
      avg: sents.reduce((a, b) => a + b, 0) / sents.length,
      count: sents.length,
    }))
    .filter((t) => t.count >= 2)
    .sort((a, b) => Math.abs(b.avg) - Math.abs(a.avg))
    .slice(0, 10);

  const sentimentValue = stats.avg_sentiment ?? 0;
  const bullishCount = articles.filter((a) => a.sentiment_label === "bullish").length;
  const bearishCount = articles.filter((a) => a.sentiment_label === "bearish").length;
  const ratio = bearishCount > 0 ? (bullishCount / bearishCount).toFixed(2) : "∞";

  const liveFeed = articles.slice(0, 20);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">Social Sentiment</h1>
        <p className="text-sm text-[#bbcac6] mt-1">Aggregated sentiment across all sources</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Total Posts" value={stats.total_count.toLocaleString()} sub={`${stats.articles_today} today`} />
        <KpiCard title="Avg Sentiment Score" value={formatSentiment(stats.avg_sentiment)} sub={sentimentValue > 0.2 ? "Bullish" : sentimentValue < -0.2 ? "Bearish" : "Neutral"} />
        <KpiCard title="Bull / Bear Ratio" value={ratio} sub={`${bullishCount} bull · ${bearishCount} bear`} />
      </div>

      {/* Trend + Distribution charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] mb-3">Sentiment Trend (7d)</h2>
          <SentimentTrendChart data={sentimentTrend} />
        </div>
        <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] mb-3">Sentiment Distribution</h2>
          <SentimentDistributionChart articles={articles} />
        </div>
      </div>

      {/* Live Feed */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
        <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] mb-3">Live Feed</h2>
        <div className="space-y-2">
          {liveFeed.length === 0 ? (
            <p className="text-[#bbcac6] text-sm">No articles</p>
          ) : (
            liveFeed.map((a) => (
              <a key={a.id} href={a.url} target="_blank" rel="noreferrer"
                className="flex items-center gap-3 hover:bg-[#222a3d] rounded px-2 py-1.5 transition-colors">
                <span className={`w-2 h-2 rounded-full shrink-0 ${sentimentDot(a.sentiment_label)}`} />
                <span className="text-sm text-[#dae2fd] flex-1 truncate">{a.headline}</span>
                <span className={`text-xs font-mono shrink-0 ${sentimentColor(a.sentiment_label)}`}>
                  {a.sentiment !== null ? formatSentiment(a.sentiment) : "—"}
                </span>
              </a>
            ))
          )}
        </div>
      </div>

      {/* Top Movers */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
        <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] mb-3">Top Movers (by sentiment strength)</h2>
        <div className="space-y-1">
          {topMovers.length === 0 ? (
            <p className="text-[#bbcac6] text-sm">Not enough data (need 2+ articles per ticker)</p>
          ) : (
            topMovers.map((t) => (
              <a key={t.symbol} href={`/ticker/${t.symbol}`}
                className="flex justify-between items-center hover:bg-[#222a3d] rounded px-2 py-1.5 transition-colors">
                <span className="font-mono text-sm font-bold text-[#4fdbc8]">${t.symbol}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#bbcac6]">{t.count} articles</span>
                  <span className={`text-sm font-mono ${sentimentColor(
                    t.avg > 0.2 ? "bullish" : t.avg < -0.2 ? "bearish" : null
                  )}`}>
                    {formatSentiment(t.avg)}
                  </span>
                </div>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
