from datetime import datetime, timezone

from app.database import get_database
from app.services.search_service import search_mentions


class MonitoringSearchService:
    def __init__(self) -> None:
        self.database = get_database()

    async def get_monitoring(self, monitoring_id: str) -> dict | None:
        rows = await self.database.request(
            "GET", "monitorings",
            params={"select": "*,clients(id,name)", "id": f"eq.{monitoring_id}", "limit": "1"},
        )
        return rows[0] if rows else None

    async def list_terms(self, monitoring_id: str) -> list[dict]:
        return await self.database.request(
            "GET", "terms",
            params={"select": "*", "monitoring_id": f"eq.{monitoring_id}", "order": "is_primary.desc,created_at.asc"},
        )

    async def add_term(self, monitoring_id: str, text: str, is_primary: bool) -> dict:
        if is_primary:
            await self.database.request(
                "PATCH", "terms",
                params={"monitoring_id": f"eq.{monitoring_id}", "is_primary": "eq.true"},
                json={"is_primary": False},
            )
        rows = await self.database.request(
            "POST", "terms",
            json={"monitoring_id": monitoring_id, "text": text.strip(), "is_primary": is_primary},
            prefer="return=representation",
        )
        return rows[0]

    async def update_term(self, term_id: str, text: str) -> dict:
        rows = await self.database.request(
            "PATCH", "terms", params={"id": f"eq.{term_id}"},
            json={"text": text.strip()}, prefer="return=representation",
        )
        return rows[0]

    async def set_term_active(self, term_id: str, is_active: bool) -> dict:
        rows = await self.database.request(
            "PATCH", "terms", params={"id": f"eq.{term_id}"},
            json={"is_active": is_active}, prefer="return=representation",
        )
        return rows[0]

    async def delete_term(self, term_id: str) -> None:
        await self.database.request("DELETE", "terms", params={"id": f"eq.{term_id}"})

    async def execute(self, monitoring_id: str, period_hours: int) -> tuple[dict, list, list[str]]:
        terms = await self.list_terms(monitoring_id)
        active_terms = [term["text"] for term in terms if term.get("is_active")]
        if not active_terms:
            raise ValueError("Cadastre e ative ao menos um termo antes de pesquisar.")

        rows = await self.database.request(
            "POST", "searches",
            json={"monitoring_id": monitoring_id, "period_hours": period_hours, "status": "running"},
            prefer="return=representation",
        )
        search = rows[0]
        try:
            mentions, errors = await search_mentions(active_terms, period_hours)
            if mentions:
                payload = [{
                    "search_id": search["id"],
                    "media_type": mention.media_type.value,
                    "source": mention.source,
                    "title": mention.title,
                    "url": str(mention.url),
                    "published_at": mention.published_at.isoformat() if mention.published_at else None,
                    "excerpt": mention.excerpt,
                    "searched_term": mention.searched_term,
                    "matched_term": mention.matched_term,
                } for mention in mentions]
                await self.database.request("POST", "results", json=payload)

            status = "partial" if errors else "completed"
            updated = await self.database.request(
                "PATCH", "searches", params={"id": f"eq.{search['id']}"},
                json={
                    "status": status,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "result_count": len(mentions),
                    "error_message": " | ".join(errors) if errors else None,
                }, prefer="return=representation",
            )
            return updated[0], mentions, errors
        except Exception as exc:
            await self.database.request(
                "PATCH", "searches", params={"id": f"eq.{search['id']}"},
                json={"status": "failed", "finished_at": datetime.now(timezone.utc).isoformat(), "error_message": str(exc)},
            )
            raise


monitoring_search_service = MonitoringSearchService()
