from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)