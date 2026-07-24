from functools import lru_cache
from urllib.parse import urlparse

import httpx

from app.config import get_settings


def normalize_supabase_url(raw_url: str) -> str:
    value = raw_url.strip().strip('"').strip("'")

    # Aceita valores colados no formato SUPABASE_URL=https://...
    if value.upper().startswith("SUPABASE_URL="):
        value = value.split("=", 1)[1].strip().strip('"').strip("'")

    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"

    value = value.rstrip("/")
    if value.endswith("/rest/v1"):
        value = value[: -len("/rest/v1")]

    parsed = urlparse(value)
    hostname = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise RuntimeError("SUPABASE_URL inválida. Use https://SEU-PROJETO.supabase.co")

    if not hostname.endswith(".supabase.co"):
        raise RuntimeError(
            "SUPABASE_URL não aponta para um projeto Supabase. "
            "Use a Project URL no formato https://SEU-PROJETO.supabase.co"
        )

    return value


class SupabaseDatabase:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY precisam estar configuradas.")

        supabase_url = normalize_supabase_url(settings.supabase_url)
        service_key = settings.supabase_service_role_key.strip().strip('"').strip("'")
        if service_key.upper().startswith("SUPABASE_SERVICE_ROLE_KEY="):
            service_key = service_key.split("=", 1)[1].strip().strip('"').strip("'")

        self.base_url = f"{supabase_url}/rest/v1"
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
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

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}/{table}",
                    params=params,
                    json=json,
                    headers=headers,
                )
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Não foi possível localizar o projeto Supabase. Confira a variável SUPABASE_URL no Render."
            ) from exc

        response.raise_for_status()
        if not response.content:
            return []
        return response.json()


@lru_cache
def get_database() -> SupabaseDatabase:
    return SupabaseDatabase()
