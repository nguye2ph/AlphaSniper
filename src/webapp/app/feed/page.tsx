import { getArticles } from "@/lib/api";
import type { Article } from "@/types";
import { FeedContainer } from "@/components/feed/feed-container";

const MC_TIERS: Record<string, { gte?: number; lte?: number }> = {
  micro: { lte: 250_000_000 },
  small: { gte: 250_000_000, lte: 2_000_000_000 },
  mid: { gte: 2_000_000_000, lte: 10_000_000_000 },
  large: { gte: 10_000_000_000 },
};

export default async function FeedPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | undefined }>;
}) {
  const params = await searchParams;
  const ticker = params.ticker;
  const category = params.category;
  const sentiment = params.sentiment;
  const source = params.source;
  const mcap = params.mcap;

  const mcRange = mcap ? MC_TIERS[mcap] : undefined;

  let articles: Article[] = [];
  try {
    articles = await getArticles({
      ticker: ticker || undefined,
      category: category || undefined,
      source: source || undefined,
      sentiment_gte: sentiment === "bullish" ? 0.2 : undefined,
      sentiment_lte: sentiment === "bearish" ? -0.2 : undefined,
      market_cap_gte: mcRange?.gte,
      market_cap_lte: mcRange?.lte,
      limit: 100,
    });
  } catch {
    articles = [];
  }

  const filters = { ticker, category, source, sentiment, mcap };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">News Feed</h1>
        <span className="text-sm text-zinc-500">{articles.length} articles</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <FilterLink href="/feed" label="All" active={!ticker && !category && !sentiment && !mcap} />
        <FilterLink href="/feed?sentiment=bullish" label="Bullish" active={sentiment === "bullish"} className="text-green-400" />
        <FilterLink href="/feed?sentiment=bearish" label="Bearish" active={sentiment === "bearish"} className="text-red-400" />
        <span className="border-l border-zinc-700 mx-1" />
        <FilterLink href="/feed?mcap=micro" label="Micro <250M" active={mcap === "micro"} className="text-blue-400" />
        <FilterLink href="/feed?mcap=small" label="Small 250M-2B" active={mcap === "small"} className="text-green-400" />
        <FilterLink href="/feed?mcap=mid" label="Mid 2B-10B" active={mcap === "mid"} className="text-amber-400" />
        <FilterLink href="/feed?mcap=large" label="Large >10B" active={mcap === "large"} className="text-purple-400" />
        <span className="border-l border-zinc-700 mx-1" />
        <FilterLink href="/feed?category=earnings" label="Earnings" active={category === "earnings"} />
        <FilterLink href="/feed?category=merger" label="M&A" active={category === "merger"} />
        <FilterLink href="/feed?category=insider" label="Insider" active={category === "insider"} />
        <FilterLink href="/feed?source=finnhub" label="Finnhub" active={source === "finnhub"} />
        <FilterLink href="/feed?source=marketaux" label="MarketAux" active={source === "marketaux"} />
        <FilterLink href="/feed?source=tickertick" label="TickerTick" active={source === "tickertick"} />
      </div>

      {/* Client container with auto-refresh + load more */}
      <FeedContainer initialArticles={articles} filters={filters} />
    </div>
  );
}

function FilterLink({ href, label, active, className = "" }: {
  href: string; label: string; active: boolean; className?: string;
}) {
  return (
    <a
      href={href}
      className={`px-3 py-1 rounded-full text-xs border transition-colors ${className} ${
        active ? "bg-zinc-700 border-zinc-600 text-white" : "border-zinc-800 text-zinc-400 hover:border-zinc-600"
      }`}
    >
      {label}
    </a>
  );
}
