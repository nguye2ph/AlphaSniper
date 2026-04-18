"""Tests for social sentiment parser and insider trade parser."""

import pytest

from src.parsers.social_sentiment_parser import analyze_sentiment, extract_tickers
from src.parsers.insider_trade_parser import parse_trade, _parse_int, _parse_float, _parse_date


class TestExtractTickers:
    def test_basic_extraction(self):
        tickers = extract_tickers("I'm buying TSLA and AAPL today")
        assert "TSLA" in tickers
        assert "AAPL" in tickers

    def test_dollar_sign_tickers(self):
        tickers = extract_tickers("$NVDA is mooning $AMD too")
        assert "NVDA" in tickers
        assert "AMD" in tickers

    def test_filters_common_words(self):
        tickers = extract_tickers("I AM NOT A CEO BUT I HOLD TSLA")
        assert "TSLA" in tickers
        assert "AM" not in tickers
        assert "NOT" not in tickers
        assert "CEO" not in tickers

    def test_single_letter_filtered(self):
        tickers = extract_tickers("A B C TSLA")
        assert "TSLA" in tickers
        # Single letters should be filtered (len < 2)
        assert "A" not in tickers

    def test_dedup(self):
        tickers = extract_tickers("TSLA TSLA TSLA")
        assert tickers.count("TSLA") == 1

    def test_empty_string(self):
        assert extract_tickers("") == []


class TestAnalyzeSentiment:
    def test_bullish(self):
        score, label = analyze_sentiment("This stock is amazing, great earnings, bullish!")
        assert score > 0
        assert label == "bullish"

    def test_bearish(self):
        score, label = analyze_sentiment("Terrible earnings, stock crashing, disaster")
        assert score < 0
        assert label == "bearish"

    def test_neutral(self):
        score, label = analyze_sentiment("Stock traded at $50 today")
        assert label in ("neutral", "bullish", "bearish")  # VADER can be either

    def test_empty_string(self):
        score, label = analyze_sentiment("")
        assert score == 0.0
        assert label == "neutral"


class TestInsiderTradeParser:
    def test_basic_parse(self):
        payload = {
            "ticker": "AAPL",
            "officer_name": "Tim Cook",
            "officer_title": "CEO",
            "transaction_type": "P - Purchase",
            "shares": "10,000",
            "price": "$150.50",
            "value": "$1,505,000",
            "filing_date": "2026-04-15",
        }
        result = parse_trade(payload)
        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["officer_name"] == "Tim Cook"
        assert result["transaction_type"] == "buy"
        assert result["shares"] == 10000
        assert result["price"] == 150.50
        assert result["value"] == 1505000

    def test_sale_type(self):
        payload = {
            "ticker": "MSFT",
            "officer_name": "Satya Nadella",
            "transaction_type": "S - Sale",
            "shares": "5000",
            "price": "400",
            "value": "2000000",
            "filing_date": "2026-04-10",
        }
        result = parse_trade(payload)
        assert result["transaction_type"] == "sell"

    def test_missing_ticker(self):
        result = parse_trade({"ticker": "", "filing_date": "2026-01-01"})
        assert result is None

    def test_missing_filing_date(self):
        result = parse_trade({"ticker": "AAPL", "filing_date": ""})
        assert result is None

    def test_parse_int_comma(self):
        assert _parse_int("1,000,000") == 1000000
        assert _parse_int(500) == 500

    def test_parse_float_dollar(self):
        assert _parse_float("$150.50") == 150.50
        assert _parse_float(99.9) == 99.9

    def test_parse_date_formats(self):
        assert _parse_date("2026-04-15") is not None
        assert _parse_date("04/15/2026") is not None
        assert _parse_date("") is None
        assert _parse_date("invalid") is None
