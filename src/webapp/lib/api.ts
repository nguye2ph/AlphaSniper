/** FastAPI client — fetch wrapper with typed responses */

import type { Article, ArticleFilters, ArticleStats, HourlyBucket, SentimentTrendPoint, Source, Ticker, TickerSentimentPoint, TopTicker } from "@/types";

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

export const getTickerSentimentHistory = (symbol: string, days = 7) =>
  fetchApi<TickerSentimentPoint[]>(`/api/tickers/${symbol}/sentiment-history`, { days });

/** Sources */
export const getSources = () => fetchApi<Source[]>("/api/sources");

/** Insider Trades */
export const getInsiderTrades = (params?: { ticker?: string; transaction_type?: string; days?: number; limit?: number }) =>
  fetchApi<import("@/types").InsiderTrade[]>("/api/insider-trades", params as Record<string, string | number | undefined>);

/** Earnings */
export const getEarnings = (params?: { ticker?: string; days?: number; limit?: number }) =>
  fetchApi<import("@/types").EarningsEvent[]>("/api/earnings", params as Record<string, string | number | undefined>);

/** Social Sentiment */
export const getSocialSentiment = (params?: { ticker?: string; platform?: string; days?: number; limit?: number }) =>
  fetchApi<import("@/types").SocialSentiment[]>("/api/sentiment/social", params as Record<string, string | number | undefined>);

export const getSentimentSummary = (ticker: string, days = 7) =>
  fetchApi<import("@/types").SentimentSummary>(`/api/sentiment/social/summary`, { ticker, days });

/** Short Interest */
export const getShortInterest = (params?: { ticker?: string; days?: number; limit?: number }) =>
  fetchApi<import("@/types").ShortInterest[]>("/api/short-interest", params as Record<string, string | number | undefined>);

/** Options Flow */
export const getOptionsFlow = (params?: { ticker?: string; days?: number; limit?: number }) =>
  fetchApi<import("@/types").Article[]>("/api/options-flow", params as Record<string, string | number | undefined>);

/** Scheduler Admin */
export const getSchedulerSources = () =>
  fetchApi<import("@/types").SchedulerSource[]>("/api/admin/scheduler/sources");

/** Health */
export const getHealth = () => fetchApi<{ status: string }>("/health");

/** Heatmap */
export const getSentimentHeatmap = (limit = 50) =>
  fetchApi<{ ticker: string; sentiment_avg: number; mention_count: number; health_score: number | null }[]>("/api/sentiment/heatmap", { limit });

/** Portfolio */
export const getPortfolioStats = () =>
  fetchApi<{ total_articles_24h: number; avg_sentiment: number | null; top_movers: { ticker: string; sentiment_avg: number; count: number }[]; upcoming_earnings: number; high_short_interest_count: number }>("/api/portfolio/stats");

/** Alerts */
export const getAlertRules = () =>
  fetchApi<{ id: string; name: string; enabled: boolean; conditions: object[]; ticker_filter: string[] | null; action: string; cooldown_minutes: number; last_triggered_at: string | null; created_at: string }[]>("/api/alerts/rules");

/** Ticker Health */
export const getTickerHealth = (symbol: string) =>
  fetchApi<{ ticker: string; score: number; breakdown: Record<string, number>; signals: string[]; computed_at: string }>(`/api/ticker/${symbol}/health`);
