"use client";
import { AnimatedCounter } from "./animated-counter";
import { LiveIndicator } from "./live-indicator";

export function KpiCard({
  title,
  value,
  icon,
  valueClass = "text-white",
  live = false,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  valueClass?: string;
  live?: boolean;
}) {
  return (
    <div className="glass-card rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-zinc-400">{title}</span>
          {live && <LiveIndicator />}
        </div>
        <span className="text-zinc-500">{icon}</span>
      </div>
      <p className={`text-2xl font-bold mt-2 ${valueClass}`}>
        {typeof value === "number" ? <AnimatedCounter value={value} /> : value}
      </p>
    </div>
  );
}
