from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import ScheduledTask, TaskRun

class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, user_id: str, name: str, schedule_cron: str, action_type: str, action_payload: str) -> ScheduledTask:
        task = ScheduledTask(
            user_id=user_id,
            name=name,
            schedule_cron=schedule_cron,
            action_type=action_type,
            action_payload=action_payload
        )
        self.session.add(task)
        await self.session.commit()
        return task
