from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Unpack, Any
from pwn import p8,u8,p16,u16,p32,u32
from functools import partial

@dataclass
class SizedIntConfig:
    signed: bool
    packer: Callable[[int, Unpack[Any]], bytes]
    unpacker: Callable[[bytes, Unpack[Any]], int]


class PType:
    SIZE: int = None
    config: SizedIntConfig

    def serialize(self) -> int: raise NotImplementedError
    def from_raw(self, raw) -> Any: raise NotImplementedError


# TODO: dataclasses should store ints somehow
# TODO: add arithmetic ops
# TODO: add unit tests!!

class SizedInt(PType):
    def __init__(self, v: int):
        self.v = v
        for op in 'add', 'and', 'floordiv', 'lshift', 'mod', 'mul', 'or', 'rshift', 'sub', 'xor':
            opname = f'__{op}__'
            new_method = partial(self.int_op, op=getattr(int, opname))
            setattr(SizedInt, opname, new_method)
            setattr(SizedInt, f'__r{op}__', new_method)

    def int_op(self, them, op):
        self.v = op(self.v, them)
        return self

    def serialize(self):
        return self.config.packer(self.v, signed=self.config.signed)

    def from_raw(self, raw) -> Any:
        self.v = self.config.unpacker(raw, signed=self.config.signed)
        return self

    # def __str__(self):
    #     return f'{self.v}'
    #
    # def __repr__(self):
    #     return str(self)
    #
    # def __lt__(self, other):
    #     return self.v < other.v


class U8(SizedInt):
    SIZE = 8
    config = SizedIntConfig(False, p8, u8)
    def __init__(self, v = 0):
        super().__init__(v)

class I8(SizedInt):
    SIZE = 8
    config = SizedIntConfig(True, p8, u8)
    def __init__(self, v = 0):
        super().__init__(v)

class U16(SizedInt):
    SIZE = 16
    config = SizedIntConfig(False, p16, u16)
    def __init__(self, v = 0):
        super().__init__(v)

class I16(SizedInt):
    SIZE = 16
    config = SizedIntConfig(True, p16, u16)
    def __init__(self, v = 0):
        super().__init__(v)

class U32(SizedInt):
    SIZE = 32
    config = SizedIntConfig(False, p32, u32)
    def __init__(self, v = 0):
        super().__init__(v)

class I32(SizedInt):
    SIZE = 32
    config = SizedIntConfig(True, p32, u32)
    def __init__(self, v = 0):
        super().__init__(v)

class MTime(I32):
    TS_ADJUST = 946684800  # 2000-01-01 00:00:00

    def __init__(self, v = 0):
        super().__init__(v)

    def __str__(self):
        if self.v < 0:
            return str(datetime.utcfromtimestamp(MTime.TS_ADJUST))
        return str(datetime.utcfromtimestamp(self.v * 60 + MTime.TS_ADJUST))


registered_types = {
    U8, I8,
    U16, I16,
    U32, I32,

    MTime
}
