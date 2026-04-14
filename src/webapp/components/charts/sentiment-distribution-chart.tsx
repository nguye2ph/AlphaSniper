"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { Article } from "@/types";

interface Props {
  articles: Article[];
}

const BUCKETS = [
  { label: "Very Bearish", min: -1, max: -0.6, color: "#7f1d1d" },
  { label: "Bearish", min: -0.6, max: -0.2, color: "#ef4444" },
  { label: "Neutral", min: -0.2, max: 0.2, color: "#71717a" },
  { label: "Bullish", min: 0.2, max: 0.6, color: "#22c55e" },
  { label: "Very Bullish", min: 0.6, max: 1.001, color: "#14532d" },
];

export function SentimentDistributionChart({ articles }: Props) {
  const data = BUCKETS.map((b) => ({
    label: b.label,
    color: b.color,
    count: articles.filter(
      (a) => a.sentiment !== null && a.sentiment >= b.min && a.sentiment < b.max
    ).length,
  }));

  const hasData = data.some((d) => d.count > 0);
  if (!hasData) {
    return (
      <div className="flex items-center justify-center h-[300px] text-zinc-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          dataKey="label"
          tick={{ fill: "#71717a", fontSize: 10 }}
          angle={-20}
          textAnchor="end"
          interval={0}
        />
        <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
          labelStyle={{ color: "#a1a1aa" }}
          formatter={(value) => [value, "Articles"]}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
