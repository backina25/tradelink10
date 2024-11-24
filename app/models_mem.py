from abc import ABC, abstractmethod
from datetime import datetime, timezone
import inspect
import logging
import re
import simplejson as json
from typing import Any, ClassVar, Dict, List, Optional, TypeVar, Type, Tuple

# project imports and definitions
from app.models_db import Account, Signal, WebSource
from app.utils.serializer import datetime_serializer

# project definitions and globals
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
        return str(self.to_dict_blacken())

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
        for field in self.get_field_names():
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

    @classmethod
    def get_all_subclasses(cls):
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(subclass.get_all_subclasses())
        return all_subclasses

    def get_field_names(self):
        return [attr for attr in self.__dict__ if not attr.startswith('_')]

    def find(self, query):
        return [item for item in self if item.compare(query)]

    @classmethod
    def from_json(cls, json_str: str = None):
        logprefix = f"{cls.__name__}.from_json(): "
        if json_str is None or json_str == "":
            raise ValueError(f"{logprefix}requires a JSON string (got {str(json_str)})")
        try:
            dict_from_json = json.loads(json_str, use_decimal=True)
        except Exception as e:
            raise ValueError(f"{logprefix}failed to parse JSON: {e}")
        # logger.debug(f"{logprefix}: dict_from_json={dict_from_json}")
        return cls(**dict_from_json)

    def instmethodname(self):
        return f"{self.__class__.__name__}.{inspect.currentframe().f_back.f_code.co_name}"
 
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
        for field in self.get_field_names():
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

    def to_dict(self):
        return {attr: getattr(self, attr) for attr in self.get_field_names()}

    def to_dict_blacken(self, blacken_keys: List[str]=['password', 'passphrase']) -> Dict[str, Any]:
        dict_copy = {}
        for attr_key in self.get_field_names():
            if attr_key in blacken_keys:
                dict_copy[attr_key] = "XXXXXXXXXX"
            else:
                dict_copy[attr_key] = getattr(self, attr_key)
        return dict_copy

    def to_json(self):
        inst_as_dict = self.to_dict()
        logger.debug(f"{self.instmethodname()}: to_json()[1]: inst_as_dict={inst_as_dict}")
        json_str = json.dumps(inst_as_dict, indent=4, sort_keys=True, default=datetime_serializer, use_decimal=True)
        logger.debug(f"{self.instmethodname()}: to_json()[2: json_str={json_str}")
        return json_str

# --------------------------------------------------------------------------------------------

class Position(OurBaseMemoryModel):
    pass

class Trade(OurBaseMemoryModel):
    pass

class Order(OurBaseMemoryModel):
    pass

class Exchange(OurBaseMemoryModel):
    pass


# --------------------------------------------------------------------------------------------
class OurGenericList(List):
    # Special list where the first item determines the type of the list! Once an elemnt
    # is added to the list, all subsequent items must be of the same type. Once the
    # item type is set, it cannot be changed.
    #
    # Items MAY support the following methods:
    #   - __eq__()          # used to compare objects for equality
    #   - __lt__()          # used for sorting the list
    #
    # Items MUST support the following methods:
    _methods_required_by_item_class = [ "from_json", "match_criteria", "modify", "pk", "to_json" ]

    def __init__(self, *args, force_item_class=None):
        # logger.debug(f"{self.__class__.__name__}.__init__(): args={args}, force_item_class={force_item_class}")
        if len(args) > 1:
            raise ValueError(f"{self.__class__.__name__} can only be called with a single list argument, not {len(args)}")
        if len(args) == 1 and type(args[0]) != list:
            raise ValueError(f"{self.__class__.__name__} argument must be a list, not {type(args[0])}")

        # set item_class (either explicitly or by the first item in the list)
        self.item_class = None    
        if force_item_class is not None:
            if not inspect.isclass(force_item_class):
                raise ValueError(f"{self.__class__.__name__} requires the force_item_class argument to be a class, not {type(force_item_class)}")
            self.item_class = force_item_class
        if len(args) == 1:
            if type(args[0][0]) == dict and force_item_class is None:
                raise ValueError(f"{self.__class__.__name__} requires the force_item_class argument if it is given a list of dict items (got None)")
            if force_item_class is None:
                self.item_class = type(args[0][0])

        # allow empty list
        if len(args) == 0:
            super().__init__()
            return
        
        obj_list = []
        if len(args) > 1:
            raise ValueError(f"{self.__class__.__name__} can only be called with a single list argument, not {len(args)}")
        if type(args[0]) != list:
            raise ValueError(f"{self.__class__.__name__} argument must be a list, not {type(args[0])}")
        # the constructor accepts...
        #   1) items with a class having the required methods
        #   2) items of type dict if force_item_class is given
        for item in args[0]:
            if isinstance(item, self.item_class):
                obj_list.append(item)
            elif type(item) == dict:
                item_obj = self.item_class(**item)
                obj_list.append(item_obj)
            else:
                raise TypeError(f"{self.__class__.__name__} can only contain {self.item_class.__name__} objects, not {type(item)}")
        super().__init__(obj_list)

    def setattr(self, key, value):
        if key == "item_class":
            for method in self.__class__._methods_required_by_item_class:
                if not hasattr(value, method):
                    raise ValueError(f"{self.__class__.__name__} wanted {key} {value.__name__} misses required method {method}")
        super().__setattr__(key, value)

    def append(self, item):
        if self.item_class is None:
            self.item_class = type(item)
        if not isinstance(item, self.item_class):
            raise TypeError(f"{self.__class__.__name__} can only contain {self.item_class.__name__} objects, not {type(item)}")
        # logger.debug(f"{self.__class__.__name__}.append(): appending item of type {type(item)}: {item}")
        super().append(item)

    @classmethod
    def from_dict(cls, given_dict: dict):
        logprefix = f"{cls.__name__}.from_dict(): "

        # logger.debug(f"{logprefix}given_dict={given_dict}")

        # verify given_dict
        if given_dict is None:
            raise ValueError(f"{logprefix}requires a dict (got None)")
        if "item_class" not in given_dict:
            raise ValueError(f"{logprefix}missing item_class in dict")
        if "items" not in given_dict:
            raise ValueError(f"{logprefix}missing items in dict")
        # set item_class
        if given_dict["item_class"] is None:
            raise ValueError(f"{logprefix}item_class is None (explicitly set to None)")
        if type(given_dict["items"]) != list:
            raise ValueError(f"{logprefix}items is not a list")

        # get item class (either as class or as classname)
        if type(given_dict["item_class"]) == str:
            if given_dict["item_class"] not in globals():
                raise ValueError(f"{logprefix}item class {given_dict['item_class']} not found")
            item_class = globals()[given_dict["item_class"]]
        else:
            item_class = given_dict["item_class"]

        # call constructor (which will do more checks)
        # logger.debug(f"{logprefix}calling constructor with: item_class={item_class}, items={given_dict['items']} and first item type={type(given_dict['items'][0])}")
        return cls(given_dict["items"], force_item_class=item_class)
        
    @classmethod
    def from_json(cls, json_str: str):
        logprefix = f"{cls.__name__}.from_json(): "
        if json_str is None or json_str == "":
            raise ValueError(f"{logprefix}requires a JSON string (got {str(json_str)})")
        # logger.debug(f"{logprefix}json_str={json_str}")
        dict_from_json = json.loads(json_str, use_decimal=True)
        # logger.debug(f"{logprefix}type(dict_from_json)={type(dict_from_json)}, list_from_json={dict_from_json}")
        return cls.from_dict(dict_from_json)

    def insert(self, index: int, item):
        if self.item_class is None:
            self.item_class = type(item)
        if not isinstance(item, self.item_class):
            raise TypeError(f"{self.__class__.__name__} can only contain {self.item_class.__name__} objects, not {type(item)}")
        super().insert(index, item)

    def find_by_match_criteria(self, **kwargs):
        match_list = self.__class__()
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
        if not isinstance(other_list, self.__class__):
            raise TypeError(f"{self.__class__.__name__}.modify() can only be called with a {self.__class__.__name__} object, not {type(other_list)}")
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
        if not isinstance(other_list, self.__class__):
            raise TypeError(f"{self.__class__.__name__}.subtract() can only be called with a {self.__class__.__name__} object, not {type(other_list)}")
        for item in other_list:
            self.remove_pk(item.pk)

    def to_dict(self):
        for item in self:
            if not hasattr(item, "to_dict"):
                raise ValueError(f"{self.__class__.__name__} item of type {item.__class__.__name__} misses method to_dict(): {item}")
        return { "item_class": self.item_class.__name__, "items": [item.to_dict() for item in self] }

    def to_json(self):
        list_dict = self.to_dict()
        return json.dumps(list_dict, indent=4, sort_keys=True, default=datetime_serializer, use_decimal=True)

    def pks(self):
        return [item.pk for item in self]

    pass