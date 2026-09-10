from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from OpenDEMON.database.models import AuditLog

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(self, user_id: Optional[str], action: str, resource_type: str, resource_id: Optional[str] = None, details: Optional[str] = None, ip_address: Optional[str] = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        self.session.add(log)
        await self.session.commit()
        return log
