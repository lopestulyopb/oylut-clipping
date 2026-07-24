from app.database import get_database


class ClippingService:
    def __init__(self) -> None:
        self.database = get_database()

    async def create(self, *, title: str, items: list[dict], monitoring_id: str | None = None, search_id: str | None = None, client_name: str | None = None, monitoring_name: str | None = None) -> dict:
        rows = await self.database.request("POST", "clippings", json={"title": title.strip(), "monitoring_id": monitoring_id or None, "search_id": search_id or None, "client_name": client_name or None, "monitoring_name": monitoring_name or None, "item_count": len(items)}, prefer="return=representation")
        clipping = rows[0]
        payload = []
        for position, item in enumerate(items, start=1):
            sentiment = item.get("sentiment")
            if sentiment not in {"positive", "neutral", "negative"}:
                sentiment = None
            payload.append({"clipping_id": clipping["id"], "position": position, "source": item.get("source") or "Fonte não identificada", "title": item.get("title") or "Sem título", "url": item.get("url") or "", "matched_term": item.get("term") or item.get("matched_term"), "published_at": item.get("published_at") or None, "excerpt": item.get("excerpt") or None, "sentiment": sentiment})
        if payload:
            await self.database.request("POST", "clipping_items", json=payload)
        return clipping

    async def list_clippings(self) -> list[dict]:
        return await self.database.request("GET", "clippings", params={"select": "*", "order": "created_at.desc"})

    async def get(self, clipping_id: str) -> dict | None:
        rows = await self.database.request("GET", "clippings", params={"select": "*", "id": f"eq.{clipping_id}", "limit": "1"})
        return rows[0] if rows else None

    async def list_items(self, clipping_id: str) -> list[dict]:
        return await self.database.request("GET", "clipping_items", params={"select": "*", "clipping_id": f"eq.{clipping_id}", "order": "position.asc"})

    async def delete(self, clipping_id: str) -> None:
        await self.database.request("DELETE", "clippings", params={"id": f"eq.{clipping_id}"})


clipping_service = ClippingService()
