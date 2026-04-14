"use client";

import { useId } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { SentimentTrendPoint } from "@/types";

interface Props {
  data: SentimentTrendPoint[];
}

function formatTime(timestamp: string): string {
  const d = new Date(timestamp);
  return d.toLocaleDateString("en-US", { weekday: "short" }) + " " +
    d.getHours().toString().padStart(2, "0") + ":" +
    d.getMinutes().toString().padStart(2, "0");
}

export function SentimentTrendChart({ data }: Props) {
  const gradientId = useId();

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-zinc-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTime}
          tick={{ fill: "#71717a", fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[-1, 1]}
          tick={{ fill: "#71717a", fontSize: 11 }}
          tickFormatter={(v: number) => v.toFixed(1)}
        />
        <Tooltip
          contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
          labelStyle={{ color: "#a1a1aa" }}
          labelFormatter={(label) => typeof label === "string" ? formatTime(label) : String(label)}
          formatter={(value, name) => {
            if (name === "avg_sentiment") return [typeof value === "number" ? value.toFixed(3) : value, "Avg Sentiment"];
            if (name === "count") return [value, "Articles"];
            return [value, String(name)];
          }}
        />
        <ReferenceLine y={0} stroke="#52525b" strokeDasharray="4 4" />
        <Area
          type="monotone"
          dataKey="avg_sentiment"
          stroke="#22c55e"
          strokeWidth={2}
          fill={`url(#${gradientId})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
