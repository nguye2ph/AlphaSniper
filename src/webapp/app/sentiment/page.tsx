import { getArticles, getArticleStats, getSentimentTrend } from "@/lib/api";
import { formatSentiment, sentimentColor } from "@/lib/utils";
import type { Article, ArticleStats, SentimentTrendPoint } from "@/types";
import { SentimentTrendChart } from "@/components/charts/sentiment-trend-chart";
import { SentimentDistributionChart } from "@/components/charts/sentiment-distribution-chart";

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
  const gaugePercent = ((sentimentValue + 1) / 2) * 100;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Sentiment Analysis</h1>

      {/* Gauge */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-6 text-center">
        <p className="text-sm text-zinc-400 mb-2">Market Sentiment</p>
        <p className={`text-4xl font-bold ${sentimentColor(
          sentimentValue > 0.2 ? "bullish" : sentimentValue < -0.2 ? "bearish" : null
        )}`}>
          {formatSentiment(stats.avg_sentiment)}
        </p>
        <div className="mt-4 mx-auto max-w-md">
          <div className="h-3 rounded-full bg-zinc-800 relative overflow-hidden">
            <div className="absolute left-0 top-0 h-full bg-gradient-to-r from-red-500 via-zinc-500 to-green-500 opacity-30 w-full" />
            <div
              className="absolute top-0 h-full w-1 bg-white rounded"
              style={{ left: `${gaugePercent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-zinc-600 mt-1">
            <span>Bearish</span><span>Neutral</span><span>Bullish</span>
          </div>
        </div>
      </div>

      {/* Trend + Distribution charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Sentiment Trend (7d)</h2>
          <SentimentTrendChart data={sentimentTrend} />
        </div>

        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Sentiment Distribution</h2>
          <SentimentDistributionChart articles={articles} />
        </div>
      </div>

      {/* Top movers */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
        <h2 className="text-sm font-medium text-zinc-400 mb-3">Top Movers (by sentiment strength)</h2>
        <div className="space-y-2">
          {topMovers.length === 0 ? (
            <p className="text-zinc-500 text-sm">Not enough data (need 2+ articles per ticker)</p>
          ) : (
            topMovers.map((t) => (
              <a key={t.symbol} href={`/ticker/${t.symbol}`}
                className="flex justify-between items-center hover:bg-zinc-800 rounded px-2 py-1 transition-colors">
                <span className="font-mono text-sm">${t.symbol}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-zinc-500">{t.count} articles</span>
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
