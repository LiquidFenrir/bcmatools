import os
import sys
import contextlib

from lxml import etree
from lxml.builder import E as GenXML

from internal import lzss3_dec, extraction, my_rle

def do_arc(fn, outfolder):
    with open(fn, "rb") as f:
        data = f.read()
        try:
            newdata = lzss3_dec.decompress_bytes(data)
            print("DARC was LZ compressed")
            data = newdata
        except lzss3_dec.DecompressionError:
            pass
        mainarc = extraction.DARC(data)

    for k, v in mainarc.data.files.items():
        p = os.path.join(outfolder, k)
        print("File path:", p)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(v)
        if k.endswith(".arc"):
            do_arc(p, os.path.join(outfolder, os.path.splitext(k)[0]))
        # elif k.endswith(".bclim"):
        #     with open(os.path.join(outfolder, k), "rb") as f:
        #         extraction.BCLIM(f.read())

def do_single_bclyt(filepath, savepos):
    with open(filepath, "rb") as f:
        extraction.BCLYT(f.read()).to_xml().getroottree().write(savepos, pretty_print=True, xml_declaration=True, encoding='utf-8')

def do_bclyt(name, savepos):
    regions = ["EUR", "USA", "CHN", "TWN", "JPN", "KOR"]
    types = ["small", "large", "index", "BcmaInfo"]
    images = {}
    langs = {
        "EUR": ["fr", "en", "ru", "pt", "nl", "es", "it", "de"],
        "USA": ["en", "es", "fr"],
        "JPN": ["ja"],
        "TWN": ["tc"],
        "CHN": ["sc"],
        "KOR": ["ko"],
    }
    indexes = {r: {l: None for l in langs[r]} for r in regions}
    pages = {r: {l: {} for l in langs[r]} for r in regions}
    bcmainfo = etree.Element("BcmaInfo")

    for root, dirs, files in os.walk(name):
        for filename in files:
            if filename.endswith(".bclim"):
                arcname = os.path.split(os.path.split(root)[0])[1]
                i = images.get(arcname, {})
                fullpath = os.path.join(root, filename)
                with open(fullpath, "rb") as f:
                    i[os.path.splitext(filename)[0]] = my_rle.do_compression(f.read().hex())
                if len(i) == 1:
                    images[arcname] = i
            elif not filename.endswith(".bclyt"):
                continue

            fullpath = os.path.join(root, filename)
            # print(fullpath)

            typ = None
            for t in types:
                if t in root:
                    typ = t
                    break
            if typ is None:
                continue

            reg = None
            lng = None
            if typ != "BcmaInfo":
                for r in regions:
                    if r + "_" in root:
                        reg = r
                        break
                if reg is None:
                    print("Unknown region for", root)
                    continue

                for l in langs[reg]:
                    if "_" + l + "_" in root:
                        lng = l
                        break
                if lng is None:
                    print("Unknown language for", root)
                    continue

            page = None
            sub_page = None
            if typ != "BcmaInfo" and typ != "index":
                page = filename[5:8]
                sub_page = filename.split("_")[-1].split(".")[0]

            with open(fullpath, "rb") as f:
                print(fullpath)
                x = extraction.BCLYT(f.read()).to_xml()
                if typ == "BcmaInfo":
                    bcmainfo.append(x.getroottree().getroot())
                elif typ == "index":
                    indexes[reg][lng] = GenXML.Index(x)
                else:
                    p = pages[reg][lng].get(page, {})
                    p[typ, sub_page] = x
                    if len(p) == 1:
                        pages[reg][lng][page] = p

    root = etree.Element("Manual")
    image_arcs = []
    for arc, imgs in images.items():
        imgs_x = []
        for imgname, imgdata in imgs.items():
            imgs_x.append(GenXML.Image(imgdata, name=imgname))
        image_arcs.append(GenXML.ImageArc(*imgs_x, name=arc))
    root.append(GenXML.ImageArcs(*image_arcs).getroottree().getroot())
    root.append(bcmainfo)
    for r in regions:
        langs_x = []
        for l in langs[r]:
            idx = indexes[r][l]
            if idx is not None:
                ps = [idx]
                for pnumber, v in pages[r][l].items():
                    ps_i = []
                    for (ptype, subpnum), v2 in v.items():
                        ps_i.append(GenXML.SubPage(v2, pagesize=ptype, subpage=subpnum))
                    ps.append(GenXML.Page(*ps_i, page=str(pnumber)))
                if len(ps):
                    langs_x.append(GenXML.Pages(*ps, lang=l))
        if len(langs_x):
            root.append(GenXML.Region(*langs_x, region=r).getroottree().getroot())
    etree.ElementTree(root).write(savepos, pretty_print=True, xml_declaration=True, encoding='utf-8')

if __name__ == "__main__":
    handlers = {
        "arc": do_arc,
        "bclyt": do_bclyt,
        "single": do_single_bclyt,
    }

    if len(sys.argv) == 4:
        try:
            h = handlers[sys.argv[1]]
        except KeyError:
            print("Unkown action:", sys.argv[1])
        else:
            h(sys.argv[2], sys.argv[3])
            print("Complete")
    else:
        print("Usage: {} <{}> <input path> <output path>".format(sys.argv[0], "|".join(map(str, handlers))))
        sys.exit(0)
