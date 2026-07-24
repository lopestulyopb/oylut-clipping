from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import feedparser
import httpx

from app.schemas.mention import MediaType, Mention

GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?"
    "q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def _split_title(raw_title: str) -> tuple[str, str]:
    title, separator, source = raw_title.rpartition(" - ")
    if separator and title and source:
        return title.strip(), source.strip()
    return raw_title.strip(), "Google News"


async def search_google_news(term: str, period_hours: int = 24) -> list[Mention]:
    """Collect every Google News RSS entry that falls inside the requested period."""
    query = quote_plus(f'"{term}" when:{period_hours}h')
    url = GOOGLE_NEWS_RSS.format(query=query)

    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers={"User-Agent": "OylutClipping/0.1"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    feed = feedparser.parse(response.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=period_hours)
    mentions: list[Mention] = []

    for entry in feed.entries:
        published_at = _parse_date(entry.get("published"))
        if published_at and published_at.astimezone(timezone.utc) < cutoff:
            continue

        title, source = _split_title(entry.get("title", "Sem título"))
        link = entry.get("link")
        if not link:
            continue

        mentions.append(
            Mention(
                title=title,
                source=source,
                media_type=MediaType.NEWS,
                url=link,
                published_at=published_at,
                excerpt=entry.get("summary"),
                searched_term=term,
                matched_term=term,
            )
        )

    return mentions
