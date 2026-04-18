import { getInsiderTrades } from "@/lib/api";
import type { InsiderTrade } from "@/types";
import { formatTimeAgo } from "@/lib/utils";

async function getData() {
  try {
    return await getInsiderTrades({ days: 30, limit: 100 });
  } catch {
    return [] as InsiderTrade[];
  }
}

function typeBadge(type: string) {
  if (type === "buy") return "bg-[#00a572]/20 text-[#4edea3]";
  if (type === "sell") return "bg-[#93000a]/20 text-[#ffb4ab]";
  return "bg-[#2d3449] text-[#bbcac6]";
}

function valueColor(type: string) {
  if (type === "buy") return "text-[#4edea3]";
  if (type === "sell") return "text-[#ffb4ab]";
  return "text-[#dae2fd]";
}

function typeLabel(type: string) {
  if (type === "buy") return "BUY";
  if (type === "sell") return "SELL";
  return "OPT";
}

export default async function InsiderTradesPage() {
  const trades = await getData();

  const now = new Date();
  const volume24h = trades.filter((t) => {
    const diff = now.getTime() - new Date(t.filing_date).getTime();
    return diff < 86_400_000;
  }).reduce((sum, t) => sum + t.value, 0);

  const sectorCounts: Record<string, number> = {};
  trades.forEach((t) => { sectorCounts[t.ticker] = (sectorCounts[t.ticker] || 0) + 1; });
  const topTicker = Object.entries(sectorCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";

  const fmtValue = (v: number) => {
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  };

  return (
    <div className="space-y-6 p-6 bg-[#0b1326] min-h-screen">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-bold text-[#dae2fd]">Insider Trades</h2>
          <p className="text-xs text-[#bbcac6] mt-0.5">Recent SEC Form 4 filings</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-[#171f33] px-4 py-2.5 rounded-lg border border-[#3c4947]/15 text-right">
            <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">24H Volume</p>
            <p className="font-mono text-sm text-[#4fdbc8] mt-0.5">{fmtValue(volume24h)}</p>
          </div>
          <div className="bg-[#171f33] px-4 py-2.5 rounded-lg border border-[#3c4947]/15 text-right">
            <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">Most Active</p>
            <p className="font-mono text-sm text-[#4fdbc8] mt-0.5">{topTicker}</p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e]">
                {["Ticker", "Officer", "Title", "Type", "Shares", "Price", "Value", "Filed"].map((h, i) => (
                  <th
                    key={h}
                    className={`px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold ${i >= 4 ? "text-right" : "text-left"}`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-[#bbcac6] text-xs">
                    No insider trades found
                  </td>
                </tr>
              ) : (
                trades.map((t) => (
                  <tr
                    key={t.id}
                    className="border-t border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors group relative"
                  >
                    <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8] text-xs relative">
                      <span className="absolute left-0 top-0 bottom-0 w-0.5 bg-[#4fdbc8] opacity-0 group-hover:opacity-100 transition-opacity" />
                      {t.ticker}
                    </td>
                    <td className="px-4 py-3 text-[#dae2fd] text-xs truncate max-w-[180px]">{t.officer_name}</td>
                    <td className="px-4 py-3 text-[#bbcac6] text-xs truncate max-w-[140px]">{t.officer_title}</td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${typeBadge(t.transaction_type)}`}>
                        {typeLabel(t.transaction_type)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#dae2fd]">
                      {t.shares.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#dae2fd]">
                      ${t.price.toFixed(2)}
                    </td>
                    <td className={`px-4 py-3 text-right font-mono text-xs ${valueColor(t.transaction_type)}`}>
                      {t.transaction_type === "buy" ? "+" : t.transaction_type === "sell" ? "-" : ""}
                      {fmtValue(t.value)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#bbcac6]">
                      {formatTimeAgo(t.filing_date)}
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
