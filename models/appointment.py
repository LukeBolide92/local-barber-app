from datetime import date, time
from sqlalchemy import String, ForeignKey, Date, Time, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    collaborator_id: Mapped[int] = mapped_column(ForeignKey("collaborators.id"))
    date: Mapped[date] = mapped_column(Date)
    time: Mapped[time] = mapped_column(Time)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    client: Mapped[Client] = relationship("Client", back_populates="appointments")
    service: Mapped[Service] = relationship("Service", back_populates="appointments")
    collaborator: Mapped[Collaborator] = relationship("Collaborator", back_populates="appointments")