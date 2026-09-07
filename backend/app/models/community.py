import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Community(Base):
    __tablename__ = "communities"
    __table_args__ = (
        CheckConstraint(
            "type IN ('college', 'hostel', 'apartment_society', 'corporate_campus')",
            name="ck_communities_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(32))
    city: Mapped[str] = mapped_column(String(120), index=True)
    invite_code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    members: Mapped[list["User"]] = relationship(back_populates="community")
