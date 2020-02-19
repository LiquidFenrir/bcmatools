import struct

from internal import dataholder

class ReaderThingy:
    __slots__ = ["parent", "start", "index", "view", "size", "endian", "data"]

    def read_off(self, f, o, smolize=True):
        d = struct.unpack_from(self.endian + f, self.view, o)
        if smolize and len(d) == 1:
            return d[0]
        else:
            return d

    def read_format(self, f, smolize=True):
        old_index = self.index
        self.index += struct.calcsize(f)
        return self.read_off(f, self.start + old_index, smolize)

    def __init__(self, view, start, size, **kwargs):
        self.parent = kwargs.get("parent", None)
        self.start = start
        self.index = 0
        self.view = view
        self.size = size
        self.endian = "<"
        self.data = dataholder.DataHolder()
        if not kwargs.get("later", False):
            self.validate()
