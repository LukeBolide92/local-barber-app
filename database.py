from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Engine placeholder (commented out until FASE 2)
# engine = create_engine("sqlite:///barber.db", echo=True)
# Base.metadata.create_all(engine)