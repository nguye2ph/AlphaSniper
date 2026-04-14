"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { HourlyBucket } from "@/types";

interface Props {
  data: HourlyBucket[];
}

function formatHour(hour: string): string {
  const d = new Date(hour);
  return d.getHours().toString().padStart(2, "0") + ":00";
}

export function ArticlesPerHourChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-zinc-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          dataKey="hour"
          tickFormatter={formatHour}
          tick={{ fill: "#71717a", fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
          labelStyle={{ color: "#a1a1aa" }}
          labelFormatter={(label) => typeof label === "string" ? formatHour(label) : String(label)}
          formatter={(value) => [value, "Articles"]}
        />
        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
