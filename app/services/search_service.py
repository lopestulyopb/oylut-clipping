import asyncio
import re
import unicodedata

import httpx

from app.collectors.google_news import search_google_news
from app.schemas.mention import Mention

MAX_RESULTS_PER_SEARCH = 500


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.lower()).strip()


def _publication_key(mention: Mention) -> tuple[str, str]:
    """Identify one publication inside one source.

    The same article returned by multiple search terms is shown once.
    Different articles from the same source remain separate results.
    Similar articles published by different sources also remain separate results.
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
    """Run collectors and keep each distinct publication from each source."""
    tasks = [search_google_news(term, period_hours) for term in terms]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    mentions: list[Mention] = []
    errors: list[str] = []

    for term, response in zip(terms, responses, strict=True):
        if isinstance(response, Exception):
            if isinstance(response, httpx.TimeoutException):
                errors.append(f"A consulta demorou mais que o esperado para o termo: {term}.")
            elif isinstance(response, httpx.HTTPError):
                errors.append(f"Não foi possível consultar notícias para o termo: {term}.")
            else:
                errors.append(f"Não foi possível processar o termo: {term}.")
            continue

        mentions.extend(response)

    mentions.sort(
        key=lambda mention: mention.published_at.timestamp() if mention.published_at else 0,
        reverse=True,
    )
    unique_mentions = _remove_internal_repetitions(mentions)
    return unique_mentions[:MAX_RESULTS_PER_SEARCH], errors
