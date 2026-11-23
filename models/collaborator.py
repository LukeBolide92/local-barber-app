from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Collaborator(Base):
    __tablename__ = "collaborators"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(50))
    availability: Mapped[int] = mapped_column(Integer)  # 1 = active, 0 = inactive