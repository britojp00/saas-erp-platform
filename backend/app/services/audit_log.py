from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuditLogRepository(session)

    async def log(
        self,
        *,
        tenant_id: int,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        user_id: int | None = None,
        description: str | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
        )
        return await self.repo.create(audit_log)

    async def list(
        self,
        tenant_id: int,
        *,
        page: int,
        page_size: int,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        user_id: int | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        offset = (page - 1) * page_size
        return await self.repo.list(
            tenant_id,
            offset=offset,
            limit=page_size,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            sort=sort,
            order=order,
        )
