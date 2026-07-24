from functools import lru_cache

import httpx

from app.config import get_settings


class SupabaseDatabase:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY precisam estar configuradas.")

        supabase_url = settings.supabase_url.strip().rstrip("/")
        if not supabase_url.startswith(("http://", "https://")):
            supabase_url = f"https://{supabase_url}"

        self.base_url = f"{supabase_url}/rest/v1"
        self.headers = {
            "apikey": settings.supabase_service_role_key.strip(),
            "Authorization": f"Bearer {settings.supabase_service_role_key.strip()}",
            "Content-Type": "application/json",
        }

    async def request(
        self,
        method: str,
        table: str,
        *,
        params: dict[str, str] | None = None,
        json: dict | list[dict] | None = None,
        prefer: str | None = None,
    ) -> list[dict]:
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.request(
                method,
                f"{self.base_url}/{table}",
                params=params,
                json=json,
                headers=headers,
            )

        response.raise_for_status()
        if not response.content:
            return []
        return response.json()


@lru_cache
def get_database() -> SupabaseDatabase:
    return SupabaseDatabase()
