from app.database import get_database


class MonitoringService:
    def __init__(self) -> None:
        self.database = get_database()

    async def list_by_client(self, client_id: str) -> list[dict]:
        return await self.database.request(
            "GET",
            "monitorings",
            params={
                "select": "*",
                "client_id": f"eq.{client_id}",
                "order": "created_at.desc",
            },
        )

    async def create(self, client_id: str, name: str) -> dict:
        rows = await self.database.request(
            "POST",
            "monitorings",
            json={"client_id": client_id, "name": name.strip()},
            prefer="return=representation",
        )
        return rows[0]

    async def update_name(self, monitoring_id: str, name: str) -> dict:
        rows = await self.database.request(
            "PATCH",
            "monitorings",
            params={"id": f"eq.{monitoring_id}"},
            json={"name": name.strip()},
            prefer="return=representation",
        )
        return rows[0]

    async def set_active(self, monitoring_id: str, is_active: bool) -> dict:
        rows = await self.database.request(
            "PATCH",
            "monitorings",
            params={"id": f"eq.{monitoring_id}"},
            json={"is_active": is_active},
            prefer="return=representation",
        )
        return rows[0]

    async def delete(self, monitoring_id: str) -> None:
        await self.database.request("DELETE", "monitorings", params={"id": f"eq.{monitoring_id}"})


monitoring_service = MonitoringService()
