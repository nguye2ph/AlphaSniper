/** TypeScript types matching FastAPI Pydantic schemas */

export interface Article {
  id: string;
  source: string;
  source_id: string;
  headline: string;
  summary: string | null;
  url: string;
  published_at: string;
  tickers: string[];
  sentiment: number | null;
  sentiment_label: string | null;
  market_cap: number | null;
  category: string | null;
  content: string | null;
  key_points: string[] | null;
  image_url: string | null;
  author: string | null;
}

export interface ArticleStats {
  total_count: number;
  by_source: Record<string, number>;
  avg_sentiment: number | null;
  articles_today: number;
}

export interface Ticker {
  symbol: string;
  name: string | null;
  exchange: string | null;
  market_cap: number | null;
  sector: string | null;
  is_active: boolean;
}

export interface Source {
  name: string;
  source_type: string;
  base_url: string;
  is_active: boolean;
  article_count: number;
}

/** Aggregation types (Phase 2 endpoints) */

export interface SentimentTrendPoint {
  timestamp: string;
  avg_sentiment: number;
  count: number;
}

export interface TopTicker {
  symbol: string;
  count: number;
  avg_sentiment: number | null;
}

export interface TickerSentimentPoint {
  timestamp: string;
  sentiment: number | null;
  headline: string;
}

export interface HourlyBucket {
  hour: string;
  count: number;
}

export interface ArticleFilters {
  ticker?: string;
  source?: string;
  sentiment_gte?: number;
  sentiment_lte?: number;
  market_cap_gte?: number;
  market_cap_lte?: number;
  category?: string;
  from_date?: string;
  to_date?: string;
  limit?: number;
  offset?: number;
}
