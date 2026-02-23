
from .base import Registry, CategoryRegistry
from ..log import logger
from colorama import Fore, Style, init
init(autoreset=True)

categories = CategoryRegistry(str, int)

def help_categories(_dict):
    # list sorted by code
    items = sorted(_dict._data.items(), key=lambda kv: int(kv[1]))

    shift = getattr(_dict, "_shift", 8)
    levels = getattr(_dict, "_levels", 4)
    mask = (1 << shift) - 1

    def split_levels(code: int):
        parts = []
        for i in range(levels):
            s = (levels - 1 - i) * shift
            parts.append((code >> s) & mask)
        while parts and parts[-1] == 0:
            parts.pop()
        return parts

    rows = []
    for name, val in items:
        code = int(val)
        parts = split_levels(code)
        parts_str = ".".join(f"{p:02X}" for p in parts) if parts else "00"
        rows.append((name, f"0x{code:0{levels*2}X}", parts_str))

    # compute column widths and render
    name_w = max(len("Name"), max(len(r[0]) for r in rows))
    code_w = max(len("Code"), max(len(r[1]) for r in rows))
    lvl_w  = max(len("Levels"), max(len(r[2]) for r in rows))
    hdr = f"{'Name':{name_w}}  {'Code':{code_w}}  {'Levels':{lvl_w}}"
    sep = "-" * (name_w + code_w + lvl_w + 4)
    lines = [hdr, sep] + [f"{n:{name_w}}  {c:{code_w}}  {l:{lvl_w}}" for n, c, l in rows]
    logger.info("\n" + "\n".join(lines))
    
    
categories.set_help(help_categories)

categories.add_category("Deform", value=60)
categories.add_category("Image Processing", value=64)
categories.add_category("Align", value=68)
categories.add_category("Reconstruct", value=72)
categories.add_category("Project", value=76)
categories.add_category("Segment", value=80)
categories.add_category("Analyze", value=84)