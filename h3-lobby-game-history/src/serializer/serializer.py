import inspect
import io
from dataclasses import is_dataclass, fields
from typing import Annotated, get_origin, get_args
from typing import TypeVar, Type
from serializer.types import registered_types


T = TypeVar('T')


class SerializerError(Exception):
    pass


def parse(dataclass: Type[T], data: bytes) -> T:
    reader = io.BytesIO(data)
    return __parse(reader, dataclass)


def parse_field(reader, curr_cls_args, field_type):
    ret = None

    if field_type in registered_types:
        b = reader.read(field_type.SIZE // 8)
        ret = field_type().from_raw(b)

    elif inspect.isclass(field_type) and is_dataclass(field_type):
        ret = __parse(reader, field_type)

    elif get_origin(field_type) == Annotated:
        args = get_args(field_type)
        arg_type, length = args

        # if length is a string, then we are referencing a concrete field
        if isinstance(length, str):
            length = curr_cls_args[length].v

        if arg_type == bytes:
            ret = reader.read(length)

        elif get_origin(arg_type) == list:
            elem_type, *_ = get_args(arg_type)
            ret = [parse_field(reader, curr_cls_args, elem_type) for _ in range(length)]

    return ret


def __parse(reader, datatype):
    cls_args = {}

    for field in fields(datatype):
        field_type = field.type
        field_name = field.name
        cls_args[field_name] = parse_field(reader, cls_args, field_type)

    return datatype(**cls_args)


def _serialize(curr_dataclass, field_type, field_data):
    ret = bytearray()
    if field_type in registered_types:
        ret.extend(field_data.serialize())

    elif inspect.isclass(field_type) and is_dataclass(field_type):
        ret.extend(serialize(field_data))

    elif get_origin(field_type) == Annotated:
        args = get_args(field_type)
        arg_type, length = args

        # if length is a string, then we are referencing a concrete field
        if isinstance(length, str):
            length = getattr(curr_dataclass, length).v

        if arg_type == bytes:
            ret.extend(field_data)

        elif get_origin(arg_type) == list:
            for i in range(length):
                ret.extend(_serialize(curr_dataclass, type(field_data[i]), field_data[i]))

    return ret


def serialize(dataclass) -> bytes:
    ret = bytearray()

    for field in fields(type(dataclass)):
        field_type = field.type
        field_name = field.name
        field_data = getattr(dataclass, field_name)

        ret.extend(_serialize(dataclass, field_type, field_data))

    return bytes(ret)
