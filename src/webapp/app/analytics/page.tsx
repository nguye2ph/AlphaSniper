import Link from "next/link";
import { getPortfolioStats, getSentimentHeatmap } from "@/lib/api";
import { formatSentiment, sentimentColor } from "@/lib/utils";

function heatmapBg(v: number): string {
  if (v > 0.3) return "bg-[#4edea3]/20 border-[#4edea3]/30";
  if (v > 0.1) return "bg-[#4edea3]/10 border-[#4edea3]/20";
  if (v < -0.3) return "bg-[#ffb4ab]/20 border-[#ffb4ab]/30";
  if (v < -0.1) return "bg-[#ffb4ab]/10 border-[#ffb4ab]/20";
  return "bg-[#2d3449]/50 border-[#3c4947]/30";
}

function KpiCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-[#171f33] p-5 rounded-lg h-32 border border-[#3c4947]/15 flex flex-col justify-between">
      <p className="text-[11px] uppercase tracking-wider text-[#bbcac6]">{label}</p>
      <div>
        <p className="text-2xl font-mono font-bold text-[#dae2fd]">{value}</p>
        {sub && <p className="text-xs text-[#bbcac6] mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default async function AnalyticsPage() {
  let stats: Awaited<ReturnType<typeof getPortfolioStats>> | null = null;
  let heatmap: Awaited<ReturnType<typeof getSentimentHeatmap>> = [];

  try {
    [stats, heatmap] = await Promise.all([
      getPortfolioStats(),
      getSentimentHeatmap(40),
    ]);
  } catch {
    // API may not be running; render with empty data
  }

  const avgSentimentLabel =
    stats?.avg_sentiment !== null && stats?.avg_sentiment !== undefined
      ? stats.avg_sentiment > 0.2 ? "bullish" : stats.avg_sentiment < -0.2 ? "bearish" : null
      : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">Analytics</h1>
        <p className="text-sm text-[#bbcac6] mt-1">Portfolio overview &amp; market heatmap</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Articles 24h"
          value={stats?.total_articles_24h ?? "—"}
          sub="collected last 24 hours"
        />
        <KpiCard
          label="Avg Sentiment"
          value={stats?.avg_sentiment != null ? formatSentiment(stats.avg_sentiment) : "—"}
          sub={avgSentimentLabel ?? "neutral"}
        />
        <KpiCard
          label="Upcoming Earnings"
          value={stats?.upcoming_earnings ?? "—"}
          sub="next 7 days"
        />
        <KpiCard
          label="High Short Interest"
          value={stats?.high_short_interest_count ?? "—"}
          sub="tickers flagged"
        />
      </div>

      {/* Sentiment Heatmap */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-5">
        <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] font-semibold mb-4">
          Sentiment Heatmap
        </h2>
        {heatmap.length === 0 ? (
          <p className="text-center text-[#bbcac6] py-8 text-sm">No heatmap data available</p>
        ) : (
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
            {heatmap.map((cell) => (
              <Link
                key={cell.ticker}
                href={`/ticker/${cell.ticker}`}
                className={`flex flex-col items-center justify-center p-2 rounded border text-center transition-opacity hover:opacity-80 ${heatmapBg(cell.sentiment_avg)}`}
              >
                <span className="text-xs font-mono font-bold text-[#dae2fd]">{cell.ticker}</span>
                <span className={`text-[10px] font-mono mt-0.5 ${sentimentColor(cell.sentiment_avg > 0.2 ? "bullish" : cell.sentiment_avg < -0.2 ? "bearish" : null)}`}>
                  {formatSentiment(cell.sentiment_avg)}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Top Movers */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] font-semibold">Top Movers</h2>
        </div>
        {!stats?.top_movers?.length ? (
          <p className="text-center text-[#bbcac6] py-8 text-sm">No data available</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e] text-[11px] uppercase tracking-wider text-[#bbcac6]">
                <th className="text-left px-4 py-2">Ticker</th>
                <th className="text-right px-4 py-2">Avg Sentiment</th>
                <th className="text-right px-4 py-2">Articles</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#3c4947]/15">
              {stats.top_movers.map((m) => {
                const lbl = m.sentiment_avg > 0.2 ? "bullish" : m.sentiment_avg < -0.2 ? "bearish" : null;
                return (
                  <tr key={m.ticker} className="hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-2.5">
                      <Link href={`/ticker/${m.ticker}`} className="font-mono font-bold text-[#4fdbc8] hover:underline">
                        {m.ticker}
                      </Link>
                    </td>
                    <td className={`px-4 py-2.5 text-right font-mono ${sentimentColor(lbl)}`}>
                      {formatSentiment(m.sentiment_avg)}
                    </td>
                    <td className="px-4 py-2.5 text-right font-mono text-[#bbcac6]">{m.count}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
