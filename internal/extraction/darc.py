import os

from .readerthingy import ReaderThingy

class TableEntry:
    def __init__(self, reader, offset):
        self.filename_off, self.offset, self.size = reader.read_off("3I", offset)

    def __str__(self):
        return "TableEntry: f {} o {} s {}".format(hex(self.filename_off), hex(self.offset), hex(self.size))

    def __repr__(self):
        return str(self)

class DARC(ReaderThingy):
    def __init__(self, data):
        ReaderThingy.__init__(self, data, 0, len(data))

    def analyze_part(self, start_e, end_e):
        idx = start_e
        while idx < end_e:
            entry = self.data.tableentries[idx]

            folder = bool(entry.filename_off & 0x01000000)
            namoff = self.data.filetableoff + self.data.tablemetasize + (entry.filename_off & 0x00ffffff)

            name = []
            while type(name) is not str:
                c = self.read_off("2s", namoff)
                namoff += 2
                if c[0] == 0:
                    name = b"".join(name).decode('utf-16le')
                else:
                    name.append(c)

            if folder:
                assert(entry.size <= len(self.data.tableentries))
                old_path = self.data.pathroot
                self.data.pathroot = os.path.join(old_path, name)
                self.analyze_part(idx + 1, entry.size)
                self.data.pathroot = old_path
                idx = entry.size - 1
            else:
                assert(entry.offset < self.data.filelen)
                assert((entry.offset + entry.size) <= self.data.filelen)
                fullname = os.path.join(self.data.pathroot, name)
                self.data.files[fullname] = self.view[entry.offset : entry.offset + entry.size]

            idx += 1

    def validate(self):
        headermagic, endianness = self.read_format("4sh")
        assert(headermagic == b"darc")
        headerlen = self.read_format("H")
        assert(headerlen == 0x1c)

        self.data.version, self.data.filelen, self.data.filetableoff, self.data.filetablelen, self.data.filedataoff = self.read_format("5I")
        assert(self.data.version == 0x01000000)
        assert(self.data.filelen == self.size)
        assert(self.data.filetableoff == 0x1c)

        d = self.read_format("3I")
        entries_count = d[2]

        tabledata_start = self.data.filetableoff
        self.data.tablemetasize = entries_count * 0xC
        assert(self.data.tablemetasize <= self.data.filetablelen)

        self.data.tableentries = [TableEntry(self, i + tabledata_start) for i in range(0, self.data.tablemetasize, 0xC)]
        self.data.files = {}
        self.data.pathroot = ""
        self.analyze_part(2, len(self.data.tableentries))
