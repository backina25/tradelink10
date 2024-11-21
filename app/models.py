from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String(255))
    order_id = Column(String(255))
    action = Column(String(50))
    symbol = Column(String(50))
    price = Column(Numeric)
    quantity = Column(Numeric)
    received_at = Column(TIMESTAMP, default=lambda: datetime.now(datetime.timezone.utc))

    def __repr__(self):
        field_names = self.get_field_names()
        field_values = {field: getattr(self, field) for field in field_names}
        return f"<Signal({', '.join(f'{key}={value}' for key, value in field_values.items())})>"
    
    @classmethod
    def get_field_names(cls):
            return [column.name for column in cls.__table__.columns]
    
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)