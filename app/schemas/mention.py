from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl


class MediaType(str, Enum):
    NEWS = "noticia"
    YOUTUBE = "youtube"
    SOCIAL = "rede_social"


class Mention(BaseModel):
    title: str
    source: str
    media_type: MediaType
    url: HttpUrl
    published_at: datetime | None = None
    excerpt: str | None = None
    searched_term: str
    matched_term: str
