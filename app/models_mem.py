from abc import ABC, abstractmethod
from datetime import datetime, timezone
import inspect
import logging
import re
import simplejson as json
from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Type, Tuple

# project imports and definitions
logger = logging.getLogger("sanic.root.exch")

# --------------------------------------------------------------------------------------------

class OurBaseMemoryModel(ABC):

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.compare_fields(other)

    def __lt__(self, other):
        """__lt__ is used by sort() and sorted() to compare two objects"""
        return self.pk < other.pk

    def __repr__(self):
        field_names = self.get_field_names()
        field_values = {field: getattr(self, field) for field in field_names}
        return f"<{self.__class__.__name__}({', '.join(f'{key}={value}' for key, value in field_values.items())})>"

    def __str__(self):
        return str(self.dict_blacken())

    @classmethod
    def classmethodname(cls):
        # use cls.classmethodname() for debug logs
        return f"{cls.__name__}.{inspect.currentframe().f_back.f_code.co_name}" 

    def compare(self, other):
        return self.__dict__ == other.__dict__

    def compare_fields(self, other, exclude_fields=[]) -> Dict[str, Any]:
        same_same = True
        # Verify that we compare objects of the same class
        if not isinstance(other, self.__class__):
            raise TypeError(f"Cannot compare objects of different classes ({self.__class__.__name__} vs {other.__class__.__name__}).")
        # Compare all fields
        for field in self.model_fields.keys():
            if field not in exclude_fields and getattr(self, field) != getattr(other, field):
                logger.debug(f"{self.instmethodname()}: compare_fields() failed for field {field}={getattr(self, field)}")
                same_same = False
        return same_same
    
    def compare_properties(self, other, exclude_properties=[]) -> Dict[str, Any]:
        same_same = True
        # Verify that we compare objects of the same class
        if not isinstance(other, self.__class__):
            raise TypeError(f"Cannot compare objects of different classes ({self.__class__.__name__} vs {other.__class__.__name__}).")
        # Get all property names by inspecting the class
        properties = [p for p in dir(self.__class__) if isinstance(getattr(self.__class__, p), property) and p not in exclude_properties]
        
        # Compare all properties
        for prop in properties:
            if getattr(self, prop) != getattr(other, prop):
                logger.debug(f"{self.instmethodname()}: compare_properties() failed for property {prop}={getattr(self, prop)}")
                same_same = False
        return same_same

    def dict_blacken(self, blacken_keys: List[str]=['password', 'passphrase']) -> Dict[str, Any]:
        dict_copy = {}
        for attr_key in self.model_fields.keys():
            if attr_key in blacken_keys:
                dict_copy[attr_key] = "XXXXXXXXXX"
            else:
                dict_copy[attr_key] = getattr(self, attr_key)
        return dict_copy

    @classmethod
    def get_all_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_all_subclasses())
        return all_subclasses

    def find(self, query):
        return [item for item in self if item.compare(query)]
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str, indent=4, sort_keys=True, default=str, use_decimal=True)
        return cls(**data)

    def instmethodname(self):
        return f"{self.__class__.__name__}.{inspect.currentframe().f_back.f_code.co_name}"
 
    def keys(self):
        return [attr for attr in self.__dict__ if not attr.startswith('_')] 

    def match_criteria(self, **kwargs) -> bool:
        # supported:
        #   - plain matching: use {key: 'value'}
        #   - REGEX string matching: add argument { key: { 'regex': pattern }}
        #   - MEMBER OF list: add argument {key: { 'in': [value1, value2, ...] }}
        #   - numeric comparison: add argument {key: {OP: value}} where OP is one of '$gt', '$lt', '$ge', '$le'
        #   - multiple key-value pairs: all must match
        for key, value in kwargs.items():
            logger.debug(f"{self.instmethodname()}: match_criteria() called with key {key}={value}")
            if type(key) != str:
                raise TypeError(f"{self.instmethodname()}: match key must be of type str but is a {type(key)}: {str(key)}")
            if key not in self.__dict__:
                raise ValueError(f"{self.instmethodname()}: match_criteria() called with invalid key {key}")
            if type(value) == dict:
                if '$gt' in value and getattr(self, key) <= value['$gt']:
                    return False
                elif '$lt' in value and getattr(self, key) >= value['$lt']:
                    return False
                elif '$ge' in value and getattr(self, key) < value['$ge']:
                    return False
                elif '$le' in value and getattr(self, key) > value['$le']:
                    return False
                elif 'regex' in value and not re.match(value['regex'], getattr(self, key)):
                    return False
                elif '$has_element' in value and value['$has_element'] not in getattr(self, key) and "*" not in getattr(self, key):
                    return False
                elif '$in' in value and getattr(self, key) not in value['$in']:
                    return False
            elif getattr(self, key) != value:
                # db_logger.debug(f"{self.instmethodname()}: match_criteria() failed for key {key}={value}")
                return False
        return True

    def modify(self, other) -> bool:
        was_modified = False
        if not isinstance(other, self.__class__):
            raise TypeError(f"Cannot compare objects of different classes ({self.__class__.__name__} vs {other.__class__.__name__}).")
        for field in self.keys():
            if getattr(other, field) is not None and getattr(self, field) != getattr(other, field):
                setattr(self, field, getattr(other, field))
                was_modified = True
        return was_modified

    @property
    def pk(self):
        return self.primary_key
    
    @property
    @abstractmethod
    def primary_key(self):
        pass

    def to_json(self):
        return json.dumps(self.__dict__, indent=4, sort_keys=True, default=str, use_decimal=True)

class Position(OurBaseMemoryModel):
    pass

class Trade(OurBaseMemoryModel):
    pass

class Order(OurBaseMemoryModel):
    pass

class Exchange(OurBaseMemoryModel):
    pass

# --------------------------------------------------------------------------------------------

class OurBaseList(List):
    def __init__(self, items: List[OurBaseMemoryModel]=[], item_type: Type[OurBaseMemoryModel]=OurBaseMemoryModel):
        for item in items:
            if not isinstance(item, item_type):
                raise TypeError(f"{self.__class__.__name__} can only contain {item_type.__name__} objects, not {type(item)}")
        self.item_type = item_type
        super().__init__(items)

    def append(self, item: OurBaseMemoryModel):
        if not isinstance(item, self.item_type):
            raise TypeError(f"{self.__class__.__name__} can only contain {self.item_type.__name__} objects, not {type(item)}")
        super().append(item)

    def insert(self, index: int, item: OurBaseMemoryModel):
        if not isinstance(item, self.item_type):
            raise TypeError(f"{self.__class__.__name__} can only contain {self.item_type.__name__} objects, not {type(item)}")
        super().insert(index, item)

    def find_by_match_criteria(self, **kwargs) -> 'OurBaseList':
        match_list = OurBaseList(item_type=self.item_type)
        for item in self:
            if item.match_criteria(**kwargs):
                match_list.append(item)
        return match_list

    def remove_pk(self, primary_key) -> None:
        """only delete the first occurrence of the primary key
            use List.remove() to remove an item (uses __eq__)
        """
        for item in range(len(self)):
            if self[item].pk == primary_key:
                del self[item]
                return  

    def remove_pks(self, primary_keys) -> None:
        for primary_key in primary_keys:
            self.remove_pk(primary_key)

    def modify(self, other_list):
        was_modified = False
        pk_index = {}
        for self_index in range(len(self)):
            pk_index[self[self_index].pk] = {'self': self_index}
        for other_list_index in range(len(other_list)):
            pk = other_list[other_list_index].pk
            if pk in pk_index:
                pk_index[pk]['other'] = other_list_index
            else:
                pk_index[pk] = {'other': other_list_index}
        for pk, index_dict in pk_index.items():
            if 'self' in index_dict and 'other' in index_dict:
                was_modified |= self[index_dict['self']].modify(other_list[index_dict['other']])
        return was_modified

    def subtract(self, other_list):
        for item in other_list:
            self.remove_pk(item.pk)

    def pks(self):
        return [item.pk for item in self]

class PositionList(OurBaseList):
    def __init__(self, positions: List[Position]=[]):
        super().__init__(positions, Position)

class TradeList(OurBaseList):
    def __init__(self, trades: List[Trade]=[]):
        super().__init__(trades, Trade)

class OrderList(OurBaseList):
    def __init__(self, orders: List[Order]=[]):
        super().__init__(orders, Order)

class ExchangeList(OurBaseList):
    def __init__(self, exchanges: List[Exchange]=[]):
        super().__init__(exchanges, Exchange)