from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    main_term: str = Field(min_length=2, max_length=150)
    variations: list[str] = Field(default_factory=list)
    period_hours: int = Field(default=24, ge=1, le=720)
