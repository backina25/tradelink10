from datetime import datetime, timezone
import logging
import simplejson as json
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, DECIMAL
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

logger = logging.getLogger("sanic.root.webhook")

class OurBaseDBModel(Base):
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
        data = json.loads(json_str, use_decimal=True)
        return cls(**data)

    @classmethod
    def get_field_names(cls):
            return [column.name for column in cls.__table__.columns]

    async def insert(self, session: AsyncSession):
        session.add(self)
        await session.commit()

    def to_dict(self):
        logger.debug(f"to_dict: {self.__dict__}")
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def to_json(self):
        logger.debug(f"to_json: {self.to_dict()}")
        return json.dumps(self.to_dict(), use_decimal=True)

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

class Signal(OurBaseDBModel):
    __tablename__ = "signals"

    id            = Column(Integer, primary_key=True, index=True)
    strategy      = Column(String(255))
    order_id      = Column(String(255))
    action        = Column(String(50))
    symbol        = Column(String(50))
    price         = Column(DECIMAL)
    quantity      = Column(DECIMAL)
    received_at   = Column(TIMESTAMP, default=datetime.now)

class Account(OurBaseDBModel):
    __tablename__ = "accounts"

    name = Column(String(255), primary_key=True, index=True)
    exchange_id = Column(String(255))
    modified_at   = Column(TIMESTAMP, default=datetime.now)

class WebSource(OurBaseDBModel):
    __tablename__ = "websources"

    source_name   = Column(String(255), primary_key=True, index=True)
    password_seed = Column(String(255))
    ok_ips        = Column(String(255))
    ok_routes     = Column(String(255))
    ok_strategies = Column(String(255))
    modified_at   = Column(TIMESTAMP, default=datetime.now)