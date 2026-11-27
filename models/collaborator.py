from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base

if TYPE_CHECKING:
    from models.appointment import Appointment


class Collaborator(Base):
    __tablename__ = "collaborators"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50))
    availability: Mapped[int] = mapped_column(Integer)  # 1 = active, 0 = inactive
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    work_days: Mapped[str] = mapped_column(String, nullable=True)  # JSON serialized list

    # Relationships
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="collaborator")