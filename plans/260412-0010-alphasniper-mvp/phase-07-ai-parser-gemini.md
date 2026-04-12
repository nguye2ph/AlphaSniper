# Phase 7: AI Parser (Gemini API)

## Overview
- **Priority**: Medium
- **Status**: pending
- **Description**: Replace rule-based headline parser with Google Gemini API for structured extraction. Higher accuracy on complex headlines.

## Key Insights
- Gemini API supports structured output (JSON mode)
- Batch processing: collect N headlines → single API call → parse all
- Fallback: keep rule-based parser for when Gemini is unavailable/rate-limited
- Cost: estimate per 1000 headlines before going live

## Related Code Files
- **Create**: `src/parsers/gemini-parser.py`
- **Modify**: `src/parsers/headline-parser.py` (add fallback chain)
- **Modify**: `src/jobs/parse-article-tasks.py` (use Gemini parser)
- **Modify**: `src/core/config.py` (add GEMINI_API_KEY)

## Gemini Prompt Design
```
Extract structured data from stock news headlines.

For each headline, return JSON:
{
  "tickers": ["AAPL"],        // Stock symbols mentioned
  "sentiment": 0.7,           // -1.0 (bearish) to 1.0 (bullish)
  "sentiment_label": "bullish",
  "category": "earnings",     // earnings|insider|merger|analyst|product|legal|other
  "key_entities": ["Tim Cook"], // People, companies mentioned
  "urgency": "high"           // high|medium|low
}

Headlines:
1. "{headline_1}"
2. "{headline_2}"
...
```

## Implementation Steps
1. Create `GeminiParser` in `gemini-parser.py`:
   - `parse_headline(headline) -> ParsedArticle`
   - `parse_batch(headlines: list[str]) -> list[ParsedArticle]`
   - Structured output mode (JSON schema)
   - Rate limiting + retry with tenacity
2. Create parser chain: Gemini → rule-based fallback
3. Update Taskiq parse task to use Gemini parser
4. Add cost tracking (log token usage per call)
5. Batch processing: collect 10-20 headlines per API call

## Todo List
- [ ] GeminiParser with structured output
- [ ] Batch processing (multiple headlines per call)
- [ ] Fallback chain (Gemini → rule-based)
- [ ] Rate limiting + retry
- [ ] Cost tracking (tokens used)
- [ ] Config: GEMINI_API_KEY

## Test Cases
- Single headline: extracts correct ticker + sentiment
- Batch: 10 headlines parsed in single API call
- Fallback: Gemini unavailable → rule-based parser used
- Complex headline: "CFO of $PLCE resigns amid SEC probe" → ticker=PLCE, sentiment=bearish, category=insider
- Cost: log shows token count per parse call

## Acceptance Criteria
- [ ] Gemini parser extracts tickers with >95% accuracy
- [ ] Batch mode reduces API calls by 10x
- [ ] Fallback works when GEMINI_API_KEY not set
- [ ] Token usage logged for cost monitoring
- [ ] No parsing failures crash the pipeline

## Next Steps
- Phase 8: Integration tests + polish
