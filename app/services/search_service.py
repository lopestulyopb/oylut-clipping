import asyncio
import re
import unicodedata

import httpx

from app.collectors.google_news import search_google_news
from app.schemas.mention import Mention


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.lower()).strip()


def _publication_key(mention: Mention) -> tuple[str, str]:
    """Identify one publication inside one source.

    The same article returned by multiple search terms is shown once.
    The same or similar article published by another source remains a separate mention.
    """
    return (_normalize(mention.source), _normalize(mention.title))


def _remove_internal_repetitions(mentions: list[Mention]) -> list[Mention]:
    unique_mentions: list[Mention] = []
    seen: set[tuple[str, str]] = set()

    for mention in mentions:
        key = _publication_key(mention)
        if key in seen:
            continue
        seen.add(key)
        unique_mentions.append(mention)

    return unique_mentions


async def search_mentions(terms: list[str], period_hours: int) -> tuple[list[Mention], list[str]]:
    """Run collectors and keep one record per publication in each source."""
    tasks = [search_google_news(term, period_hours) for term in terms]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    mentions: list[Mention] = []
    errors: list[str] = []

    for term, response in zip(terms, responses, strict=True):
        if isinstance(response, Exception):
            if isinstance(response, httpx.HTTPError):
                errors.append(f"Não foi possível consultar notícias para: {term}.")
            else:
                errors.append(f"Ocorreu um erro ao processar o termo: {term}.")
            continue

        mentions.extend(response)

    mentions.sort(
        key=lambda mention: mention.published_at.timestamp() if mention.published_at else 0,
        reverse=True,
    )
    return _remove_internal_repetitions(mentions), errors
