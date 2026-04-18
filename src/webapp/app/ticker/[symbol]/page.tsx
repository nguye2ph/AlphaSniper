import { getTickerNews, getTickerSentimentHistory } from "@/lib/api";
import type { Article, TickerSentimentPoint } from "@/types";
import { formatSentiment, formatMarketCap, marketCapColor, sentimentColor } from "@/lib/utils";
import { SentimentTrendChart } from "@/components/charts/sentiment-trend-chart";
import { CategoryDonutChart } from "@/components/charts/category-donut-chart";

function SentimentBadge({ label }: { label: string | null }) {
  if (label === "bullish") return (
    <span className="px-3 py-1 rounded text-sm font-mono bg-[#00a572]/20 text-[#4edea3]">Bullish</span>
  );
  if (label === "bearish") return (
    <span className="px-3 py-1 rounded text-sm font-mono bg-[#93000a]/20 text-[#ffb4ab]">Bearish</span>
  );
  return <span className="px-3 py-1 rounded text-sm font-mono bg-[#2d3449] text-[#bbcac6]">Neutral</span>;
}

function StatCard({ label, value, className = "text-[#dae2fd]" }: {
  label: string; value: string | number; className?: string;
}) {
  return (
    <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
      <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">{label}</p>
      <p className={`text-xl font-mono font-bold mt-1 ${className}`}>{value}</p>
    </div>
  );
}

export default async function TickerPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const upperSymbol = symbol.toUpperCase();

  let articles: Article[] = [];
  let rawSentimentHistory: TickerSentimentPoint[] = [];
  try {
    [articles, rawSentimentHistory] = await Promise.all([
      getTickerNews(upperSymbol, 50),
      getTickerSentimentHistory(upperSymbol),
    ]);
  } catch {
    articles = [];
    rawSentimentHistory = [];
  }

  const sentimentHistory = rawSentimentHistory.map((p) => ({
    timestamp: p.timestamp,
    avg_sentiment: p.sentiment ?? 0,
    count: 1,
  }));

  const sentiments = articles.filter((a) => a.sentiment !== null).map((a) => a.sentiment!);
  const avgSentiment = sentiments.length > 0 ? sentiments.reduce((a, b) => a + b, 0) / sentiments.length : null;
  const bullishCount = articles.filter((a) => a.sentiment_label === "bullish").length;
  const bearishCount = articles.filter((a) => a.sentiment_label === "bearish").length;
  const marketCap = articles.find((a) => a.market_cap !== null)?.market_cap ?? null;

  const categoryCounts: Record<string, number> = {};
  articles.forEach((a) => {
    const cat = a.category || "general";
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });
  const categoryData = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));

  const overallLabel = avgSentiment !== null
    ? (avgSentiment > 0.2 ? "bullish" : avgSentiment < -0.2 ? "bearish" : null)
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-mono text-4xl font-bold text-[#dae2fd]">${upperSymbol}</h1>
            <p className="font-mono text-2xl text-[#bbcac6] mt-1">—</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <SentimentBadge label={overallLabel} />
            <p className="text-xs text-[#bbcac6]">{articles.length} articles</p>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard label="Market Cap" value={formatMarketCap(marketCap)} className={marketCapColor(marketCap)} />
        <StatCard label="Avg Sentiment" value={formatSentiment(avgSentiment)} className={sentimentColor(overallLabel)} />
        <StatCard label="Bullish" value={bullishCount} className="text-[#4edea3]" />
        <StatCard label="Bearish" value={bearishCount} className="text-[#ffb4ab]" />
        <StatCard label="Total Articles" value={articles.length} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] mb-3">Sentiment Over Time</h2>
          <SentimentTrendChart data={sentimentHistory} />
        </div>
        <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] mb-3">Category Breakdown</h2>
          <CategoryDonutChart data={categoryData} />
        </div>
      </div>

      {/* Articles list */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] font-semibold">News Feed</h2>
        </div>
        {articles.length === 0 ? (
          <p className="px-4 py-8 text-center text-[#bbcac6]">No articles found for ${upperSymbol}</p>
        ) : (
          <div className="divide-y divide-[#3c4947]/15">
            {articles.map((a) => (
              <a key={a.id} href={a.url} target="_blank" rel="noreferrer"
                className="flex items-center gap-4 px-4 py-3 hover:bg-[#222a3d] transition-colors group">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#dae2fd] group-hover:text-[#4fdbc8] transition-colors truncate">{a.headline}</p>
                  <p className="text-xs text-[#bbcac6] mt-0.5 font-mono">
                    {a.source} · {new Date(a.published_at).toLocaleDateString()} {new Date(a.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
                <div className="shrink-0">
                  <SentimentBadge label={a.sentiment_label} />
                </div>
                {a.sentiment !== null && (
                  <span className={`font-mono text-sm shrink-0 w-14 text-right ${sentimentColor(a.sentiment_label)}`}>
                    {formatSentiment(a.sentiment)}
                  </span>
                )}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
