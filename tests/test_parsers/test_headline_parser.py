"""Tests for the rule-based headline parser."""

from src.parsers.headline_parser import parse_headline


class TestTickerExtraction:
    def test_explicit_ticker(self):
        r = parse_headline("$AAPL surges on earnings")
        assert "AAPL" in r.tickers

    def test_multiple_tickers(self):
        r = parse_headline("$AAPL and $TSLA lead tech rally")
        assert "AAPL" in r.tickers
        assert "TSLA" in r.tickers

    def test_no_ticker(self):
        r = parse_headline("Markets close higher on optimism")
        # May or may not extract contextual tickers, but no crash
        assert isinstance(r.tickers, list)

    def test_false_positive_excluded(self):
        r = parse_headline("CEO announces IPO for SEC filing")
        assert "CEO" not in r.tickers
        assert "IPO" not in r.tickers
        assert "SEC" not in r.tickers


class TestSentiment:
    def test_bullish(self):
        r = parse_headline("$AAPL surges on record profit growth")
        assert r.sentiment_label == "bullish"
        assert r.sentiment > 0

    def test_bearish(self):
        r = parse_headline("$PLCE drops after CEO resigns amid fraud probe")
        assert r.sentiment_label == "bearish"
        assert r.sentiment < 0

    def test_neutral(self):
        r = parse_headline("Company announces quarterly results")
        assert r.sentiment_label == "neutral"
        assert r.sentiment == 0.0


class TestCategory:
    def test_earnings(self):
        r = parse_headline("$AAPL Q3 earnings beat expectations")
        assert r.category == "earnings"

    def test_merger(self):
        r = parse_headline("Microsoft to acquire Activision")
        assert r.category == "merger"

    def test_insider(self):
        r = parse_headline("CFO of XYZ Corp resigns")
        assert r.category == "insider"

    def test_regulatory(self):
        r = parse_headline("FDA approves new treatment")
        assert r.category == "regulatory"

    def test_legal(self):
        r = parse_headline("SEC investigation into company fraud")
        assert r.category == "legal"

    def test_analyst(self):
        r = parse_headline("Goldman upgrades stock with new price target")
        assert r.category == "analyst"

    def test_general(self):
        r = parse_headline("Markets open higher today")
        assert r.category == "general"
