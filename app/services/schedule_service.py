from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.database import get_database
from app.services.monitoring_search_service import monitoring_search_service


class ScheduleService:
    def __init__(self) -> None:
        self.database = get_database()

    async def list_all(self) -> list[dict]:
        return await self.database.request("GET", "schedules", params={"select": "*,monitorings(id,name,clients(id,name))", "order": "created_at.desc"})

    async def create(self, data: dict) -> dict:
        data["next_run_at"] = self._next_run(data).isoformat()
        rows = await self.database.request("POST", "schedules", json=data, prefer="return=representation")
        return rows[0]

    async def set_active(self, schedule_id: str, active: bool) -> None:
        payload = {"is_active": active}
        if active:
            rows = await self.database.request("GET", "schedules", params={"select": "*", "id": f"eq.{schedule_id}", "limit": "1"})
            if rows:
                payload["next_run_at"] = self._next_run(rows[0]).isoformat()
        await self.database.request("PATCH", "schedules", params={"id": f"eq.{schedule_id}"}, json=payload)

    async def delete(self, schedule_id: str) -> None:
        await self.database.request("DELETE", "schedules", params={"id": f"eq.{schedule_id}"})

    async def run_due(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        due = await self.database.request("GET", "schedules", params={"select": "*", "is_active": "eq.true", "next_run_at": f"lte.{now.isoformat()}"})
        executions = []
        for schedule in due:
            try:
                search, mentions, errors = await monitoring_search_service.execute(schedule["monitoring_id"], int(schedule["period_hours"]))
                executions.append({"schedule_id": schedule["id"], "search_id": search["id"], "results": len(mentions), "errors": errors})
            finally:
                schedule["last_run_at"] = now.isoformat()
                next_run = self._next_run(schedule, after=now + timedelta(minutes=1))
                active = not schedule.get("end_date") or next_run.date().isoformat() <= schedule["end_date"]
                await self.database.request("PATCH", "schedules", params={"id": f"eq.{schedule['id']}"}, json={"last_run_at": now.isoformat(), "next_run_at": next_run.isoformat(), "is_active": active})
        return executions

    def _next_run(self, data: dict, after: datetime | None = None) -> datetime:
        tz = ZoneInfo(data.get("timezone") or "America/Fortaleza")
        reference = (after or datetime.now(timezone.utc)).astimezone(tz)
        hour, minute = map(int, str(data["run_time"])[:5].split(":"))
        start = datetime.fromisoformat(str(data["start_date"])).date()
        candidate = reference.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate.date() < start:
            candidate = candidate.replace(year=start.year, month=start.month, day=start.day)
        if candidate <= reference:
            candidate += timedelta(days=1)
        if data["frequency"] == "weekly":
            weekday = int(data.get("weekday") or 0)
            candidate += timedelta(days=(weekday - candidate.weekday()) % 7)
            if candidate <= reference:
                candidate += timedelta(days=7)
        return candidate.astimezone(timezone.utc)


schedule_service = ScheduleService()
