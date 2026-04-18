import { getShortInterest } from "@/lib/api";
import type { ShortInterest } from "@/types";

async function getData() {
  try {
    return await getShortInterest({ days: 30, limit: 100 });
  } catch {
    return [] as ShortInterest[];
  }
}

function squeezeCircleColor(score: number | null) {
  if (score === null) return "bg-[#2d3449] text-[#bbcac6]";
  if (score >= 80) return "bg-[#93000a]/30 text-[#ffb4ab]";
  if (score >= 50) return "bg-amber-900/30 text-amber-400";
  return "bg-[#00a572]/20 text-[#4edea3]";
}

function shortPctColor(pct: number) {
  if (pct >= 20) return "text-[#ffb4ab]";
  if (pct >= 10) return "text-amber-400";
  return "text-[#dae2fd]";
}

function KpiCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between border border-[#3c4947]/15">
      <p className="text-xs uppercase tracking-wider text-[#bbcac6] font-sans">{title}</p>
      <div>{children}</div>
    </div>
  );
}

export default async function ShortInterestPage() {
  const data = await getData();

  const highest = data.reduce<ShortInterest | null>((best, s) =>
    s.squeeze_score !== null && (best === null || s.squeeze_score > (best.squeeze_score ?? 0)) ? s : best, null);
  const mostShorted = data.reduce<ShortInterest | null>((best, s) =>
    best === null || s.short_pct_float > best.short_pct_float ? s : best, null);
  const avgDtc = data.length > 0
    ? (data.reduce((sum, s) => sum + s.days_to_cover, 0) / data.length).toFixed(1)
    : "—";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">Short Interest</h1>
        <p className="text-sm text-[#bbcac6] mt-1">Daily short interest data from ORTEX</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard title="Highest Squeeze Score">
          {highest ? (
            <>
              <span className="font-mono font-bold text-[#4fdbc8] text-xl">{highest.ticker}</span>
              <span className={`ml-2 inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-mono font-bold ${squeezeCircleColor(highest.squeeze_score)}`}>
                {highest.squeeze_score}
              </span>
            </>
          ) : <span className="font-mono text-3xl text-[#dae2fd]">—</span>}
        </KpiCard>
        <KpiCard title="Most Shorted">
          {mostShorted ? (
            <>
              <p className="font-mono font-bold text-[#4fdbc8] text-xl">{mostShorted.ticker}</p>
              <p className={`font-mono text-lg ${shortPctColor(mostShorted.short_pct_float)}`}>{mostShorted.short_pct_float.toFixed(1)}% float</p>
            </>
          ) : <span className="font-mono text-3xl text-[#dae2fd]">—</span>}
        </KpiCard>
        <KpiCard title="Avg Days to Cover">
          <p className="font-mono text-3xl text-[#dae2fd]">{avgDtc}</p>
        </KpiCard>
      </div>

      {/* Table */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e] border-b border-[#3c4947]/30">
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left w-8">#</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left">Ticker</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-right">Short % Float</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-right">Days to Cover</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-right">Borrow Fee %</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-center">Squeeze Score</th>
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left">Report Date</th>
              </tr>
            </thead>
            <tbody>
              {data.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-[#bbcac6]">No short interest data</td></tr>
              ) : (
                data.map((s, i) => (
                  <tr key={s.id} className="border-b border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-3 font-mono text-[#bbcac6] text-xs">{i + 1}</td>
                    <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8]">{s.ticker}</td>
                    <td className={`px-4 py-3 text-right font-mono ${shortPctColor(s.short_pct_float)}`}>
                      {s.short_pct_float.toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-[#dae2fd]">{s.days_to_cover.toFixed(1)}</td>
                    <td className="px-4 py-3 text-right font-mono text-[#dae2fd]">
                      {s.borrow_fee_pct !== null ? `${s.borrow_fee_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex items-center justify-center w-9 h-9 rounded-full text-sm font-mono font-bold ${squeezeCircleColor(s.squeeze_score)}`}>
                        {s.squeeze_score !== null ? s.squeeze_score : "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-[#bbcac6] text-xs">
                      {new Date(s.report_date).toLocaleDateString()}
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
