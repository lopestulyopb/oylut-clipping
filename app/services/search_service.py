import asyncio

import httpx

from app.collectors.google_news import search_google_news
from app.schemas.mention import Mention


async def search_mentions(terms: list[str], period_hours: int) -> tuple[list[Mention], list[str]]:
    """Run collectors and preserve every returned mention."""
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
    return mentions, errors
