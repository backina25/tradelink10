from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession

Base = declarative_base()

class MyBase(Base):
    __abstract__ = True  # This ensures that this class is not mapped to a table

    def __repr__(self):
        field_names = self.get_field_names()
        field_values = {field: getattr(self, field) for field in field_names}
        return f"<Signal({', '.join(f'{key}={value}' for key, value in field_values.items())})>"

    async def delete(self, session: AsyncSession):
        async with session.begin():
            await session.delete(self)
            await session.commit()

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def get_field_names(cls):
            return [column.name for column in cls.__table__.columns]

    async def insert(self, session: AsyncSession):
        async with session.begin():
            session.add(self)
            await session.commit()

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def to_json(self):
        return json.dumps(self.to_dict())

    async def upsert(self, session: AsyncSession):
        async with session.begin():
            db_instance = await session.get(self.__class__, self.id)
            if db_instance:
                for key, value in self.to_dict().items():
                    setattr(db_instance, key, value)
                await session.commit()
            else:
                session.add(self)
                await session.commit()

class Signal(MyBase):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String(255))
    order_id = Column(String(255))
    action = Column(String(50))
    symbol = Column(String(50))
    price = Column(Numeric)
    quantity = Column(Numeric)
    received_at = Column(TIMESTAMP, default=datetime.now)


# from sqlalchemy.types import TIMESTAMP
# sel = select([User.id, bindparam("timestamp", datetime.datetime.now(datetime.timezone.utc), type_=TIMESTAMP(timezone=True))])