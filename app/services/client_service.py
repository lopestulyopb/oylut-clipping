import re
import unicodedata

from app.database import get_database


def create_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "cliente"


class ClientService:
    def __init__(self) -> None:
        self.database = get_database()

    async def list_clients(self) -> list[dict]:
        return await self.database.request(
            "GET",
            "clients",
            params={"select": "*", "order": "created_at.desc"},
        )

    async def get_client(self, client_id: str) -> dict | None:
        rows = await self.database.request(
            "GET",
            "clients",
            params={"select": "*", "id": f"eq.{client_id}", "limit": "1"},
        )
        return rows[0] if rows else None

    async def create_client(self, name: str, logo_url: str | None = None) -> dict:
        clean_name = name.strip()
        payload = {
            "name": clean_name,
            "slug": create_slug(clean_name),
            "logo_url": logo_url.strip() if logo_url and logo_url.strip() else None,
        }
        rows = await self.database.request(
            "POST",
            "clients",
            json=payload,
            prefer="return=representation",
        )
        return rows[0]

    async def update_client(self, client_id: str, name: str, logo_url: str | None = None) -> dict:
        clean_name = name.strip()
        rows = await self.database.request(
            "PATCH",
            "clients",
            params={"id": f"eq.{client_id}"},
            json={
                "name": clean_name,
                "slug": create_slug(clean_name),
                "logo_url": logo_url.strip() if logo_url and logo_url.strip() else None,
            },
            prefer="return=representation",
        )
        return rows[0]

    async def set_client_active(self, client_id: str, is_active: bool) -> dict:
        rows = await self.database.request(
            "PATCH",
            "clients",
            params={"id": f"eq.{client_id}"},
            json={"is_active": is_active},
            prefer="return=representation",
        )
        return rows[0]

    async def delete_client(self, client_id: str) -> None:
        await self.database.request("DELETE", "clients", params={"id": f"eq.{client_id}"})


client_service = ClientService()
