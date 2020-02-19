import struct
from io import BytesIO
from typing import List, Any
from dataclasses import dataclass

from internal import usefulenums

USD_TYPE_OVERRIDE = 1

class Writable:
    def __init__(self, out=None):
        if out is None:
            self.fobj = BytesIO()
        else:
            self.fobj = out

    def write(self, fmt, *args):
        self.fobj.write(struct.pack(fmt, *args))
    def raw(self, buf):
        if type(buf) is Writable:
            assert(type(buf.fobj) is BytesIO)
            self.fobj.write(buf.fobj.getbuffer())
        else:
            self.fobj.write(buf)

    def __len__(self):
        assert(type(self.fobj) is BytesIO)
        return len(self.fobj.getbuffer())

    def asbytes(self):
        return self.fobj.getvalue()

class RGBA:
    MAPPED_COLORS = {}

    @staticmethod
    def add_from_color(color):
        assert(color.tag == "Color")
        r = int(color.get("r"))
        g = int(color.get("g"))
        b = int(color.get("b"))
        a = int(color.get("a"))
        RGBA.MAPPED_COLORS[color.get("index")] = (r, g, b, a)

    @staticmethod
    def from_index(idx):
        return struct.unpack("<I", struct.pack("<4B", *(RGBA.MAPPED_COLORS[idx])))[0]

class Vec2:
    def __init__(self, node, conv=False):
        assert(node.tag == "Vector2")
        self.name = node.get("name")
        self.x = node.get("x")
        self.y = node.get("y")
        if conv:  # don't need to check, this bud is always made of floats
            self.convert()

    def write_to_file(self, out):
        out.write("<2f", self.x, self.y)

    def convert(self, converter=float, converterY=None):
        if converterY is None:
            converterY = converter
        self.x = converter(self.x)
        self.y = converterY(self.y)

class Vec3:
    def __init__(self, node):
        assert(node.tag == "Vector3")
        self.name = node.get("name")
        self.x = float(node.get("x"))
        self.y = float(node.get("y"))
        self.z = float(node.get("z"))

    def write_to_file(self, out):
        out.write("<3f", self.x, self.y, self.z)

class Lyt1:
    def __init__(self, bclyt, node):
        self.origin = usefulenums.OriginType[node.get("origin_type")]
        size = Vec2(node[0], True)
        assert(size.name == "size")
        self.size = size

    def write_to_file(self, out):
        out.write("<4sI", b"lyt1", 0x14)
        out.write("<I", self.origin.value)
        self.size.write_to_file(out)

class Fnl1:
    def __init__(self, bclyt, node):
        self.font_count = len(node)
        self.index = {}
        self.name_offsets = []
        self.font_names = bytearray()
        offset_start = self.font_count * 4
        for font in node:
            self.name_offsets.append(len(self.font_names) + offset_start)
            self.font_names += font.text.encode("utf-8")
            self.index[font.text] = len(self.index)
            self.font_names += b"\x00"
        diff = len(self.font_names) & 3
        if diff != 0:
            self.font_names += b"\x00" * (4 - diff)

    def get_index(self):
        return self.index

    def write_to_file(self, out):
        out.write("<4sI", b"fnl1", 8 + 4 + self.font_count * 4 + len(self.font_names))  # header (section name, section size)
        out.write("<I{}I".format(self.font_count), self.font_count, *self.name_offsets)
        out.raw(self.font_names)

class Txl1:
    def __init__(self, bclyt, node):
        self.texture_count = len(node)
        self.index = {}
        self.name_offsets = []
        self.texture_names = bytearray()
        offset_start = self.texture_count * 4
        for texture in node:
            self.name_offsets.append(len(self.texture_names) + offset_start)
            self.texture_names += texture.text.encode("utf-8")
            self.index[texture.text] = len(self.index)
            self.texture_names += b"\x00"
        diff = len(self.texture_names) & 3
        if diff != 0:
            self.texture_names += b"\x00" * (4 - diff)

    def get_index(self):
        return self.index

    def write_to_file(self, out):
        out.write("<4sI", b"txl1", 8 + 4 + self.texture_count * 4 + len(self.texture_names))  # header (section name, section size)
        out.write("<I{}I".format(self.texture_count), self.texture_count, *self.name_offsets)
        out.raw(self.texture_names)

class TexMapEntry:
    def __init__(self, bclyt, node):
        self.texture_index = bclyt.texture_index_from_name(node.get("texture_name"))
        self.wrap_s_mode = usefulenums.WrapMode[node.get("wrap_s_mode")]
        self.min_filter_mode = usefulenums.FilterMode[node.get("min_filter_mode")]
        self.wrap_t_mode = usefulenums.WrapMode[node.get("wrap_t_mode")]
        self.max_filter_mode = usefulenums.FilterMode[node.get("max_filter_mode")]

    def write_to_file(self, out):
        val1 = (self.wrap_s_mode.value & 0b11) | ((self.min_filter_mode.value & 0b11) << 2)
        val2 = (self.wrap_t_mode.value & 0b11) | ((self.max_filter_mode.value & 0b11) << 2)
        out.write("<H2B", self.texture_index, val1, val2)

class TexMatrixEntry:
    def __init__(self, bclyt, node):
        self.translation = Vec2(node[0], True)
        self.rotation = float(node.get("rotation"))
        self.scale = Vec2(node[1], True)
        assert(self.translation.name == "translation")
        assert(self.scale.name == "scale")

    def write_to_file(self, out):
        self.translation.write_to_file(out)
        out.write("<f", self.rotation)
        self.scale.write_to_file(out)

class TexCoordGen:
    def __init__(self, bclyt, node):
        self.gen_type = usefulenums.MatrixType[node.get("gen_type")]
        self.source = usefulenums.TextureGenerationType[node.get("source")]

    def write_to_file(self, out):
        out.write("<2B2x", self.gen_type.value, self.source.value)

class TevStage:
    def __init__(self, bclyt, node):
        self.rgb_mode = int(node.get("rgb_mode"))
        self.alpha_mode = int(node.get("alpha_mode"))

    def write_to_file(self, out):
        out.write("<2B2x", self.rgb_mode, self.alpha_mode)

class AlphaCompare:
    def __init__(self, bclyt, node):
        self.compare_mode = int(node.get("compare_mode"))
        self.reference = float(node.get("reference"))

    def write_to_file(self, out):
        out.write("<If", self.compare_mode, self.reference)

class BlendMode:
    def __init__(self, bclyt, node):
        self.blend_operation = usefulenums.Blend_BlendFactor[node.get("blend_operation")]
        self.source_factor = usefulenums.BlendMode_BlendOp[node.get("source_factor")]
        self.dest_factor = usefulenums.BlendMode_BlendOp[node.get("dest_factor")]
        self.logic_operation = usefulenums.Blend_LogicOp[node.get("logic_operation")]

    def write_to_file(self, out):
        out.write("<4B", self.blend_operation.value, self.source_factor.value, self.dest_factor.value, self.logic_operation.value)

class IndirectParam:
    def __init__(self, bclyt, node):
        self.rotation = float(node.get("rotation"))
        self.scale = Vec2(node[0], True)
        assert(self.scale.name == "scale")

    def write_to_file(self, out):
        out.write("<f", self.rotation)
        self.scale.write_to_file(out)

class ProjTexGenParam:
    def __init__(self, bclyt, node):
        self.pos = Vec2(node[0], True)
        self.scale = Vec2(node[0], True)
        self.fits_layout = bool(int(node.get("fits_layout")))
        self.fits_panel = bool(int(node.get("fits_panel")))
        assert(self.pos.name == "pos")
        assert(self.scale.name == "scale")

    def write_to_file(self, out):
        self.pos.write_to_file(out)
        self.scale.write_to_file(out)
        flags = 0
        if self.fits_layout:
            flags |= 0b01
        if self.fits_panel:
            flags |= 0b10
        out.write("<B3x", flags)

class FontShadowParam:
    def __init__(self, bclyt, node):
        self.black_r = int(node.get("black_r"))
        self.black_g = int(node.get("black_g"))
        self.black_b = int(node.get("black_b"))
        self.white_r = int(node.get("white_r"))
        self.white_g = int(node.get("white_g"))
        self.white_b = int(node.get("white_b"))
        self.white_a = int(node.get("white_a"))

    def write_to_file(self, out):
        out.write("<7Bx", self.black_r, self.black_g, self.black_b, self.white_r, self.white_g, self.white_b, self.white_a)

class Material:
    def __init__(self, bclyt, node):
        assert(node.tag == "Material")
        self.name = node.get("name")
        self.tev_color = node.get("tev_color")
        assert(node[0].tag == "TevConstantColors")
        self.tev_constant_colors = [child.text for child in node[0]]
        remaining = node[1:]
        self.font_shadow_param = None
        self.indirect_param = None
        self.separate_blend_mode = None
        self.use_texture_only = None  # unused? the parser doesnt know it
        self.blend_mode = None
        self.alpha_compare = None
        self.proj_tex_gen_params = []
        self.tev_stages = []
        self.tex_coordgens = []
        self.tex_matrices = []
        self.tex_maps = []
        for child in remaining:
            if child.tag == "TexMapEntry":
                self.tex_maps.append(TexMapEntry(bclyt, child))
            elif child.tag == "TexMatrixEntry":
                self.tex_matrices.append(TexMatrixEntry(bclyt, child))
            elif child.tag == "TexCoordGen":
                self.tex_coordgens.append(TexCoordGen(bclyt, child))
            elif child.tag == "TevStage":
                self.tev_stages.append(TevStage(bclyt, child))
            elif child.tag == "ColorBlendMode":
                self.blend_mode = BlendMode(bclyt, child)
            elif child.tag == "AlphaBlendMode":
                self.separate_blend_mode = BlendMode(bclyt, child)
            elif child.tag == "AlphaCompare":
                self.alpha_compare = AlphaCompare(bclyt, child)
            elif child.tag == "IndirectParam":
                self.indirect_param = IndirectParam(bclyt, child)
            elif child.tag == "FontShadowParam":
                self.font_shadow_param = FontShadowParam(bclyt, child)
            elif child.tag == "ProjTexGenParam":
                self.proj_tex_gen_params.append(ProjTexGenParam(bclyt, child))

    def write_to_file(self, out):
        out.write("<20s7I", self.name.encode("utf-8"), RGBA.from_index(self.tev_color), *map(RGBA.from_index, self.tev_constant_colors))
        flags = 0
        flags |= int(self.font_shadow_param is not None) & 1
        flags <<= 2
        flags |= len(self.proj_tex_gen_params) & 0b11
        flags <<= 1
        flags |= int(self.indirect_param is not None) & 1
        flags <<= 1
        flags |= int(self.separate_blend_mode is not None) & 1
        flags <<= 1
        flags |= int(self.use_texture_only is not None) & 1
        flags <<= 1
        flags |= int(self.blend_mode is not None) & 1
        flags <<= 1
        flags |= int(self.alpha_compare is not None) & 1
        flags <<= 3
        flags |= len(self.tev_stages) & 0b111
        flags <<= 2
        flags |= len(self.tex_coordgens) & 0b11
        flags <<= 2
        flags |= len(self.tex_matrices) & 0b11
        flags <<= 2
        flags |= len(self.tex_maps) & 0b11
        out.write("<I", flags)
        for e in self.tex_maps:
            e.write_to_file(out)
        for e in self.tex_matrices:
            e.write_to_file(out)
        for e in self.tex_coordgens:
            e.write_to_file(out)
        for e in self.tev_stages:
            e.write_to_file(out)
        if self.alpha_compare is not None:
            self.alpha_compare.write_to_file(out)
        if self.blend_mode is not None:
            self.blend_mode.write_to_file(out)
        if self.separate_blend_mode is not None:
            self.separate_blend_mode.write_to_file(out)
        if self.indirect_param is not None:
            self.indirect_param.write_to_file(out)
        for e in self.proj_tex_gen_params:
            e.write_to_file(out)
        if self.font_shadow_param is not None:
            self.font_shadow_param.write_to_file(out)

class Mat1:
    def __init__(self, bclyt, node):
        self.materials = [Material(bclyt, child) for child in node]

    def get_index(self):
        out = {}
        for i, mat in enumerate(self.materials):
            out[mat.name] = i
        return out

    def write_to_file(self, out):
        material_data = Writable()
        mat_count = len(self.materials)
        start_off = 8 + 4 + mat_count * 4
        mat_offsets = []
        for mat in self.materials:
            mat_offsets.append(start_off + len(material_data))
            mat.write_to_file(material_data)
        # print(*map(hex, mat_offsets))
        out.write("<4sI", b"mat1", 8 + 4 + mat_count * 4 + len(material_data))  # header (section name, section size)
        out.write("<I{}I".format(mat_count), mat_count, *mat_offsets)
        out.raw(material_data)

class Marker:
    def write_to_file(self, out):
        out.write("<4sI", type(self).__name__.lower().encode("ascii"), 8)

class Pas1(Marker):
    pass
class Pae1(Marker):
    pass
class Grs1(Marker):
    pass
class Gre1(Marker):
    pass

class PanelData:
    @dataclass
    class Internal:
        flags: usefulenums.PanelFlags
        origin: Vec2
        parent_origin: Vec2
        alpha: int
        magnification_flags: usefulenums.PanelMagnificationFlags
        name: str
        translation: Vec3
        rotation: Vec3
        scale: Vec2
        size: Vec2

        def write_to_file(self, out):
            origin = 0
            origin |= self.origin.x.value
            origin <<= 2
            origin |= self.origin.y.value
            origin <<= 2
            origin |= self.parent_origin.x.value
            origin <<= 2
            origin |= self.parent_origin.y.value
            out.write("<4B", self.flags.value, origin, self.alpha, self.magnification_flags.value)
            out.write("<{}s".format(0x18), self.name.encode("utf-8"))
            self.translation.write_to_file(out)
            self.rotation.write_to_file(out)
            self.scale.write_to_file(out)
            self.size.write_to_file(out)

    @dataclass
    class TxtData(Internal):
        additional_chars: int
        font_index: int
        material_index: int
        another_origin: Vec2
        line_alignment: usefulenums.LineAlignment
        # color indexes
        top_color: str
        bottom_color: str
        text_size: Vec2
        character_size: float
        line_size: float
        text: str

        def write_to_file(self, out):
            PanelData.Internal.write_to_file(self, out)
            if len(self.text) == 0:
                encoded_text = b""
            else:
                encoded_text = self.text.encode("utf-16le") + b"\x00\x00"  # terminating NUL
            total_text_len = len(encoded_text)
            max_size = total_text_len + self.additional_chars * 2
            out.write("<2H", max_size, total_text_len)
            out.write("<2H", self.material_index, self.font_index)
            origin = 0
            origin |= self.another_origin.x.value
            origin <<= 2
            origin |= self.another_origin.y.value
            out.write("<2B2x", origin, self.line_alignment.value)
            text_offset = 0x74  # never observed another value so /shrug
            out.write("<I", text_offset)
            out.write("<2I", RGBA.from_index(self.top_color), RGBA.from_index(self.bottom_color))
            self.text_size.write_to_file(out)
            out.write("<2f", self.character_size, self.line_size)
            out.raw(encoded_text)

    @dataclass
    class TexCoord:
        tl: Vec2
        tr: Vec2
        bl: Vec2
        br: Vec2

        def write_to_file(self, out):
            self.tl.write_to_file(out)
            self.tr.write_to_file(out)
            self.bl.write_to_file(out)
            self.br.write_to_file(out)

    @dataclass
    class PicData(Internal):
        # color indexes
        tl_color: str
        tr_color: str
        bl_color: str
        br_color: str
        material_index: int
        # texture_coords: List[TexCoord]
        texture_coords: List[Any]

        def write_to_file(self, out):
            PanelData.Internal.write_to_file(self, out)
            out.write("<4I", RGBA.from_index(self.tl_color), RGBA.from_index(self.tr_color), RGBA.from_index(self.bl_color), RGBA.from_index(self.br_color))
            out.write("<2H", self.material_index, len(self.texture_coords))
            for coord in self.texture_coords:
                coord.write_to_file(out)

    @dataclass
    class UVCoord:
        u: float
        v: float

        def write_to_file(self, out):
            out.write("<2f", self.u, self.v)
    @dataclass
    class UVCoordSet:
        # tl: UVCoord
        # tr: UVCoord
        # bl: UVCoord
        # br: UVCoord
        tl: Any
        tr: Any
        bl: Any
        br: Any

        def write_to_file(self, out):
            self.tl.write_to_file(out)
            self.tr.write_to_file(out)
            self.bl.write_to_file(out)
            self.br.write_to_file(out)
    @dataclass
    class WndFrame:
        material_index: int
        flip_type: int

        def write_to_file(self, out):
            out.write("<HBx", self.material_index, self.flip_type)

    @dataclass
    class WndData(Internal):
        content_overflow_l: float
        content_overflow_r: float
        content_overflow_t: float
        content_overflow_b: float
        flag: int
        # color indexes
        tl_color: str
        tr_color: str
        bl_color: str
        br_color: str
        material_index: int
        # uvsets: List[UVCoordSet]
        # frames: List[WndFrame]
        uvsets: List[Any]
        frames: List[Any]

        def write_to_file(self, out):
            PanelData.Internal.write_to_file(self, out)
            out.write("<4f", self.content_overflow_l, self.content_overflow_r, self.content_overflow_t, self.content_overflow_b)
            out.write("<2B2x", len(self.frames), self.flag)
            out.write("<2I", 0x68, 0x7c)
            out.write("<4I", RGBA.from_index(self.tl_color), RGBA.from_index(self.tr_color), RGBA.from_index(self.bl_color), RGBA.from_index(self.br_color))
            out.write("<2H", self.material_index, len(self.uvsets))
            for uvset in self.uvsets:
                uvset.write_to_file(out)
            frame_off = 0x7C
            frame_off += len(self.frames) * 4
            for i in range(len(self.frames)):
                out.write("<I", frame_off)
                frame_off += 4
            for frame in self.frames:
                frame.write_to_file(out)

    def make_pan1(self, bclyt, node):
        conversion = {
            "flags": lambda f: usefulenums.PanelFlags[f],
            "alpha": int,
            "magnification_flags": lambda f: usefulenums.PanelMagnificationFlags[f],
            "name": str,
        }
        out = {}
        for k, v in node.attrib.items():
            out[k] = conversion[k](v)
        for child in node:
            if child.tag == "Vector2":
                vec = Vec2(child)
                if "origin" in vec.name:
                    vec.convert(lambda x: usefulenums.OriginHorizontal[x], lambda y: usefulenums.OriginVertical[y])
                else:
                    vec.convert()
                out[vec.name] = vec
            elif child.tag == "Vector3":
                vec = Vec3(child)
                out[vec.name] = vec
        return PanelData.Internal(**out)

    def make_txt1(self, bclyt, node):
        conversion = {
            "flags": lambda f: usefulenums.PanelFlags[f],
            "alpha": int,
            "magnification_flags": lambda f: usefulenums.PanelMagnificationFlags[f],
            "name": str,
            "additional_chars": int,
            "font_index": bclyt.font_index_from_name,
            "material_index": bclyt.material_index_from_name,
            "line_alignment": lambda f: usefulenums.LineAlignment[f],
            "top_color": str,
            "bottom_color": str,
            "character_size": float,
            "line_size": float,
            "text": str,
        }
        out = {}
        for k, v in node.attrib.items():
            if k == "material_name":
                k = "material_index"
            elif k == "font_name":
                k = "font_index"
            out[k] = conversion[k](v)
        for child in node:
            if child.tag == "Vector2":
                vec = Vec2(child)
                if "origin" in vec.name:
                    vec.convert(lambda x: usefulenums.OriginHorizontal[x], lambda y: usefulenums.OriginVertical[y])
                else:
                    vec.convert()
                out[vec.name] = vec
            elif child.tag == "Vector3":
                vec = Vec3(child)
                out[vec.name] = vec
        return PanelData.TxtData(**out)

    def make_pic1(self, bclyt, node):
        conversion = {
            "flags": lambda f: usefulenums.PanelFlags[f],
            "alpha": int,
            "magnification_flags": lambda f: usefulenums.PanelMagnificationFlags[f],
            "name": str,
            "tl_color": str,
            "tr_color": str,
            "bl_color": str,
            "br_color": str,
            "material_index": bclyt.material_index_from_name
        }
        out = {}
        for k, v in node.attrib.items():
            if k == "material_name":
                k = "material_index"
            out[k] = conversion[k](v)
        for child in node:
            if child.tag == "Vector2":
                vec = Vec2(child)
                if "origin" in vec.name:
                    vec.convert(lambda x: usefulenums.OriginHorizontal[x], lambda y: usefulenums.OriginVertical[y])
                else:
                    vec.convert()
                out[vec.name] = vec
            elif child.tag == "Vector3":
                vec = Vec3(child)
                out[vec.name] = vec
            elif child.tag == "TextureCoords":
                coords = out.get("texture_coords", [])
                if len(coords) == 0:
                    out["texture_coords"] = coords
                coords.append(PanelData.TexCoord(*map(lambda c: Vec2(c, True), child)))
        return PanelData.PicData(**out)

    def make_wnd1(self, bclyt, node):
        conversion = {
            "flags": lambda f: usefulenums.PanelFlags[f],
            "alpha": int,
            "magnification_flags": lambda f: usefulenums.PanelMagnificationFlags[f],
            "name": str,
            "content_overflow_l": float,
            "content_overflow_r": float,
            "content_overflow_t": float,
            "content_overflow_b": float,
            "flag": int,
            "tl_color": str,
            "tr_color": str,
            "bl_color": str,
            "br_color": str,
            "material_index": bclyt.material_index_from_name
        }
        out = {}
        for k, v in node.attrib.items():
            if k == "material_name":
                k = "material_index"
            out[k] = conversion[k](v)
        for child in node:
            if child.tag == "Vector2":
                vec = Vec2(child)
                if "origin" in vec.name:
                    vec.convert(lambda x: usefulenums.OriginHorizontal[x], lambda y: usefulenums.OriginVertical[y])
                else:
                    vec.convert()
                out[vec.name] = vec
            elif child.tag == "Vector3":
                vec = Vec3(child)
                out[vec.name] = vec
            elif child.tag == "WindowFrame":
                frames = out.get("frames", [])
                if len(frames) == 0:
                    out["frames"] = frames
                frames.append(PanelData.WndFrame(bclyt.material_index_from_name(child.get("material")), int(child.get("flip"))))
            else:
                print("WndData unknown child:", child.tag)
        out["uvsets"] = []
        return PanelData.WndData(**out)

    def __init__(self, bclyt, paneltype, node):
        self.type = paneltype
        datatypes = {
            "pan1": self.make_pan1,
            "txt1": self.make_txt1,
            "pic1": self.make_pic1,
            "wnd1": self.make_wnd1,
        }
        self.data = datatypes[paneltype](bclyt, node)

    def write_to_file(self, out):
        data_bytes = Writable()
        self.data.write_to_file(data_bytes)
        diff = len(data_bytes) & 3
        if diff:
            data_bytes.write("<{}x".format(4 - diff))
        out.write("<4sI", self.type.encode("ascii"), 8 + len(data_bytes))
        out.raw(data_bytes)

class UserData:
    @dataclass
    class Internal:
        name: str
        internal_type: int
        nameoff: int
        dataoff: int
        setting: int
        typ: usefulenums.UsdEntryDataType

        def write_to_file(self, out):
            out.write("<2IHBx", self.nameoff, self.dataoff, self.setting, self.typ.value)

    def __init__(self, bclyt, node):
        self.offsets_info = []
        self.data = bytearray()
        deltaoff = 12 * len(node)
        for n in node:
            assert(n.tag == "Data")
            namoff = 0
            nam = n.get("name")
            if USD_TYPE_OVERRIDE == -1:
                if nam == "IsAreaRect" or nam == "LayoutIndex":
                    internal_type = 2
                else:
                    internal_type = 1
            else:
                internal_type = USD_TYPE_OVERRIDE
            curtyp = usefulenums.UsdEntryDataType[n.get("type")]
            if curtyp == usefulenums.UsdEntryDataType.String:
                assert(n[0].tag == "String")
                text = n[0].text
                setting = len(text)
                dataoff = len(self.data)
                self.data += text.encode("utf-8")
                self.data += b"\x00"
                if internal_type == 1:
                    namoff = len(self.data) + deltaoff
                    self.data += nam.encode("utf-8")
                    self.data += b"\x00"
            elif curtyp == usefulenums.UsdEntryDataType.Ints:
                setting = len(n)
                diff = len(self.data) & 3
                if diff != 0:
                    self.data += b"\x00" * (4 - diff)
                dataoff = len(self.data)
                for child in n:
                    assert(child.tag == "Integer")
                    self.data += struct.pack("<I", int(child.text))
                if internal_type == 1:
                    namoff = len(self.data) + deltaoff
                    self.data += nam.encode("utf-8")
                    self.data += b"\x00"
            elif curtyp == usefulenums.UsdEntryDataType.Floats:
                setting = len(n)
                diff = len(self.data) & 3
                if diff != 0:
                    self.data += b"\x00" * (4 - diff)
                dataoff = len(self.data)
                for child in n:
                    assert(child.tag == "Float")
                    self.data += struct.pack("<f", float(child.text))
                if internal_type == 1:
                    namoff = len(self.data) + deltaoff
                    self.data += nam.encode("utf-8")
                    self.data += b"\x00"
            self.offsets_info.append(UserData.Internal(nam, internal_type, namoff, dataoff + deltaoff, setting, curtyp))
            deltaoff -= 12

        deltaoff = 12 * len(self.offsets_info)
        for info in self.offsets_info:
            if info.internal_type == 2:
                info.nameoff = len(self.data) + deltaoff
                self.data += info.name.encode("utf-8")
                self.data += b"\x00"
            deltaoff -= 12
        diff = len(self.data) & 3
        if diff:
            self.data += b"\x00" * (4 - diff)

    def write_to_file(self, out):
        data_count = len(self.offsets_info)
        out.write("<4sI", b"usd1", 8 + 4 + (12 * data_count) + len(self.data))
        out.write("<I", data_count)
        for offinfo in self.offsets_info:
            offinfo.write_to_file(out)
        out.raw(self.data)

class Panel:
    def __init__(self, bclyt, node):
        self.parts = []
        self.parts.append(PanelData(bclyt, node.get("type").lower(), node[0]))
        if node[-1].tag == "UserData":
            cut = node[1:-1]
        else:
            cut = node[1:]

        if len(cut) != 0:
            self.parts.append(Pas1())
            for child in cut:
                self.parts.extend(Panel(bclyt, child).parts)
            self.parts.append(Pae1())

        if node[-1].tag == "UserData":
            self.parts.append(UserData(bclyt, node[-1]))

class Grp1:
    def __init__(self, bclyt, name, panels_refs):
        self.name = name
        self.refs = []
        for ref in panels_refs:
            assert(ref.tag == "PanelRef")
            self.refs.append(ref.get("name"))

    def write_to_file(self, out):
        out.write("<4sI", b"grp1", 8 + 16 + 4 + 16 * len(self.refs))
        out.write("<16s", self.name.encode("utf-8"))
        out.write("<I", len(self.refs))
        for ref in self.refs:
            out.write("<16s", ref.encode("utf-8"))

class Group:
    def __init__(self, bclyt, node):
        self.parts = []
        self.parts.append(Grp1(bclyt, node.get("name"), node[:node.get("panels_count")]))

class BCLYT:
    def add_layout(self, node):
        self.sections.append(Lyt1(self, node))

    def add_colors(self, node):
        self.colors_dict = {}
        RGBA.MAPPED_COLORS = self.colors_dict
        for color in node:
            RGBA.add_from_color(color)

    def add_fonts(self, node):
        if len(node) == 0:
            return
        fnl = Fnl1(self, node)
        self.fonts = fnl.get_index()
        self.sections.append(fnl)
    def add_textures(self, node):
        if len(node) == 0:
            return
        txl = Txl1(self, node)
        self.textures = txl.get_index()
        self.sections.append(txl)
    def add_materials(self, node):
        if len(node) == 0:
            return
        mat = Mat1(self, node)
        self.materials = mat.get_index()
        self.sections.append(mat)
    def add_root_panel(self, node):  # nested structure
        pan = Panel(self, node)
        self.sections += pan.parts
    def add_root_group(self, node):  # nested structure
        grp  = Group(self, node)
        self.sections += grp.parts

    def __init__(self, root):
        assert(root.tag == "BCLYT")
        self.sections = []
        section_type_map = {
            "Layout": self.add_layout,
            "Colors": self.add_colors,
            "Fonts": self.add_fonts,
            "Textures": self.add_textures,
            "Materials": self.add_materials,
            "Panel": self.add_root_panel,
            "Group": self.add_root_group,
        }
        for child in root:
            try:
                section_type_map[child.tag](child)
            except KeyError:
                raise ValueError(f"Unknown tag at BCLYT level: {child.tag} ")

    def texture_index_from_name(self, texture_name):
        return self.textures[texture_name]
    def font_index_from_name(self, font_name):
        return self.fonts[font_name]
    def material_index_from_name(self, material_name):
        return self.materials[material_name]

    def write_to_file(self, out):
        RGBA.MAPPED_COLORS = self.colors_dict
        output = Writable(out)
        sections_data = Writable()
        for s in self.sections:
            s.write_to_file(sections_data)
        header_bom = 0xfeff
        header_size = 0x14
        revision = 0x2020000
        output.write("<4s2H3I", b"CLYT", header_bom, header_size, revision, len(sections_data) + header_size, len(self.sections))
        output.raw(sections_data)
