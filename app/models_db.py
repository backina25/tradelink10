from datetime import datetime, timezone
from decimal import Decimal
import logging
import simplejson as json
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, DECIMAL
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base

# project imports
from app.utils.serializer import datetime_serializer

# project definitions and globals
Base = declarative_base()
logger = logging.getLogger("sanic.root.webhook")

# ------------------------------------------------------------------------------

class OurBaseDBModel(Base):
    __abstract__ = True  # This ensures that this class is not mapped to a table

    def __repr__(self):
        field_names = self.get_field_names()
        field_values = {field: getattr(self, field) for field in field_names}
        return f"<{self.__class__.__name__}({', '.join(f'{key}={value}' for key, value in field_values.items())})>"

    async def delete(self, session: AsyncSession):
        async with session.begin():
            await session.delete(self)
            await session.commit()

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str = None):
        if json_str is None:
            raise ValueError("{cls.__name__}.from_json(): json_str is None")
        try:
            data = json.loads(json_str, use_decimal=True)
        except Exception as e:
            raise ValueError(f"{cls.__name__}.from_json(): failed to parse JSON: {e}")
        return cls(**data)

    @classmethod
    def get_subclass_from_tablename(cls, tablename):
        for cls in cls.get_all_subclasses():
            if cls.__tablename__ == tablename:
                return cls
        return None

    @classmethod
    def get_field_names(cls):
        return [column.name for column in cls.__table__.columns]

    @classmethod
    def get_field_type(cls, field_name):
        return cls.__table__.columns[field_name].type

    @classmethod
    def get_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_all_subclasses())
        return all_subclasses

    async def insert(self, session: AsyncSession):
        session.add(self)
        await session.commit()

    @property
    def pk(self):
        return self.id
    
    @classmethod
    def get_tablename(cls):
        return cls.__tablename__
    
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns if column.name[0] != "_"}

    def to_json(self):
        inst_as_dict = self.to_dict()
        return json.dumps(inst_as_dict, indent=4, sort_keys=True, default=datetime_serializer, use_decimal=True)

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

class Account(OurBaseDBModel):
    __tablename__ = "accounts"

    name = Column(String(255), primary_key=True, index=True)
    exchange_id = Column(String(255))
    modified_at   = Column(TIMESTAMP, default=datetime.now)

    @property
    def pk(self):
        return self.name

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

    @property
    def pk(self):
        return getattr(self, self.pk_field_name)
    
    @property
    def pk_field_name(self):
        return next((key.name for key in self.__table__.primary_key), None)

class WebSource(OurBaseDBModel):
    __tablename__ = "websources"

    source_name   = Column(String(255), primary_key=True, index=True)
    password_seed = Column(String(255))
    ok_ips        = Column(String(255))
    ok_routes     = Column(String(255))
    ok_strategies = Column(String(255))
    modified_at   = Column(TIMESTAMP, default=datetime.now)

    @property
    def pk(self):
        return self.source_name
