import os
import struct

def explore_tree(file_tree, folder = ""):
    folders = set()
    if len(folder):
        folders.add(folder)
    files = {}
    for k, v in file_tree.items():
        newk = k if len(folder) == 0 else os.path.join(folder, k)
        if type(v) is dict:
            newfolders, newfiles = explore_tree(v, newk)
            folders.update(newfolders)
            files.update(newfiles)
        else:
            files[newk] = v
    return folders, files

class TableEntry:
    def __init__(self, folder, name_off_from_end, data_offset_from_end, size):
        self.name_off = name_off_from_end
        if folder:
            self.name_off |= 0x01000000
        self.data_off = data_offset_from_end
        self.size = size

class DARC:
    def __init__(self, file_tree):
        folders, files = explore_tree(file_tree)
        assert(len(folders) <= 1) # only supports trees with 1 folder or none at all
        header_size = 0x1c
        header_bom = 0xfeff
        header_version = 0x01000000
        self.header = struct.pack("<4s2HI", b"darc", header_bom, header_size, header_version)
        table_start = header_size
        table_entries_count = len(folders) + len(files) + 2
        table_entries_size = table_entries_count * 0xC
        self.names = bytearray.fromhex("00002e000000")
        entries = []
        entries.append(TableEntry(True, 0, 0, table_entries_count))
        entries.append(TableEntry(True, 2, 0, table_entries_count))
        name_index = len(self.names)
        for foldername in folders:
            encoded = foldername.encode("utf-16le") + (b"\x00" * 2)
            self.names.extend(encoded)
            entries.append(TableEntry(True, name_index, 1, table_entries_count))  # dunno why, but observed 1
            name_index += len(encoded)
        table_files_start_index = len(entries)
        for filename, data in files.items():
            encoded = os.path.basename(filename).encode("utf-16le") + (b"\x00" * 2)
            self.names.extend(encoded)
            entries.append(TableEntry(False, name_index, 0, len(data)))
            entries[-1].data = data
            name_index += len(encoded)
        # pad to 4 byte boundary
        if len(self.names) & 3:
            self.names += b"\x00" * (4 - (len(self.names) & 3))
        data_start = table_start + table_entries_size + len(self.names)
        self.filedata = bytearray()
        for i in range(table_files_start_index, len(entries)):
            new_off = len(self.filedata) + data_start
            entries[i].data_off = new_off
            self.filedata += entries[i].data
            diff = len(self.filedata) & 15
            if diff != 0:
                self.filedata += b"\x00" * (16 - diff)
        self.entries_data = bytearray()
        for e in entries:
            self.entries_data += struct.pack("<3I", e.name_off, e.data_off, e.size)
        filelen = header_size + len(self.entries_data) + len(self.names) + len(self.filedata)
        self.header += struct.pack("4I", filelen, table_start, len(self.filedata), header_size + len(self.entries_data) + len(self.names))

    def write_to_file(self, out):
        out.write(self.header)
        out.write(self.entries_data)
        out.write(self.names)
        out.write(self.filedata)