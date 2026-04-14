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

const SOURCE_COLORS: Record<string, string> = {
  finnhub: "#3b82f6",
  marketaux: "#8b5cf6",
  sec_edgar: "#f59e0b",
};

const FALLBACK_COLORS = ["#22c55e", "#ec4899", "#06b6d4", "#84cc16"];

interface Props {
  data: { source: string; count: number }[];
}

export function SourceArticlesChart({ data }: Props) {
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
          dataKey="source"
          tickFormatter={(s: string) => s.replaceAll("_", " ")}
          tick={{ fill: "#71717a", fontSize: 12 }}
        />
        <YAxis tick={{ fill: "#71717a", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
          labelStyle={{ color: "#a1a1aa" }}
          labelFormatter={(label) => typeof label === "string" ? label.replaceAll("_", " ") : String(label)}
          formatter={(value) => [value, "Articles"]}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={SOURCE_COLORS[entry.source] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
