"""Reddit collector via PRAW — polls r/wallstreetbets, r/stocks for stock mentions."""

import asyncio
from datetime import datetime, timezone

import praw
import structlog

from src.collectors.base_collector import BaseCollector
from src.core.config import settings
from src.core.models.raw_social_post import RawSocialPost

logger = structlog.get_logger()


class RedditPraw(BaseCollector):
    """Polls Reddit subreddits for new posts mentioning stocks. Read-only mode."""

    source_name = "reddit"

    def __init__(self):
        self.subreddits = settings.reddit_subreddits
        self.reddit: praw.Reddit | None = None

    async def setup(self) -> None:
        await super().setup()
        if not settings.reddit_client_id:
            return  # Skip PRAW init when creds missing
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        self.reddit.read_only = True

    def _fetch_subreddit(self, sub_name: str) -> list[tuple[str, dict]]:
        """Sync: fetch new posts from a subreddit. Returns list of (id, payload)."""
        posts: list[tuple[str, dict]] = []
        subreddit = self.reddit.subreddit(sub_name)
        for post in subreddit.new(limit=50):
            payload = {
                "title": post.title,
                "body": post.selftext[:2000] if post.selftext else "",
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "author": str(post.author) if post.author else "[deleted]",
                "subreddit": sub_name,
                "url": f"https://reddit.com{post.permalink}",
                "created_utc": post.created_utc,
                "flair": post.link_flair_text or "",
            }
            posts.append((post.id, payload))
        return posts

    async def collect(self) -> None:
        """Poll Reddit subreddits for new posts."""
        if not self.reddit:
            logger.warning("reddit_credentials_missing")
            return

        loop = asyncio.get_running_loop()
        for sub_name in self.subreddits:
            try:
                fetched = await loop.run_in_executor(None, self._fetch_subreddit, sub_name)
            except Exception as e:
                logger.error("reddit_fetch_error", subreddit=sub_name, error=str(e)[:100])
                continue

            # Save to MongoDB async
            saved = 0
            for post_id, payload in fetched:
                existing = await RawSocialPost.find_one(
                    RawSocialPost.source == self.source_name,
                    RawSocialPost.source_id == post_id,
                )
                if existing:
                    continue
                doc = RawSocialPost(
                    source=self.source_name,
                    source_id=post_id,
                    payload=payload,
                    collected_at=datetime.now(timezone.utc),
                )
                await doc.insert()
                saved += 1

            logger.info("reddit_fetched", subreddit=sub_name, saved=saved)
