from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String(255))
    order_id = Column(String(255))
    action = Column(String(50))
    ticker = Column(String(50))
    price = Column(Numeric)
    quantity = Column(Numeric)
    received_at = Column(TIMESTAMP, default=datetime.utcnow)
