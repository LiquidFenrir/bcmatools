# info sources:
# https://github.com/shibbo/flyte/
# https://github.com/pleonex/Clypo
# http://3dbrew.org/wiki/CLYT_format

from lxml.builder import E as GenXML

from .readerthingy import ReaderThingy
from internal import usefulenums
from internal.dataholder import DataHolder

def check_type(k, v, out, outattrs):
    mat_types = (
        TevConstantColors,
        TexMapEntry,
        TexMatrixEntry,
        TexCoordGen,
        TevStage,
        AlphaCompare,
        BlendMode,
        IndirectParam,
        ProjTexGenParam,
        FontShadowParam,
    )
    if type(v) in (Vec2, Vec3):
        out.append(v.to_xml(k))
    elif type(v) is Wnd1Frame:
        out.append(v.to_xml())
    elif type(v) is UVCoordSet:
        out.append(v.to_xml())
    elif type(v) is RGBA:
        outattrs[k] = str(v.index)
    elif type(v) in mat_types:
        out.append(v.to_xml())
    elif type(v) is list:
        for x in v:
            check_type(k, x, out, outattrs)
    elif type(v) is TextureCoords:
        tmp = attr_control(v)
        out.append(GenXML.TextureCoords(*tmp))
    elif type(v) is bool:
        outattrs[k] = str(int(v))
    else:
        outattrs[k] = str(v)
def attr_control(data):
    attrs = data.getdata()
    out = []
    outattrs = {}
    for k, v in attrs.items():
        check_type(k, v, out, outattrs)
    out.append(outattrs)
    return out

class RGBA:
    MAPPED_COLORS = []
    def __init__(self, number):
        data = DataHolder()
        data.r = (number & (0xFF << (8 * 0))) >> (8 * 0)
        data.g = (number & (0xFF << (8 * 1))) >> (8 * 1)
        data.b = (number & (0xFF << (8 * 2))) >> (8 * 2)
        data.a = (number & (0xFF << (8 * 3))) >> (8 * 3)
        try:
            self.index = RGBA.MAPPED_COLORS.index(data)
        except:
            self.index = len(RGBA.MAPPED_COLORS)
            self.MAPPED_COLORS.append(data)

    def __str__(self):
        return "RGBA({})".format(RGBA.MAPPED_COLORS[self.index])

    def __repr__(self):
        return str(self)

class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "Vec2(x={0.x}, y={0.y})".format(self)

    def __repr__(self):
        return str(self)

    def to_xml(self, name):
        return GenXML.Vector2(name=name, x=str(self.x), y=str(self.y))

class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return "Vec3(x={0.x}, y={0.y}, z={0.z})".format(self)

    def __repr__(self):
        return str(self)

    def to_xml(self, name):
        return GenXML.Vector3(name=name, x=str(self.x), y=str(self.y), z=str(self.z))

class UVCoord:
    def __init__(sefl, floats):
        self.u = floats[0]
        self.v = floats[1]

    def __str__(self):
        return "UV(u={0.u}, v={0.v})".format(self)

    def __repr__(self):
        return str(self)

def splitarray(arr, sz):
    return [arr[x:x+sz] for x in range(0, len(arr), sz)]

class UVCoordSet:
    def __init__(sefl, floats):
        self.data = DataHolder()
        self.data.tl, self.data.tr, self.data.bl, self.data.br = map(UVCoord, splitarray(floats))

    def __str__(self):
        return "{}({})".format(type(self).__name__, self.data)
    
    def to_xml(self):
        inside = (
            GenXML.UVCoord(name="tl", u=tl.u, v=tl.v),
            GenXML.UVCoord(name="tr", u=tr.u, v=tr.v),
            GenXML.UVCoord(name="bl", u=bl.u, v=bl.v),
            GenXML.UVCoord(name="br", u=br.u, v=br.v),
        )
        return GenXML.UVCoords(*inside)

class Lyt1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)

    def validate(self):
        origin, w, h = self.read_format("I2f")
        self.data.size = Vec2(w, h)
        self.data.origin = usefulenums.OriginType(origin).name

    def to_xml(self):
        return GenXML.Layout(self.data.size.to_xml("size"), origin_type=self.data.origin)

class Fnl1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)
    
    def validate(self):
        number_fonts = self.read_format("I")
        font_start_off = self.index + self.start
        font_offsets = self.read_format("{}I".format(number_fonts), False)
        self.data.font_names = []
        for off in font_offsets:
            namoff = off + font_start_off
            name = []
            while True:
                c = self.read_off("1s", namoff)
                namoff += 1
                if c == b'\x00':
                    self.data.font_names.append("".join(name))
                    break
                else:
                    name.append(c.decode('ascii'))

class Txl1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)

    def validate(self):
        number_textures = self.read_format("I")
        textures_start_off = self.index + self.start
        textures_offsets = self.read_format("{}I".format(number_textures), False)
        self.data.texture_names = []
        for off in textures_offsets:
            namoff = off + textures_start_off
            name = []
            while True:
                c = self.read_off("1s", namoff)
                namoff += 1
                if c == b'\x00':
                    self.data.texture_names.append(b"".join(name).decode("utf-8"))
                    break
                else:
                    name.append(c)

class TexMapEntry:
    def __init__(self, parent):
        self.data = DataHolder()
        texture_index, val1, val2 = parent.read_format("H2B")
        self.data.texture_name = parent.parent.textures[texture_index]
        self.data.wrap_s_mode = usefulenums.WrapMode(val1 & 0x3).name
        self.data.min_filter_mode = usefulenums.FilterMode((val1 >> 2) & 0x3).name
        self.data.wrap_t_mode = usefulenums.WrapMode(val2 & 0x3).name
        self.data.max_filter_mode = usefulenums.FilterMode((val2 >> 2) & 0x3).name

    def to_xml(self):
        return GenXML.TexMapEntry(*attr_control(self.data))

class TexMatrixEntry:
    def __init__(self, parent):
        self.data = DataHolder()
        tx, ty, self.data.rotation, sx, sy = parent.read_format("5f")
        self.data.translation = Vec2(tx, ty)
        self.data.scale = Vec2(sx, sy)

    def to_xml(self):
        return GenXML.TexMatrixEntry(*attr_control(self.data))

class TexCoordGen:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.gen_type = usefulenums.MatrixType(parent.read_format("B")).name
        self.data.source = usefulenums.TextureGenerationType(parent.read_format("B")).name
        parent.read_format("2x")

    def to_xml(self):
        return GenXML.TexCoordGen(*attr_control(self.data))

class TevStage:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.rgb_mode, self.data.alpha_mode = parent.read_format("2B2x")

    def to_xml(self):
        return GenXML.TevStage(*attr_control(self.data))

class AlphaCompare:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.compare_mode, self.data.reference = parent.read_format("If")

    def to_xml(self):
        return GenXML.AlphaCompare(*attr_control(self.data))

class BlendMode:
    def __init__(self, parent):
        self.data = DataHolder()
        blend_operation, source_factor, dest_factor, logic_operation = parent.read_format("4B")
        self.data.blend_operation = usefulenums.Blend_BlendFactor(blend_operation).name
        self.data.source_factor = usefulenums.BlendMode_BlendOp(source_factor).name
        self.data.dest_factor = usefulenums.BlendMode_BlendOp(dest_factor).name
        self.data.logic_operation = usefulenums.Blend_LogicOp(logic_operation).name

class ColorBlendMode(BlendMode):
    def to_xml(self):
        return GenXML.ColorBlendMode(*attr_control(self.data))
class AlphaBlendMode(BlendMode):
    def to_xml(self):
        return GenXML.AlphaBlendMode(*attr_control(self.data))

class IndirectParam:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.rotation = parent.read_format("f")
        self.data.scale = Vec2(*parent.read_format("2f"))

    def to_xml(self):
        return GenXML.IndirectParam(*attr_control(self.data))

class ProjTexGenParam:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.pos = Vec2(*parent.read_format("2f"))
        self.data.scale = Vec2(*parent.read_format("2f"))
        flags = parent.read_format("B3x")
        self.data.fits_layout = bool(flags & 0x1)
        self.data.fits_panel = bool(flags & 0x2)
        self.data.adjust_projection_sr = bool(flags & 0x3)

    def to_xml(self):
        return GenXML.ProjTexGenParam(*attr_control(self.data))

class FontShadowParam:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.black_r, self.data.black_g, self.data.black_b, self.data.white_r, self.data.white_g, self.data.white_b, self.data.white_a = parent.read_format("7Bx")

    def to_xml(self):
        return GenXML.FontShadowParam(*attr_control(self.data))

class TevConstantColors:
    def __init__(self, colors):
        self.colors = list(map(RGBA, colors))

    def to_xml(self):
        cs = [GenXML.ColorIndex(str(c.index)) for c in self.colors]
        return GenXML.TevConstantColors(*cs)

class Material:
    def __init__(self, parent):
        self.data = DataHolder()
        self.data.name = parent.read_format("{}s".format(0x14)).rstrip(b"\x00").decode("utf-8")
        self.data.tev_color = RGBA(parent.read_format("I"))
        self.data.tev_constant_colors = TevConstantColors(parent.read_format("6I"))
        flags = parent.read_format("I")
        tex_maps_count = flags & 0b11
        tex_matrix_count = (flags >> 2) & 0b11
        tex_coordgen_count = (flags >> 4) & 0b11
        tev_stage_count = (flags >> 6) & 0b111
        alpha_compare = bool((flags >> 9) & 1)
        blend_mode = bool((flags >> 10) & 1)
        use_texture_only = bool((flags >> 11) & 1)
        separate_blend_mode = bool((flags >> 12) & 1)
        indirect_param = bool((flags >> 13) & 1)
        proj_tex_gen_param_count = (flags >> 14) & 0b11
        has_font_shadow_param = bool((flags >> 16) & 1)

        self.data.tex_maps = [TexMapEntry(parent) for i in range(tex_maps_count)]
        self.data.tex_matrixes = [TexMatrixEntry(parent) for i in range(tex_matrix_count)]
        self.data.tex_coords = [TexCoordGen(parent) for i in range(tex_coordgen_count)]
        self.data.tev_stages = [TevStage(parent) for i in range(tev_stage_count)]

        if alpha_compare:
            self.data.alpha_compare = AlphaCompare(parent)
        if blend_mode:
            self.data.color_blend_mode = ColorBlendMode(parent)
        if separate_blend_mode:
            self.data.alpha_blend_mode = AlphaBlendMode(parent)
        if indirect_param:
            self.data.indirect_param = IndirectParam(parent)

        self.data.proj_tex_gen_params = [ProjTexGenParam(parent) for i in range(proj_tex_gen_param_count)]

        if has_font_shadow_param:
            self.data.font_shadow_param = FontShadowParam(parent)

    def to_xml(self):
        return GenXML.Material(*attr_control(self.data))

class Mat1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)

    def validate(self):
        material_count = self.read_format("I")
        materials_offsets = self.read_format("{}I".format(material_count), False)
        self.data.materials = []
        for off in materials_offsets:
            self.index = off - 8
            self.data.materials.append(Material(self))

class Usd1_Entry:
    def __init__(self, data):
        start_pos = data.start + data.index
        name_offset = data.read_format("I")
        name_offset_used = name_offset + start_pos
        self.name = []
        while True:
            c = data.read_off("1s", name_offset_used)
            name_offset_used += 1
            if c == b'\x00':
                self.name = b"".join(self.name).decode("utf-8")
                break
            else:
                self.name.append(c)
        data_offset = data.read_format("I")
        setting, datatype = data.read_format("HBx")
        self.datatype = usefulenums.UsdEntryDataType(datatype)
        # print(hex(name_offset), hex(data_offset), hex(setting), self.datatype, self.name)
        data_offset += start_pos
        if self.datatype == usefulenums.UsdEntryDataType.String:  # string
            self.data = data.read_off("{}s".format(setting), data_offset ).rstrip(b"\x00").decode("utf-8")
            # print("Data name:", self.name, "A string of len", setting, ":", self.data)
        elif self.datatype == usefulenums.UsdEntryDataType.Ints:  # ints
            self.data = []
            for i in range(setting):
                self.data.append(data.read_off("i", data_offset + i * 4))
            # print("Data name:", self.name, setting, "integers:", self.data)
        elif self.datatype == usefulenums.UsdEntryDataType.Floats:  # floats
            self.data = []
            for i in range(setting):
                self.data.append(data.read_off("f", data_offset + i * 4))
            # print("Data name:", self.name, setting, "floats:", self.data)

    def to_xml(self):
        inside = None
        dt = self.datatype.value
        if dt == 0:
            inside = [GenXML.String(self.data)]
        elif dt == 1:
            inside = [GenXML.Integer(str(d)) for d in self.data]
        elif dt == 2:
            inside = [GenXML.Float(str(d)) for d in self.data]
        return GenXML.Data(*inside, {"name": self.name, "type": self.datatype.name})

    def __str__(self):
        return str(self.__dict__)
    def __repr__(self):
        return str(self)

class Usd1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)

    def validate(self):
        number_entries = self.read_format("I")
        self.data.entries = [Usd1_Entry(self) for i in range(number_entries)]

class Pan1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)

    def validate(self):
        flags, origin, alpha, magnification_flags = self.read_format("4B")
        self.data.flags = usefulenums.PanelFlags(flags).name
        self.data.origin = Vec2(usefulenums.OriginHorizontal((origin >> 6) & 0b11).name, usefulenums.OriginVertical((origin >> 4) & 0b11).name)
        self.data.parent_origin = Vec2(usefulenums.OriginHorizontal((origin >> 2) & 0b11).name, usefulenums.OriginVertical((origin) & 0b11).name)
        self.data.alpha = alpha
        self.data.magnification_flags = usefulenums.PanelMagnificationFlags(magnification_flags).name
        self.data.name = self.read_format("{}s".format(0x18)).rstrip(b"\x00").decode("utf-8")
        x, y, z = self.read_format("3f")
        self.data.translation = Vec3(x, y, z)
        x, y, z = self.read_format("3f")
        self.data.rotation = Vec3(x, y, z)
        x, y = self.read_format("2f")
        self.data.scale = Vec2(x, y)
        x, y = self.read_format("2f")
        self.data.size = Vec2(x, y)

    def __str__(self):
        return "{}({})".format(type(self).__name__, self.data)

class TextureCoords(DataHolder):
    pass

class Pic1(Pan1):
    def __init__(self, bclyt, data, s=0, e=None):
        Pan1.__init__(self, bclyt, data, s, e)

    def validate(self):
        Pan1.validate(self)
        self.data.tl_color, self.data.tr_color, self.data.bl_color, self.data.br_color = map(RGBA, self.read_format("4I"))
        material_index, texture_coord_count = self.read_format("2H")
        self.data.material_name = self.parent.materials[material_index].data.name
        self.data.texture_coords = [TextureCoords() for i in range(texture_coord_count)]
        for holder in self.data.texture_coords:
            coords = self.read_format("8f")
            holder.TopLeft, holder.TopRight, holder.BottomLeft, holder.BottomRight = map(lambda x: Vec2(*x), zip(coords[::2], coords[1::2]))

class Txt1(Pan1):
    def __init__(self, bclyt, data, s=0, e=None):
        Pan1.__init__(self, bclyt, data, s, e)

    def validate(self):
        Pan1.validate(self)
        max_size, text_size = self.read_format("2H")
        self.data.additional_chars = (max_size - text_size) >> 1
        material_index, font_index = self.read_format("2H")
        self.data.material_name = self.parent.materials[material_index].data.name
        self.data.font_name = self.parent.fonts[font_index]
        another_origin, line_alignment = self.read_format("2B2x")
        self.data.another_origin = Vec2(usefulenums.OriginHorizontal((another_origin >> 2) & 0b11).name, usefulenums.OriginVertical((another_origin) & 0b11).name)
        self.data.line_alignment = usefulenums.LineAlignment(line_alignment).name
        text_offset = self.read_format("I") + self.start - 8
        self.data.top_color, self.data.bottom_color = map(RGBA, self.read_format("2I"))
        self.data.text_size = Vec2(*self.read_format("2f"))
        self.data.character_size, self.data.line_size = self.read_format("2f")
        self.data.text = self.read_off("{}s".format(text_size), text_offset).rstrip(b"\x00")
        if len(self.data.text) & 1:
            self.data.text += b"\x00"
        try:
            converted = self.data.text.decode("utf-16le")
            self.data.text = converted
        except UnicodeDecodeError as e:
            print(e)
            print(self.data.text.hex())
            self.data.text ="!!!DECODE ERROR!!!"

class Wnd1Frame:
    def __init__(self, parent, off, materials):
        material_index, self.flip_type = parent.read_off("HBx", off)
        self.material_name = materials[material_index].data.name

    def to_xml(self):
        return GenXML.WindowFrame(material=self.material_name, flip=str(self.flip_type))

class Wnd1(Pan1):
    def __init__(self, bclyt, data, s=0, e=None):
        Pan1.__init__(self, bclyt, data, s, e)

    def validate(self):
        Pan1.validate(self)
        self.data.content_overflow_l, self.data.content_overflow_r, self.data.content_overflow_t, self.data.content_overflow_b = self.read_format("4f")
        frame_count, self.data.flag = self.read_format("2B2x")
        content_offset, frame_offsets_offset = self.read_format("2I")
        self.data.tl_color, self.data.tr_color, self.data.bl_color, self.data.br_color = map(RGBA, self.read_format("4I"))
        material_index, uv_set_count = self.read_format("2H")
        self.data.material_name = self.parent.materials[material_index].data.name
        self.data.uvsets = list(map(UVCoordSet, splitarray(self.read_format("{}f".format(8 * uv_set_count)), 8)))
        frame_offsets = self.read_off("{}I".format(frame_count), self.start + frame_offsets_offset - 8, False)
        self.data.frames = [Wnd1Frame(self, self.start + off - 8, self.parent.materials) for off in frame_offsets]

class PanelWrapper:
    def __init__(self, pan):
        self.pan = pan
        self.parent = None
        self.userdata = []
        self.children = []

    def print_info(self):
        print(self)
        for child in self.children:
            child.print_info()

    def __str__(self):
        parentstr = "" if self.parent is None else " child of " + self.parent.pan.data.name
        userdatastr = "" if len(self.userdata) == 0 else "\nUserdata\n- {}".format("\n- ".join(map(str, self.userdata)))
        return "Panel {} with {} children{}\nData: {}{}".format(self.pan.data.name, len(self.children), parentstr, self.pan, userdatastr)

    def to_xml(self):
        attributes = {"type": type(self.pan).__name__}
        data = GenXML.PanelData(*attr_control(self.pan.data))
        userdata = []
        if self.userdata:
            userdata = [GenXML.UserData(*[u.to_xml() for u in self.userdata])]
        children = [c.to_xml() for c in self.children]
        pan = GenXML.Panel(
            data,
            *userdata,
            *children,
            attributes
        )
        return pan

class Grp1(ReaderThingy):
    def __init__(self, bclyt, data, s=0, e=None):
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e, parent=bclyt)

    def validate(self):
        self.data.name = self.read_format("16s").rstrip(b"\x00").decode("utf-8")
        panels_amount = self.read_format("I")
        self.data.panels = [self.read_format("16s").rstrip(b"\x00").decode("utf-8") for i in range(panels_amount)]

    def __str__(self):
        return "Grp1({})".format(self.data)
    def __repr__(self):
        return str(self)

class GroupWrapper:
    def __init__(self, grp):
        self.grp = grp
        self.parent = None
        self.children = []

    def print_info(self):
        print(self)
        for child in self.children:
            child.print_info()

    def __str__(self):
        parentstr = "" if self.parent is None else " child of " + self.parent.grp.data.name
        return "Group {} with {} children{}\nData: {}".format(self.grp.data.name, len(self.children), parentstr, self.grp)

    def to_xml(self):
        attributes = {"name": self.grp.data.name, "panels_count": str(len(self.grp.data.panels))}
        panels = [GenXML.PanelRef({"name": ref}) for ref in self.grp.data.panels]
        children = [c.to_xml() for c in self.children]
        grp = GenXML.Group(
            *panels,
            *children,
            attributes
        )
        return grp

class BCLYT(ReaderThingy):
    def __init__(self, data, s=0, e=None):
        RGBA.MAPPED_COLORS.clear()
        ReaderThingy.__init__(self, data, s, len(data) if e is None else e)

    def validate(self):
        assert(self.read_format("4s") == b"CLYT")
        assert(self.read_format("H") == 0xfeff)

        assert(self.read_format("H") == 0x14)
        revision, filesize, self.sections_count = self.read_format("3I")

        self.layout = None

        self.root_panel = None
        self.current_panel = None

        self.root_group = None
        self.current_group = None

        self.fonts = []
        self.textures = []
        self.materials = []

        for i in range(self.sections_count):
            self.read_section()

    def read_layout(self, data, s=0, e=None):
        assert(self.layout is None)
        self.layout = Lyt1(self, data, s, e)

    def read_font_loader(self, data, s=0, e=None):
        assert(len(self.fonts) == 0)
        fnl = Fnl1(self, data, s, e)
        self.fonts = fnl.data.font_names

    def read_textures_loader(self, data, s=0, e=None):
        assert(len(self.textures) == 0)
        txl = Txl1(self, data, s, e)
        self.textures = txl.data.texture_names

    def read_material(self, data, s=0, e=None):
        assert(len(self.materials) == 0)
        mat = Mat1(self, data, s, e)
        self.materials = mat.data.materials

    def read_panel(self, data, s=0, e=None):
        wrapper = PanelWrapper(Pan1(self, data, s, e))
        if self.current_panel is None:
            self.root_panel = wrapper
        else:
            wrapper.parent = self.current_panel
            self.current_panel.children.append(wrapper)

    def read_panel_start(self, data, s=0, e=None):
        if self.current_panel is None:
            self.current_panel = self.root_panel
        else:
            self.current_panel = self.current_panel.children[-1]

    def read_panel_end(self, data, s=0, e=None):
        self.current_panel = self.current_panel.parent

    def read_picture(self, data, s=0, e=None):
        wrapper = PanelWrapper(Pic1(self, data, s, e))
        wrapper.parent = self.current_panel
        self.current_panel.children.append(wrapper)

    def read_text(self, data, s=0, e=None):
        wrapper = PanelWrapper(Txt1(self, data, s, e))
        wrapper.parent = self.current_panel
        self.current_panel.children.append(wrapper)

    def read_window(self, data, s=0, e=None):
        wrapper = PanelWrapper(Wnd1(self, data, s, e))
        wrapper.parent = self.current_panel
        self.current_panel.children.append(wrapper)

    def read_userdata(self, data, s=0, e=None):
        userdata = Usd1(self, data, s, e)
        self.current_panel.children[-1].userdata.extend(userdata.data.entries)

    def read_group(self, data, s=0, e=None):
        wrapper = GroupWrapper(Grp1(self, data, s, e))
        if self.current_group is None:
            self.root_group = wrapper
        else:
            wrapper.parent = self.current_group
            self.current_group.children.append(wrapper)

    def read_group_start(self, data, s=0, e=None):
        if self.current_group is None:
            self.current_group = self.root_group
        else:
            self.current_group = self.current_group.children[-1]

    def read_group_end(self, data, s=0, e=None):
        self.current_group = self.current_group.parent

    def read_section(self):
        self.magic, size = self.read_format("4sI")

        handlers = {
            b'lyt1': self.read_layout,
            b'txl1': self.read_textures_loader,
            b'fnl1': self.read_font_loader,
            b'mat1': self.read_material,

            b'pan1': self.read_panel,
            b'pas1': self.read_panel_start,
            b'pae1': self.read_panel_end,

            b'wnd1': self.read_window,
            b'usd1': self.read_userdata,
            b'pic1': self.read_picture,
            b'txt1': self.read_text,

            b'grp1': self.read_group,
            b'grs1': self.read_group_start,
            b'gre1': self.read_group_end
        }

        size -= 8
        try:
            # print("Doing", self.magic, "of size", hex(size), "at", hex(self.index))
            handlers[self.magic](self.view, self.index, size)
            # print("Done with", self.magic, "of size", hex(size))
            self.index += size
        except KeyError as e:
            print("Unknown key:", self.magic)
            raise e
    
    def to_xml(self):
        colors = [GenXML.Color(index=str(i), r=str(c.r), g=str(c.g), b=str(c.b), a=str(c.a)) for i, c in enumerate(RGBA.MAPPED_COLORS)]
        fonts = [GenXML.Font(f) for f in self.fonts]
        textures = [GenXML.Texture(t) for t in self.textures]
        mats = [m.to_xml() for m in self.materials]
        root = GenXML.BCLYT(
            self.layout.to_xml(),
            GenXML.Colors(*colors),
            GenXML.Textures(*textures),
            GenXML.Fonts(*fonts),
            GenXML.Materials(*mats),
            self.root_panel.to_xml(),
            self.root_group.to_xml()
        )
        return root
