from datetime import datetime, timezone
import uuid
from typing import Any
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass

def utcnow():
    return datetime.now(timezone.utc)

def uuid_gen():
    return str(uuid.uuid4())
