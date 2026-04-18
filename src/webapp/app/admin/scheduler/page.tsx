import { getSchedulerSources } from "@/lib/api";
import type { SchedulerSource } from "@/types";

async function getData() {
  try {
    return await getSchedulerSources();
  } catch {
    return [] as SchedulerSource[];
  }
}

function fmtInterval(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function StatusBadge({ enabled }: { enabled: boolean }) {
  return enabled
    ? <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#00a572]/20 text-[#4edea3]">Active</span>
    : <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#2d3449] text-[#bbcac6]">Paused</span>;
}

function StrategyBadge({ strategy }: { strategy: string }) {
  const isAuto = strategy.toUpperCase() === "AUTO";
  return isAuto
    ? <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#4fdbc8]/20 text-[#4fdbc8]">AUTO</span>
    : <span className="px-2 py-0.5 rounded text-xs font-mono bg-[#2d3449] text-[#bbcac6]">MANUAL</span>;
}

export default async function SchedulerPage() {
  const sources = await getData();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#dae2fd]">Adaptive Scheduler</h1>
        <p className="text-sm text-[#bbcac6] mt-1">Source configuration &amp; metrics</p>
      </div>

      {/* Config table */}
      <div className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 overflow-hidden">
        <div className="px-4 py-3 border-b border-[#3c4947]/30">
          <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] font-semibold">Source Configuration</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#131b2e] border-b border-[#3c4947]/30">
                {["Source Name", "Status", "Interval", "Min / Max", "Strategy", "EMA", "Last Poll", "Total Polls", "Errors"].map((h) => (
                  <th key={h} className="px-4 py-3 text-[11px] uppercase tracking-wider text-[#bbcac6] font-semibold text-left whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sources.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-8 text-center text-[#bbcac6]">No scheduler sources available</td></tr>
              ) : (
                sources.map((s) => (
                  <tr key={s.config.name} className="border-b border-[#3c4947]/15 hover:bg-[#222a3d] transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-[#4fdbc8]">{s.config.name}</td>
                    <td className="px-4 py-3"><StatusBadge enabled={s.config.enabled} /></td>
                    <td className="px-4 py-3 font-mono text-[#dae2fd]">{fmtInterval(s.config.current_interval_seconds)}</td>
                    <td className="px-4 py-3 font-mono text-[#bbcac6] text-xs whitespace-nowrap">
                      {fmtInterval(s.config.min_interval_seconds)} / {fmtInterval(s.config.max_interval_seconds)}
                    </td>
                    <td className="px-4 py-3"><StrategyBadge strategy={s.config.strategy} /></td>
                    <td className="px-4 py-3 font-mono text-[#dae2fd]">{s.metrics.ema.toFixed(3)}</td>
                    <td className="px-4 py-3 font-mono text-[#bbcac6] text-xs whitespace-nowrap">{fmtTime(s.metrics.last_poll_at)}</td>
                    <td className="px-4 py-3 font-mono text-[#dae2fd]">{s.metrics.total_polls.toLocaleString()}</td>
                    <td className="px-4 py-3 font-mono">
                      <span className={s.metrics.api_errors_last_hour > 0 ? "text-[#ffb4ab]" : "text-[#bbcac6]"}>
                        {s.metrics.api_errors_last_hour}
                      </span>
                      {s.metrics.rate_limit_errors > 0 && (
                        <span className="ml-1 text-xs text-amber-400">+{s.metrics.rate_limit_errors} rl</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live Polling Telemetry */}
      <div>
        <h2 className="text-xs uppercase tracking-wider text-[#bbcac6] font-semibold mb-3">Live Polling Telemetry</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.length === 0 ? (
            <p className="text-[#bbcac6] text-sm col-span-3">No telemetry data</p>
          ) : (
            sources.map((s) => {
              const reqPerMin = s.config.current_interval_seconds > 0
                ? (60 / s.config.current_interval_seconds).toFixed(2)
                : "—";
              return (
                <div key={s.config.name} className="bg-[#171f33] rounded-lg border border-[#3c4947]/15 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-[#4fdbc8]">{s.config.name}</span>
                    <StatusBadge enabled={s.config.enabled} />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">Articles/hr</p>
                      <p className="font-mono text-lg text-[#dae2fd]">{s.metrics.articles_last_hour}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">Req/min</p>
                      <p className="font-mono text-lg text-[#dae2fd]">{reqPerMin}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">EMA</p>
                      <p className="font-mono text-lg text-[#dae2fd]">{s.metrics.ema.toFixed(3)}</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">Errors/hr</p>
                      <p className={`font-mono text-lg ${s.metrics.api_errors_last_hour > 0 ? "text-[#ffb4ab]" : "text-[#dae2fd]"}`}>
                        {s.metrics.api_errors_last_hour}
                      </p>
                    </div>
                  </div>
                  <div className="pt-1 border-t border-[#3c4947]/15">
                    <p className="text-[10px] uppercase tracking-wider text-[#bbcac6]">Last Poll</p>
                    <p className="font-mono text-xs text-[#dae2fd]">{fmtTime(s.metrics.last_poll_at)}</p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
