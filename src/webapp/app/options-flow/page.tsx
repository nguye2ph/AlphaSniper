import { getOptionsFlow } from "@/lib/api";
import type { Article } from "@/types";

async function getData() {
  try {
    return await getOptionsFlow({ limit: 100 });
  } catch {
    return [] as Article[];
  }
}

function SentimentBadge({ label }: { label: string | null }) {
  if (label === "bullish") return (
    <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#00a572]/20 text-[#4edea3]">Bullish</span>
  );
  if (label === "bearish") return (
    <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#93000a]/20 text-[#ffb4ab]">Bearish</span>
  );
  return <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#2d3449] text-[#bbcac6]">Neutral</span>;
}

function KpiCard({ title, value, sub }: { title: string; value: string; sub?: string }) {
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

export default async function OptionsFlowPage() {
  const articles = await getData();

  const bullishCount = articles.filter((a) => a.sentiment_label === "bullish").length;
  const bearishCount = articles.filter((a) => a.sentiment_label === "bearish").length;
  const ratio = bearishCount > 0 ? (bullishCount / bearishCount).toFixed(2) : "∞";

  // Most active ticker by occurrence
  const tickerCounts: Record<string, number> = {};
  articles.forEach((a) => a.tickers.forEach((t) => { tickerCounts[t] = (tickerCounts[t] || 0) + 1; }));
  const mostActive = Object.entries(tickerCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";

  // Rough premium proxy: count of articles × sentiment magnitude
  const totalPremiumProxy = articles.reduce((sum, a) => sum + Math.abs(a.sentiment ?? 0), 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">Options Flow</h1>
        <p className="text-sm text-[#bbcac6] mt-1">Options-related news and sentiment feed</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard title="Total Volume Today" value={articles.length.toString()} sub="articles tracked" />
        <KpiCard title="Sentiment Signal" value={totalPremiumProxy.toFixed(1)} sub="aggregate magnitude" />
        <KpiCard title="Call / Put Ratio" value={ratio} sub={`${bullishCount} bull · ${bearishCount} bear`} />
        <KpiCard title="Most Active" value={mostActive} sub={mostActive !== "—" ? `${tickerCounts[mostActive]} articles` : undefined} />
      </div>

      {/* Filter tabs — visual only */}
      <div className="flex gap-2">
        {["ALL", "CALLS", "PUTS"].map((tab) => (
          <span key={tab}
            className={`px-4 py-1.5 rounded text-xs font-mono font-semibold uppercase tracking-wider cursor-default transition-colors ${
              tab === "ALL"
                ? "bg-[#4fdbc8]/20 text-[#4fdbc8]"
                : "bg-[#2d3449] text-[#bbcac6] hover:bg-[#222a3d]"
            }`}>
            {tab}
          </span>
        ))}
      </div>

      {/* Data table */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e] border-b border-[#3c4947]/30">
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left">Ticker</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left">Headline</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-center">Sentiment</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-right">Published</th>
              </tr>
            </thead>
            <tbody>
              {articles.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-[#bbcac6]">No options flow data</td></tr>
              ) : (
                articles.map((a) => (
                  <tr key={a.id} className="border-b border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8] whitespace-nowrap">
                      {a.tickers.length > 0 ? a.tickers.slice(0, 2).join(", ") : "—"}
                    </td>
                    <td className="px-4 py-3 text-[#dae2fd] max-w-md">
                      <a href={a.url} target="_blank" rel="noreferrer"
                        className="hover:text-[#4fdbc8] transition-colors line-clamp-1">
                        {a.headline}
                      </a>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <SentimentBadge label={a.sentiment_label} />
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#bbcac6] whitespace-nowrap">
                      {new Date(a.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
