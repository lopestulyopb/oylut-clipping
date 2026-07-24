import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.database import get_database
from app.services.clipping_service import clipping_service
from app.services.monitoring_search_service import monitoring_search_service


class ScheduleService:
    def __init__(self) -> None:
        self.database = get_database()

    async def list_all(self) -> list[dict]:
        return await self.database.request(
            "GET",
            "schedules",
            params={
                "select": "*,monitorings(id,name,clients(id,name))",
                "order": "created_at.desc",
            },
        )

    async def create(self, data: dict) -> dict:
        data["next_run_at"] = self._next_run(data).isoformat()
        rows = await self.database.request(
            "POST", "schedules", json=data, prefer="return=representation"
        )
        return rows[0]

    async def set_active(self, schedule_id: str, active: bool) -> None:
        payload = {"is_active": active}
        if active:
            rows = await self.database.request(
                "GET",
                "schedules",
                params={"select": "*", "id": f"eq.{schedule_id}", "limit": "1"},
            )
            if rows:
                payload["next_run_at"] = self._next_run(rows[0]).isoformat()
                payload["last_run_at"] = datetime.now(timezone.utc).isoformat()
        await self.database.request(
            "PATCH", "schedules", params={"id": f"eq.{schedule_id}"}, json=payload
        )

    async def delete(self, schedule_id: str) -> None:
        await self.database.request(
            "DELETE", "schedules", params={"id": f"eq.{schedule_id}"}
        )

    async def run_due(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        due = await self.database.request(
            "GET",
            "schedules",
            params={
                "select": "*",
                "is_active": "eq.true",
                "next_run_at": f"lte.{now.isoformat()}",
            },
        )
        executions = []
        for schedule in due:
            previous_run = self._previous_run(schedule, now)
            elapsed_hours = max(
                1,
                min(720, math.ceil((now - previous_run).total_seconds() / 3600)),
            )
            try:
                search, mentions, errors = await monitoring_search_service.execute(
                    schedule["monitoring_id"],
                    elapsed_hours,
                    published_after=previous_run,
                )
                monitoring = await monitoring_search_service.get_monitoring(
                    schedule["monitoring_id"]
                )
                clipping = None
                if mentions:
                    items = [
                        {
                            "source": mention.source,
                            "title": mention.title,
                            "url": str(mention.url),
                            "term": mention.matched_term or mention.searched_term,
                            "published_at": mention.published_at.isoformat()
                            if mention.published_at
                            else None,
                            "excerpt": mention.excerpt,
                            "sentiment": None,
                        }
                        for mention in mentions
                    ]
                    local_now = now.astimezone(
                        ZoneInfo(schedule.get("timezone") or "America/Fortaleza")
                    )
                    monitoring_name = (
                        monitoring.get("name") if monitoring else "Clipping automático"
                    )
                    client = monitoring.get("clients") if monitoring else None
                    clipping = await clipping_service.create(
                        title=f"{monitoring_name} — {local_now.strftime('%d/%m/%Y')}",
                        items=items,
                        monitoring_id=schedule["monitoring_id"],
                        search_id=search["id"],
                        client_name=client.get("name") if client else None,
                        monitoring_name=monitoring_name,
                    )
                executions.append(
                    {
                        "schedule_id": schedule["id"],
                        "search_id": search["id"],
                        "clipping_id": clipping.get("id") if clipping else None,
                        "results": len(mentions),
                        "searched_since": previous_run.isoformat(),
                        "errors": errors,
                    }
                )
            finally:
                next_run = self._next_run(schedule, after=now + timedelta(minutes=1))
                active = not schedule.get("end_date") or (
                    next_run.astimezone(
                        ZoneInfo(schedule.get("timezone") or "America/Fortaleza")
                    ).date().isoformat()
                    <= schedule["end_date"]
                )
                await self.database.request(
                    "PATCH",
                    "schedules",
                    params={"id": f"eq.{schedule['id']}"},
                    json={
                        "last_run_at": now.isoformat(),
                        "next_run_at": next_run.isoformat(),
                        "is_active": active,
                    },
                )
        return executions

    def _previous_run(self, schedule: dict, now: datetime) -> datetime:
        raw = schedule.get("last_run_at") or schedule.get("created_at")
        if raw:
            parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return min(parsed.astimezone(timezone.utc), now)
        return now - timedelta(hours=24)

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
        return candidate.astimezone(timezone.utc)


schedule_service = ScheduleService()
