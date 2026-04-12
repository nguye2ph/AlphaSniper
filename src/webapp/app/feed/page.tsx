import { getArticles } from "@/lib/api";
import type { Article } from "@/types";
import { ArticleCard } from "@/components/feed/article-card";

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

  let articles: Article[] = [];
  try {
    articles = await getArticles({
      ticker: ticker || undefined,
      category: category || undefined,
      source: source || undefined,
      sentiment_gte: sentiment === "bullish" ? 0.2 : undefined,
      sentiment_lte: sentiment === "bearish" ? -0.2 : undefined,
      limit: 100,
    });
  } catch {
    articles = [];
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">News Feed</h1>
        <span className="text-sm text-zinc-500">{articles.length} articles</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <FilterLink href="/feed" label="All" active={!ticker && !category && !sentiment} />
        <FilterLink href="/feed?sentiment=bullish" label="Bullish" active={sentiment === "bullish"} className="text-green-400" />
        <FilterLink href="/feed?sentiment=bearish" label="Bearish" active={sentiment === "bearish"} className="text-red-400" />
        <FilterLink href="/feed?category=earnings" label="Earnings" active={category === "earnings"} />
        <FilterLink href="/feed?category=merger" label="M&A" active={category === "merger"} />
        <FilterLink href="/feed?category=insider" label="Insider" active={category === "insider"} />
        <FilterLink href="/feed?category=legal" label="Legal" active={category === "legal"} />
        <FilterLink href="/feed?source=finnhub" label="Finnhub" active={source === "finnhub"} />
        <FilterLink href="/feed?source=marketaux" label="MarketAux" active={source === "marketaux"} />
      </div>

      {/* Article list */}
      <div className="space-y-3">
        {articles.length === 0 ? (
          <p className="text-zinc-500 text-center py-12">No articles found</p>
        ) : (
          articles.map((a) => <ArticleCard key={a.id} article={a} />)
        )}
      </div>
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
