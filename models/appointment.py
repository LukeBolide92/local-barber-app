from datetime import date, time, datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Date, Time, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base

if TYPE_CHECKING:
    from models.client import Client
    from models.service import Service
    from models.collaborator import Collaborator


class Appointment(Base):
    __tablename__ = "appointments"

    # Stati possibili dell'appuntamento
    STATUS_BOOKED = "BOOKED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_NO_SHOW = "NO_SHOW"
    VALID_STATUSES = (
        STATUS_BOOKED,
        STATUS_COMPLETED,
        STATUS_CANCELLED,
        STATUS_NO_SHOW,
    )

    # Stati del pagamento associato all'appuntamento
    PAYMENT_UNPAID = "UNPAID"
    PAYMENT_PAID = "PAID"
    PAYMENT_REFUNDED = "REFUNDED"
    VALID_PAYMENT_STATUSES = (
        PAYMENT_UNPAID,
        PAYMENT_PAID,
        PAYMENT_REFUNDED,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    collaborator_id: Mapped[int] = mapped_column(ForeignKey("collaborators.id"))
    date: Mapped[date] = mapped_column(Date)
    time: Mapped[time] = mapped_column(Time)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Stato dell'appuntamento (default: BOOKED)
    status: Mapped[str] = mapped_column(
        String(20), default=STATUS_BOOKED, nullable=False
    )

    # Pagamenti
    payment_status: Mapped[str] = mapped_column(
        String(10), default="UNPAID", nullable=False
    )
    amount_paid: Mapped[float | None] = mapped_column(Float, nullable=True)
    payment_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=True)

    # Valori originari del servizio al momento della prenotazione.
    # Vengono conservati anche se il servizio viene successivamente modificato.
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    client: Mapped[Client] = relationship("Client", back_populates="appointments")
    service: Mapped[Service] = relationship("Service", back_populates="appointments")
    collaborator: Mapped[Collaborator] = relationship(
        "Collaborator", back_populates="appointments"
    )