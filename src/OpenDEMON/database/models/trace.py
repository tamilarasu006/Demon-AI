from sqlalchemy import String, DateTime, func, ForeignKey, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from OpenDEMON.database.base import Base, uuid_gen

class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    trace_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    query: Mapped[str] = mapped_column(Text, default="")
    agent: Mapped[str] = mapped_column(String, default="")
    model: Mapped[str] = mapped_column(String, default="")
    engine: Mapped[str] = mapped_column(String, default="")
    result: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(String, nullable=True)
    feedback: Mapped[float] = mapped_column(Float, nullable=True)
    started_at: Mapped[float] = mapped_column(Float, default=0.0)
    ended_at: Mapped[float] = mapped_column(Float, default=0.0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    messages_json: Mapped[str] = mapped_column(Text, default="[]")
    
class TraceStep(Base):
    __tablename__ = "trace_steps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_gen)
    trace_id: Mapped[str] = mapped_column(String, ForeignKey("traces.trace_id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    step_index: Mapped[int] = mapped_column(Integer)
    step_type: Mapped[str] = mapped_column(String)
    timestamp: Mapped[float] = mapped_column(Float, default=0.0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    output_json: Mapped[str] = mapped_column(Text, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
