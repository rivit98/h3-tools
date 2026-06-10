from serializer.serializer import serialize


class Packet:
    @staticmethod
    def packets_needed():
        return 1

    @staticmethod
    def print_enabled():
        return True

    def serialize(self) -> bytes:
        return serialize(self)

    def name(self):
        return self.__class__.__name__

    # TODO: fixme for should be a static method?
    # def type(self):
    #     return rev_msg_types.get(type(self))

    # def __len__(self):
    #     # TODO: implement me mommy
    #     raise NotImplementedError

    @staticmethod
    def from_bytes(raw):
        # TODO:
        raise NotImplementedError

# TODO: maybe postinit should convert ints to U[8,16,32] variants?