from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog

SORT_FIELDS = {
    "action": AuditLog.action,
    "entity_type": AuditLog.entity_type,
    "entity_id": AuditLog.entity_id,
    "user_id": AuditLog.user_id,
    "created_at": AuditLog.created_at,
}


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, audit_log: AuditLog) -> AuditLog:
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def list(
        self,
        tenant_id: int,
        *,
        offset: int,
        limit: int,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        user_id: int | None = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        base_stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

        if action:
            base_stmt = base_stmt.where(AuditLog.action == action)
        if entity_type:
            base_stmt = base_stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            base_stmt = base_stmt.where(AuditLog.entity_id == entity_id)
        if user_id is not None:
            base_stmt = base_stmt.where(AuditLog.user_id == user_id)

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        sort_column = SORT_FIELDS.get(sort, AuditLog.created_at)
        if order == "asc":
            base_stmt = base_stmt.order_by(sort_column.asc(), AuditLog.id.asc())
        else:
            base_stmt = base_stmt.order_by(sort_column.desc(), AuditLog.id.desc())

        base_stmt = base_stmt.offset(offset).limit(limit)
        result = await self.session.execute(base_stmt)
        items = list(result.scalars().all())

        return items, total
