from enum import Enum

class WrapMode(Enum):
    Clamp = 0
    Repeat = 1
    Mirror = 2

class FilterMode(Enum):
    Near = 0
    Linear = 1

class MatrixType(Enum):
    Matrix_2x4 = 0

class TextureGenerationType(Enum):
    Tex0 = 0
    Tex1 = 1
    Tex2 = 2
    Ortho = 3
    PaneBased = 4
    PerspectiveProj = 5

class Blend_BlendFactor(Enum):
    Factor0 = 0
    Factor1 = 1
    DestColor = 2
    DestInvColor = 3
    SourceAlpha = 4
    SourceInvAlpha = 5
    DestAlpha = 6
    DestInvAlpha = 7
    SourceColor = 8
    SourceInvColor = 9

class BlendMode_BlendOp(Enum):
    Disable = 0
    Add = 1
    Subtract = 2
    ReverseSubtract = 3
    SelectMin = 4
    SelectMax = 5

class Blend_LogicOp(Enum):
    Disable = 0
    NoOp = 1
    Clear = 2
    Set = 3
    Copy = 4
    InvCopy = 5
    Inv = 6
    And = 7
    Nand = 8
    Or = 9
    Nor = 10
    Xor = 11
    Equiv = 12
    RevAnd = 13
    InvAd = 14
    RevOr = 15
    InvOr = 16

class OriginType(Enum):
    Classic = 0
    Normal = 1

class UsdEntryDataType(Enum):
    String = 0
    Ints = 1
    Floats = 2

class OriginHorizontal(Enum):
    Center = 0
    Left = 1
    Right = 2

class OriginVertical(Enum):
    Middle = 0
    Top = 1
    Bottom = 2

class LineAlignment(Enum):
    NoAlign = 0
    Left = 1
    Center = 2
    Right = 3

class PanelFlags(Enum):
    Visible = 0
    InfluencedAlpha = 1
    LocationAdjust = 2

class PanelMagnificationFlags(Enum):
    IgnorePartsMagnify = 0
    AdjustToPartsBounds = 1

class ImageFormats(Enum):
    L8 = 0x00
    A8 = 0x01
    LA4 = 0x02
    LA8 = 0x03
    HILO8 = 0x04
    RGB565 = 0x05
    RGB8 = 0x06
    RGB5A1 = 0x07
    RGBA4 = 0x08
    RGBA8 = 0x09
    ETC1 = 0x0A
    ETC1A4 = 0x0B
    L4 = 0x0C
    A4 = 0x0D
