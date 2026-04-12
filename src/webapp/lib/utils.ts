import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Sentiment label → tailwind text color */
export function sentimentColor(label: string | null): string {
  switch (label) {
    case "bullish": return "text-green-500";
    case "bearish": return "text-red-500";
    default: return "text-zinc-400";
  }
}

/** Sentiment label → tailwind bg color */
export function sentimentBgColor(label: string | null): string {
  switch (label) {
    case "bullish": return "bg-green-500/10 border-green-500/20";
    case "bearish": return "bg-red-500/10 border-red-500/20";
    default: return "bg-zinc-500/10 border-zinc-500/20";
  }
}

/** Format sentiment float to display string */
export function formatSentiment(value: number | null): string {
  if (value === null) return "N/A";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}`;
}

/** Format date to relative time ago */
export function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/** Sentiment value → chart color */
export function sentimentChartColor(value: number): string {
  if (value > 0.2) return "#22c55e";
  if (value < -0.2) return "#ef4444";
  return "#3b82f6";
}
