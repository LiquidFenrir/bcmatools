from .readerthingy import ReaderThingy
from internal import usefulenums

class BCLIM(ReaderThingy):
    def __init__(self, data, s=0, e=None):
        end = len(data) if e is None else e
        ReaderThingy.__init__(self, data, end - 0x28, end)

    def validate(self):
        assert(self.read_format("4s") == b"CLIM")
        if self.read_format("H") != 0xfeff:
            self.endian = ">"

        assert(self.read_format("H") == 0x14)
        revision, filesize, datablocks, pad = self.read_format("2I2H")

        assert(self.read_format("4s") == b"imag")
        parseinfo, w, h, fileformat = self.read_format("I2HI")
        print("CLIM parseinfo width height format:", parseinfo,  w, h, usefulenums.ImageFormats(fileformat), sep="\n- ")
