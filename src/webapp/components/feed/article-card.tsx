"use client";

import { useState } from "react";
import type { Article } from "@/types";
import { cn, sentimentColor, sentimentBgColor, formatSentiment, formatTimeAgo } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

export function ArticleCard({ article }: { article: Article }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={cn(
      "rounded-lg border p-4 transition-colors cursor-pointer",
      sentimentBgColor(article.sentiment_label),
    )} onClick={() => setExpanded(!expanded)}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium leading-snug">{article.headline}</p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {article.tickers.map((t) => (
              <Badge key={t} variant="outline" className="text-xs font-mono">
                {t}
              </Badge>
            ))}
            <span className={cn("text-xs font-mono", sentimentColor(article.sentiment_label))}>
              {formatSentiment(article.sentiment)}
            </span>
            <span className="text-xs text-zinc-500">{article.source}</span>
            <span className="text-xs text-zinc-600">{formatTimeAgo(article.published_at)}</span>
          </div>
        </div>
        <button className="text-zinc-500 shrink-0 mt-1">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-zinc-800 space-y-2">
          {article.summary && (
            <p className="text-sm text-zinc-400">{article.summary}</p>
          )}
          <div className="flex items-center gap-4 text-xs text-zinc-500">
            <span>Category: {article.category || "general"}</span>
            <span>Source ID: {article.source_id}</span>
            {article.url && (
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
              >
                Open <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
