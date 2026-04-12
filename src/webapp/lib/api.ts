/** FastAPI client — fetch wrapper with typed responses */

import type { Article, ArticleFilters, ArticleStats, HourlyBucket, SentimentTrendPoint, Source, Ticker, TopTicker } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8200";

async function fetchApi<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
    });
  }

  const res = await fetch(url.toString(), { next: { revalidate: 30 } });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

/** Articles */
export const getArticles = (filters?: ArticleFilters) =>
  fetchApi<Article[]>("/api/articles", filters as Record<string, string | number | undefined>);

export const getLatestArticles = (limit = 10) =>
  fetchApi<Article[]>("/api/articles/latest", { limit });

export const getArticleStats = () =>
  fetchApi<ArticleStats>("/api/articles/stats");

/** Aggregations (Phase 2 endpoints) */
export const getSentimentTrend = (days = 7) =>
  fetchApi<SentimentTrendPoint[]>("/api/articles/sentiment-trend", { days });

export const getTopTickers = (limit = 10) =>
  fetchApi<TopTicker[]>("/api/articles/top-tickers", { limit });

export const getArticlesByHour = (hours = 24) =>
  fetchApi<HourlyBucket[]>("/api/articles/by-hour", { hours });

/** Tickers */
export const getTickers = () => fetchApi<Ticker[]>("/api/tickers");

export const getTickerNews = (symbol: string, limit = 20) =>
  fetchApi<Article[]>(`/api/tickers/${symbol}/news`, { limit });

export const getTickerSentimentHistory = (symbol: string) =>
  fetchApi<SentimentTrendPoint[]>(`/api/tickers/${symbol}/sentiment-history`);

/** Sources */
export const getSources = () => fetchApi<Source[]>("/api/sources");

/** Health */
export const getHealth = () => fetchApi<{ status: string }>("/health");
