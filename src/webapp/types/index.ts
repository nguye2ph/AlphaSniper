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

/** Phase 2/3 data types */

export interface InsiderTrade {
  id: string;
  ticker: string;
  officer_name: string;
  officer_title: string;
  transaction_type: string;
  shares: number;
  price: number;
  value: number;
  filing_date: string;
}

export interface EarningsEvent {
  id: string;
  ticker: string;
  report_date: string;
  estimated_eps: number | null;
  actual_eps: number | null;
  estimated_revenue: number | null;
  actual_revenue: number | null;
  surprise_pct: number | null;
}

export interface SocialSentiment {
  id: string;
  ticker: string;
  platform: string;
  post_title: string;
  post_score: number;
  subreddit: string | null;
  sentiment_score: number;
  sentiment_label: string;
  tickers: string[] | null;
  posted_at: string;
}

export interface SentimentSummary {
  ticker: string;
  days: number;
  post_count: number;
  avg_sentiment: number;
  total_score: number;
}

export interface ShortInterest {
  id: string;
  ticker: string;
  short_pct_float: number;
  days_to_cover: number;
  borrow_fee_pct: number | null;
  squeeze_score: number | null;
  report_date: string;
}

export interface SchedulerSource {
  config: {
    name: string;
    enabled: boolean;
    current_interval_seconds: number;
    min_interval_seconds: number;
    max_interval_seconds: number;
    strategy: string;
  };
  metrics: {
    ema: number;
    articles_last_hour: number;
    total_polls: number;
    api_errors_last_hour: number;
    rate_limit_errors: number;
    last_poll_at: string | null;
  };
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
