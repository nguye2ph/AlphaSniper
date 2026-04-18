import { getAlertRules } from "@/lib/api";

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-[#171f33] p-5 rounded-lg h-32 border border-[#3c4947]/15 flex flex-col justify-between">
      <p className="text-[11px] uppercase tracking-wider text-[#bbcac6]">{label}</p>
      <p className="text-2xl font-mono font-bold text-[#dae2fd]">{value}</p>
    </div>
  );
}

function EnabledBadge({ enabled }: { enabled: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-mono px-2 py-0.5 rounded ${enabled ? "bg-[#4edea3]/15 text-[#4edea3]" : "bg-[#2d3449] text-[#bbcac6]"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${enabled ? "bg-[#4edea3]" : "bg-[#bbcac6]"}`} />
      {enabled ? "Active" : "Disabled"}
    </span>
  );
}

export default async function AlertsPage() {
  let rules: Awaited<ReturnType<typeof getAlertRules>> = [];

  try {
    rules = await getAlertRules();
  } catch {
    // API may not be running
  }

  const activeCount = rules.filter((r) => r.enabled).length;
  const triggeredToday = rules.filter((r) => {
    if (!r.last_triggered_at) return false;
    const d = new Date(r.last_triggered_at);
    const now = new Date();
    return d.toDateString() === now.toDateString();
  }).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">Alert Rules</h1>
        <p className="text-sm text-[#bbcac6] mt-1">Configurable trading signal alerts</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <KpiCard label="Total Rules" value={rules.length} />
        <KpiCard label="Active Rules" value={activeCount} />
        <KpiCard label="Triggered Today" value={triggeredToday} />
      </div>

      {/* Rules Table */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] font-semibold">Rules</h2>
        </div>
        {rules.length === 0 ? (
          <p className="text-center text-[#bbcac6] py-12 text-sm">No alert rules configured</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#131b2e] text-[11px] uppercase tracking-wider text-[#bbcac6]">
                  <th className="text-left px-4 py-2">Name</th>
                  <th className="text-left px-4 py-2">Conditions</th>
                  <th className="text-left px-4 py-2">Tickers</th>
                  <th className="text-left px-4 py-2">Action</th>
                  <th className="text-right px-4 py-2">Cooldown</th>
                  <th className="text-right px-4 py-2">Last Triggered</th>
                  <th className="text-center px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#3c4947]/15">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-3 font-mono font-medium text-[#dae2fd]">{rule.name}</td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <span className="font-mono text-[10px] text-[#bbcac6] bg-[#222a3d] px-2 py-1 rounded truncate block">
                        {rule.conditions.length} condition{rule.conditions.length !== 1 ? "s" : ""}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {rule.ticker_filter?.length ? (
                        <div className="flex flex-wrap gap-1">
                          {rule.ticker_filter.slice(0, 3).map((t) => (
                            <span key={t} className="text-[10px] font-mono bg-[#2d3449] text-[#4fdbc8] px-1.5 py-0.5 rounded">{t}</span>
                          ))}
                          {rule.ticker_filter.length > 3 && (
                            <span className="text-[10px] font-mono text-[#bbcac6]">+{rule.ticker_filter.length - 3}</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-[#bbcac6] text-xs">All</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[#dae2fd]">{rule.action}</td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#bbcac6]">{rule.cooldown_minutes}m</td>
                    <td className="px-4 py-3 text-right font-mono text-xs text-[#bbcac6]">
                      {rule.last_triggered_at
                        ? new Date(rule.last_triggered_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                        : "Never"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <EnabledBadge enabled={rule.enabled} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
