from app.database import get_database


class HistoryService:
    def __init__(self) -> None:
        self.database = get_database()

    async def list_searches(self) -> list[dict]:
        return await self.database.request(
            "GET",
            "searches",
            params={
                "select": "*,monitorings(id,name,clients(id,name))",
                "order": "started_at.desc",
            },
        )

    async def get_search(self, search_id: str) -> dict | None:
        rows = await self.database.request(
            "GET",
            "searches",
            params={
                "select": "*,monitorings(id,name,client_id,clients(id,name))",
                "id": f"eq.{search_id}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    async def list_results(self, search_id: str) -> list[dict]:
        return await self.database.request(
            "GET",
            "results",
            params={
                "select": "*",
                "search_id": f"eq.{search_id}",
                "order": "published_at.desc.nullslast,created_at.desc",
            },
        )


history_service = HistoryService()
