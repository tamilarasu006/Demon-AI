from sqlalchemy import String, DateTime, func, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    schedule_cron: Mapped[str] = mapped_column(String)
    action_type: Mapped[str] = mapped_column(String)
    action_payload: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("scheduled_tasks.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=True)
