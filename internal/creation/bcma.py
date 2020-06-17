from io import BytesIO

from lxml import etree
from nlzss3 import compress

from internal import usefulenums, my_rle
from .darc import DARC
from . import bclyt

class BCMA:
    def __init__(self, file_obj):
        self.common_images = {}
        self.specific_images = {}
        self.indexes = {}
        self.small_pages = {}
        self.large_pages = {}
        self.languages = []
        tree = etree.parse(file_obj)
        root = tree.getroot()
        assert(root.tag == "Manual")
        for child in root:
            if child.tag == "ImageArcs":
                for imagearc in child:
                    arcname = imagearc.get("name")
                    if arcname == "Common_texture":
                        images_go_here = self.common_images
                    else:
                        images_go_here = self.specific_images[arcname] = {}
                    for image in imagearc:
                        imgname = image.get("name")
                        # print("Found", imgname, "of", arcname)
                        images_go_here[imgname] = bytes.fromhex(my_rle.do_decompression(image.text))
            elif child.tag == "BcmaInfo":
                self.bcma_info = bclyt.BCLYT(child[0])
            elif child.tag == "Region":
                region = child.get("region")
                for language in child:
                    assert(language.tag == "Pages")
                    lang = language.get("lang")
                    full_lang = f"{region}_{lang}"
                    for page in language:
                        if page.tag == "Index":
                            # print("Found index of", full_lang)
                            bclyt.USD_TYPE_OVERRIDE = 2
                            self.indexes[full_lang] = bclyt.BCLYT(page[0])
                            bclyt.USD_TYPE_OVERRIDE = 1
                        elif page.tag == "Page":
                            for subpage in page:
                                assert(subpage.tag == "SubPage")
                                pnum = page.get('page')
                                psize = subpage.get('pagesize')
                                subpnum = subpage.get('subpage')
                                if subpnum == "info":
                                    bclyt.USD_TYPE_OVERRIDE = -1
                                full_page = f"Page_{pnum}_{psize}_{subpnum}"
                                # print("Found", full_page, "of", full_lang)
                                if psize == "small":
                                    arr = self.small_pages.get(full_lang, [])
                                    # set the pages to point to the newly created list
                                    if len(arr) == 0:
                                        self.small_pages[full_lang] = arr
                                elif psize == "large":
                                    arr = self.large_pages.get(full_lang, [])
                                    # set the pages to point to the newly created list
                                    if len(arr) == 0:
                                        self.large_pages[full_lang] = arr
                                else:
                                    raise ValueError(f"Unknown pagesize at SubPage level: {psize}")
                                arr.append((full_page, bclyt.BCLYT(subpage[0])))
                                bclyt.USD_TYPE_OVERRIDE = 1
                        else:
                            raise ValueError(f"Unknown tag at Pages level: {page.tag}")
                    self.languages.append(full_lang)
            else:
                raise ValueError(f"Unknown tag at Manual level: {child.tag}")

    def write_to_file(self, out):
        self.internal_darcs = []

        bclytbytes = BytesIO()
        self.bcma_info.write_to_file(bclytbytes)
        tree_structure = {
            "BcmaInfo.bclyt": bclytbytes.getbuffer()
        }
        self.internal_darcs.append(("BcmaInfo", DARC({"blyt": tree_structure})))

        print("Built BcmaInfo DARC")

        tree_structure = {}
        for image_name, image_data in self.common_images.items():
            tree_structure[f"{image_name}.bclim"] = image_data
        self.internal_darcs.append(("Common_texture", DARC({"timg": tree_structure}, 0x100, 0x80)))

        print("Built Common_texture DARC")

        for imagarc, arcdata in self.specific_images.items():
            tree_structure = {}
            for image_name, image_data in arcdata.items():
                tree_structure[f"{image_name}.bclim"] = image_data
            self.internal_darcs.append((imagarc, DARC({"timg": tree_structure}, 0x100, 0x80)))

        print("Built remaining texture DARCs")

        self.languages.sort()
        for reglang in self.languages:
            bclytbytes = BytesIO()

            self.indexes[reglang].write_to_file(bclytbytes)
            tree_structure = {
                "Index.bclyt": bclytbytes.getbuffer()
            }
            self.internal_darcs.append((f"{reglang}_index", DARC({"blyt": tree_structure})))

            tree_structure = {}
            for name, large_page in self.large_pages[reglang]:
                bclytbytes = BytesIO()
                large_page.write_to_file(bclytbytes)
                n = f"{name}.bclyt"
                tree_structure[n] = bclytbytes.getvalue()
            self.internal_darcs.append((f"{reglang}_large", DARC({"blyt": tree_structure}, file_padding_part=0x4)))

            tree_structure = {}
            for name, small_page in self.small_pages[reglang]:
                bclytbytes = BytesIO()
                small_page.write_to_file(bclytbytes)
                n = f"{name}.bclyt"
                tree_structure[n] = bclytbytes.getvalue()
            self.internal_darcs.append((f"{reglang}_small", DARC({"blyt": tree_structure}, file_padding_part=0x4)))

        print("Built DARCs")

        tree_structure = {}
        for darc_name, darc in self.internal_darcs:
            darc_bytes = BytesIO()
            darc.write_to_file(darc_bytes)
            print("Compressing", darc_name)
            tree_structure[f"{darc_name}.arc"] = compress(darc_bytes.getvalue())
        final_darc = DARC(tree_structure, 0x20)
        final_darc.write_to_file(out)
