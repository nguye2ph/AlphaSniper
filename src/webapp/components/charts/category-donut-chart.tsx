"use client";

import {
  PieChart,
  Pie,
  Cell,
  Legend,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const COLORS = [
  "#22c55e", "#ef4444", "#3b82f6", "#f59e0b",
  "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
];

interface Props {
  data: { name: string; value: number }[];
}

export function CategoryDonutChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-zinc-500 text-sm">
        No data available
      </div>
    );
  }

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="45%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={2}
          dataKey="value"
          label={false}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <text x="50%" y="43%" textAnchor="middle" dominantBaseline="middle" fill="#e4e4e7" fontSize={22} fontWeight="bold">
          {total}
        </text>
        <text x="50%" y="52%" textAnchor="middle" dominantBaseline="middle" fill="#71717a" fontSize={11}>
          total
        </text>
        <Tooltip
          contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px" }}
          labelStyle={{ color: "#a1a1aa" }}
          formatter={(value, name) => [value, name]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: "11px", color: "#a1a1aa" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
