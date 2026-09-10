from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from OpenDEMON.database.models import Agent, AgentRun, ToolCall

class AgentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent(self, user_id: str, name: str, description: str = "", system_prompt: str = "") -> Agent:
        agent = Agent(user_id=user_id, name=name, description=description, system_prompt=system_prompt)
        self.session.add(agent)
        await self.session.commit()
        return agent

    async def start_run(self, agent_id: str, user_id: str) -> AgentRun:
        run = AgentRun(agent_id=agent_id, user_id=user_id, status="running")
        self.session.add(run)
        await self.session.commit()
        return run
