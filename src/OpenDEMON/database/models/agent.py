from sqlalchemy import String, DateTime, func, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String)
    result: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)

class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    agent_run_id: Mapped[str] = mapped_column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tool_name: Mapped[str] = mapped_column(String)
    arguments: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
