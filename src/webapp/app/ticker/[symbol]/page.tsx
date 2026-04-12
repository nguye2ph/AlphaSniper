import { getTickerNews } from "@/lib/api";
import type { Article } from "@/types";
import { ArticleCard } from "@/components/feed/article-card";
import { formatSentiment, sentimentColor } from "@/lib/utils";

export default async function TickerPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  const upperSymbol = symbol.toUpperCase();

  let articles: Article[] = [];
  try {
    articles = await getTickerNews(upperSymbol, 50);
  } catch {
    articles = [];
  }

  // Compute stats from articles
  const sentiments = articles.filter((a) => a.sentiment !== null).map((a) => a.sentiment!);
  const avgSentiment = sentiments.length > 0 ? sentiments.reduce((a, b) => a + b, 0) / sentiments.length : null;
  const bullishCount = articles.filter((a) => a.sentiment_label === "bullish").length;
  const bearishCount = articles.filter((a) => a.sentiment_label === "bearish").length;

  // Category breakdown
  const categories: Record<string, number> = {};
  articles.forEach((a) => {
    const cat = a.category || "general";
    categories[cat] = (categories[cat] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-mono">${upperSymbol}</h1>
        <p className="text-zinc-400 text-sm mt-1">{articles.length} articles found</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Avg Sentiment" value={formatSentiment(avgSentiment)} className={sentimentColor(
          avgSentiment !== null ? (avgSentiment > 0.2 ? "bullish" : avgSentiment < -0.2 ? "bearish" : null) : null
        )} />
        <StatCard label="Bullish" value={bullishCount} className="text-green-500" />
        <StatCard label="Bearish" value={bearishCount} className="text-red-500" />
        <StatCard label="Total" value={articles.length} />
      </div>

      {/* Category breakdown */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="text-sm font-medium text-zinc-400 mb-3">Category Breakdown</h2>
        <div className="flex flex-wrap gap-3">
          {Object.entries(categories).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
            <div key={cat} className="flex items-center gap-2 text-sm">
              <span className="capitalize">{cat}</span>
              <span className="text-xs text-zinc-500 font-mono">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Articles */}
      <div className="space-y-3">
        {articles.map((a) => <ArticleCard key={a.id} article={a} />)}
      </div>
    </div>
  );
}

function StatCard({ label, value, className = "text-white" }: {
  label: string; value: string | number; className?: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className={`text-xl font-bold mt-1 ${className}`}>{value}</p>
    </div>
  );
}
