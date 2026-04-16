"use client";

import { useEffect, useState, useCallback } from "react";
import type { Article } from "@/types";
import { ArticleCard } from "@/components/feed/article-card";

interface Props {
  initialArticles: Article[];
  filters: {
    ticker?: string;
    category?: string;
    source?: string;
    sentiment?: string;
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8200";

async function fetchArticles(filters: Props["filters"], offset = 0): Promise<Article[]> {
  const url = new URL(`${API_BASE}/api/articles`);
  if (filters.ticker) url.searchParams.set("ticker", filters.ticker);
  if (filters.category) url.searchParams.set("category", filters.category);
  if (filters.source) url.searchParams.set("source", filters.source);
  if (filters.sentiment === "bullish") url.searchParams.set("sentiment_gte", "0.2");
  if (filters.sentiment === "bearish") url.searchParams.set("sentiment_lte", "-0.2");
  url.searchParams.set("limit", "100");
  if (offset > 0) url.searchParams.set("offset", String(offset));
  const res = await fetch(url.toString());
  if (!res.ok) return [];
  return res.json();
}

export function FeedContainer({ initialArticles, filters }: Props) {
  const [articles, setArticles] = useState<Article[]>(initialArticles);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [loadingMore, setLoadingMore] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const fresh = await fetchArticles(filters, 0);
      setArticles(fresh);
      setLastUpdated(new Date());
    } catch {
      // silently fail
    }
  }, [filters]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [autoRefresh, refresh]);

  async function loadMore() {
    setLoadingMore(true);
    try {
      const more = await fetchArticles(filters, articles.length);
      setArticles((prev) => {
        const existingIds = new Set(prev.map((a) => a.id));
        const uniqueMore = more.filter((a) => !existingIds.has(a.id));
        return [...prev, ...uniqueMore];
      });
    } catch {
      // silently fail
    } finally {
      setLoadingMore(false);
    }
  }

  const secondsAgo = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);
  const lastUpdatedLabel = secondsAgo < 5 ? "just now" : `${secondsAgo}s ago`;

  return (
    <div className="space-y-4">
      {/* Refresh controls */}
      <div className="flex items-center justify-between text-xs text-zinc-500">
        <span>Updated {lastUpdatedLabel}</span>
        <div className="flex items-center gap-3">
          <button
            onClick={refresh}
            className="px-2 py-1 rounded border border-zinc-700 hover:border-zinc-500 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            Refresh
          </button>
          <button
            onClick={() => setAutoRefresh((v) => !v)}
            className={`px-2 py-1 rounded border transition-colors ${
              autoRefresh
                ? "border-green-500/40 bg-green-500/10 text-green-400"
                : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
            }`}
          >
            Auto {autoRefresh ? "ON" : "OFF"}
          </button>
        </div>
      </div>

      {/* Article list */}
      <div className="space-y-3">
        {articles.length === 0 ? (
          <p className="text-zinc-500 text-center py-12">No articles found</p>
        ) : (
          articles.map((a) => <ArticleCard key={a.id} article={a} />)
        )}
      </div>

      {/* Load more */}
      {articles.length > 0 && (
        <div className="text-center pt-2">
          <button
            onClick={loadMore}
            disabled={loadingMore}
            className="px-4 py-2 rounded border border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 transition-colors text-sm disabled:opacity-50"
          >
            {loadingMore ? "Loading..." : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
