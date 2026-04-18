import { getEarnings } from "@/lib/api";
import type { EarningsEvent } from "@/types";

async function getData() {
  try {
    return await getEarnings({ days: 30, limit: 100 });
  } catch {
    return [] as EarningsEvent[];
  }
}

function surpriseColor(pct: number | null) {
  if (pct === null) return "text-[#bbcac6]";
  if (pct > 0) return "text-[#4edea3]";
  if (pct < 0) return "text-[#ffb4ab]";
  return "text-[#bbcac6]";
}

function daysUntilBadge(dateStr: string) {
  const diff = new Date(dateStr).getTime() - Date.now();
  const days = Math.ceil(diff / 86_400_000);
  if (days <= 0) return { label: "TODAY", cls: "bg-[#00a572]/20 text-[#4edea3]" };
  if (days === 1) return { label: "TOMORROW", cls: "bg-[#4fdbc8]/15 text-[#4fdbc8]" };
  return { label: `IN ${days} DAYS`, cls: "bg-[#2d3449] text-[#bbcac6]" };
}

const TH = ({ children, right }: { children: React.ReactNode; right?: boolean }) => (
  <th className={`px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold ${right ? "text-right" : "text-left"}`}>
    {children}
  </th>
);

export default async function EarningsPage() {
  const events = await getData();
  const now = new Date();

  const upcoming = events.filter((e) => new Date(e.report_date) >= now);
  const past = events.filter((e) => new Date(e.report_date) < now);

  // KPI derivations
  const thisWeek = upcoming.filter((e) => {
    const diff = new Date(e.report_date).getTime() - now.getTime();
    return diff <= 7 * 86_400_000;
  });

  const surprises = past.filter((e) => e.surprise_pct !== null).map((e) => e.surprise_pct as number);
  const avgSurprise = surprises.length > 0
    ? surprises.reduce((s, v) => s + v, 0) / surprises.length
    : null;

  const anticipated = upcoming[0]?.ticker ?? "—";

  return (
    <div className="space-y-6 p-6 bg-[#0b1326] min-h-screen">
      <div>
        <h2 className="text-xl font-bold text-[#dae2fd]">Earnings Calendar</h2>
        <p className="text-xs text-[#bbcac6] mt-0.5">Upcoming and recent earnings reports</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between border border-[#3c4947]/15">
          <span className="text-xs uppercase tracking-wider text-[#bbcac6]">This Week</span>
          <div>
            <span className="font-mono text-3xl text-[#dae2fd]">{thisWeek.length}</span>
            <p className="text-[10px] text-[#bbcac6] mt-0.5">upcoming reports</p>
          </div>
        </div>

        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between border border-[#3c4947]/15">
          <span className="text-xs uppercase tracking-wider text-[#bbcac6]">Avg Surprise %</span>
          <div>
            <span className={`font-mono text-3xl ${surpriseColor(avgSurprise)}`}>
              {avgSurprise !== null
                ? `${avgSurprise > 0 ? "+" : ""}${avgSurprise.toFixed(1)}%`
                : "N/A"}
            </span>
            <p className="text-[10px] text-[#bbcac6] mt-0.5">last {past.length} reports</p>
          </div>
        </div>

        <div className="bg-[#171f33] p-5 rounded-lg h-32 flex flex-col justify-between border border-[#3c4947]/15">
          <span className="text-xs uppercase tracking-wider text-[#bbcac6]">Most Anticipated</span>
          <div>
            <span className="font-mono text-3xl text-[#4fdbc8]">{anticipated}</span>
            <p className="text-[10px] text-[#bbcac6] mt-0.5">next to report</p>
          </div>
        </div>
      </div>

      {/* Upcoming Earnings */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30">
          <h2 className="text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold">
            Upcoming Earnings <span className="text-[#4fdbc8] ml-1">{upcoming.length}</span>
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e]">
                <TH>Ticker</TH>
                <TH>Report Date</TH>
                <TH right>Est. EPS</TH>
                <TH>Status</TH>
              </tr>
            </thead>
            <tbody>
              {upcoming.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-[#bbcac6] text-xs">No upcoming earnings</td></tr>
              ) : upcoming.map((e) => {
                const badge = daysUntilBadge(e.report_date);
                return (
                  <tr key={e.id} className="border-t border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8] text-xs">{e.ticker}</td>
                    <td className="px-4 py-3 font-mono text-xs text-[#dae2fd]">
                      {new Date(e.report_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#dae2fd]">
                      {e.estimated_eps !== null ? `$${e.estimated_eps.toFixed(2)}` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${badge.cls}`}>
                        {badge.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Results */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30">
          <h2 className="text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold">
            Recent Results <span className="text-[#4fdbc8] ml-1">{past.length}</span>
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e]">
                <TH>Ticker</TH>
                <TH>Report Date</TH>
                <TH right>Est. EPS</TH>
                <TH right>Act. EPS</TH>
                <TH right>Surprise %</TH>
              </tr>
            </thead>
            <tbody>
              {past.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-[#bbcac6] text-xs">No recent results</td></tr>
              ) : past.map((e) => (
                <tr key={e.id} className="border-t border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors">
                  <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8] text-xs">{e.ticker}</td>
                  <td className="px-4 py-3 font-mono text-xs text-[#dae2fd]">
                    {new Date(e.report_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-[#bbcac6]">
                    {e.estimated_eps !== null ? `$${e.estimated_eps.toFixed(2)}` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs text-[#dae2fd]">
                    {e.actual_eps !== null ? `$${e.actual_eps.toFixed(2)}` : "—"}
                  </td>
                  <td className={`px-4 py-3 text-right font-mono text-xs ${surpriseColor(e.surprise_pct)}`}>
                    {e.surprise_pct !== null
                      ? `${e.surprise_pct > 0 ? "+" : ""}${e.surprise_pct.toFixed(1)}%`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
