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
import { sentimentChartColor, formatSentiment } from "@/lib/utils";
import type { TopTicker } from "@/types";

interface Props {
  data: TopTicker[];
}

export function TopTickersChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-zinc-500 text-sm">
        No data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 10, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
        <XAxis type="number" tick={{ fill: "#71717a", fontSize: 11 }} />
        <YAxis
          type="category"
          dataKey="symbol"
          tick={{ fill: "#a1a1aa", fontSize: 11, fontFamily: "monospace" }}
          width={50}
        />
        <Tooltip
          contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
          labelStyle={{ color: "#a1a1aa" }}
          formatter={(value, _name, props) => {
            const item = props.payload as TopTicker;
            return [
              `${value} articles (sentiment: ${formatSentiment(item.avg_sentiment)})`,
              item.symbol,
            ];
          }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={sentimentChartColor(entry.avg_sentiment)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
