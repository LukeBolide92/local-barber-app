from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    collaborator_id: Mapped[int] = mapped_column(ForeignKey("collaborators.id"))
    date: Mapped[DateTime] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)