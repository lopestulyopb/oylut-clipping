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

    async def delete_search(self, search_id: str) -> None:
        await self.database.request("DELETE", "results", params={"search_id": f"eq.{search_id}"})
        await self.database.request("DELETE", "searches", params={"id": f"eq.{search_id}"})

    async def clear_history(self) -> None:
        searches = await self.database.request("GET", "searches", params={"select": "id"})
        for search in searches:
            await self.delete_search(search["id"])


history_service = HistoryService()
