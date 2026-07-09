from sys import argv
from io import BufferedRandom
import json
import zipfile

def update_shop_text_lengths(f: BufferedRandom, start_addr: int):
    f.seek(start_addr)
    base: int = int.from_bytes(f.read(4), "big")
    addr: int = base
    for _ in range(7):
        addr += 41
        f.write(addr.to_bytes(4, "big"))

def update_item_text(f: BufferedRandom, location: int, player: str, item: str, flags: int):
    location_to_addr: dict[int, int] = {
        0x80E553F201: 0x27C0BBB8,
        0x80E553F301: 0x27C0C27A,
        0x80E554BF01: 0x27C0B79E,
        0x80E554C001: 0x27C0B7F0,
        0x80E554C101: 0x27C0B842,
        0x80E554C201: 0x27C0B894,
        0x80E554C301: 0x27C0B8E6,
        0x80E554C401: 0x27C0B938,
        0x80E554C501: 0x27C0B98A,
        0x80E554C601: 0x27C0B9DC,
        0x80E554CF01: 0x27C0BE20,
        0x80E554D001: 0x27C0BE72,
        0x80E554D101: 0x27C0BEC4,
        0x80E554D201: 0x27C0BF16,
        0x80E554D301: 0x27C0BF68,
        0x80E554D401: 0x27C0BFBA,
        0x80E554D501: 0x27C0C00C,
        0x80E554D601: 0x27C0C05E,
        0x80E554DF01: 0x27C0D18A,
        0x80E554E001: 0x27C0D1DC,
        0x80E554E101: 0x27C0D22E,
        0x80E554E201: 0x27C0D280,
        0x80E554E301: 0x27C0D2D2,
        0x80E554E401: 0x27C0D324,
        0x80E554E501: 0x27C0D376,
        0x80E554E601: 0x27C0D3C8,
        0x80E554EF01: 0x27C0CBA8,
        0x80E554F001: 0x27C0CBFA,
        0x80E554F101: 0x27C0CC4C,
        0x80E554F201: 0x27C0CC9E,
        0x80E554F301: 0x27C0CCF0,
        0x80E554F401: 0x27C0CD42,
        0x80E554F501: 0x27C0CD94,
        0x80E554F601: 0x27C0CDE6,
        0x80E554FF01: 0x27C0C502,
        0x80E5550001: 0x27C0C554,
        0x80E5550101: 0x27C0C5A6,
        0x80E5550201: 0x27C0C5F8,
        0x80E5550301: 0x27C0C64A,
        0x80E5550401: 0x27C0C69C,
        0x80E5550501: 0x27C0C6EE,
        0x80E5550601: 0x27C0C740,
        0x80E5550F01: 0x27C0DFF0,
        0x80E5551001: 0x27C0E042,
        0x80E5551101: 0x27C0E094,
        0x80E5551201: 0x27C0E0E6,
        0x80E5551301: 0x27C0E138,
        0x80E5551401: 0x27C0E18A,
        0x80E5551501: 0x27C0E1DC,
        0x80E5551601: 0x27C0E22E,
        0x80E5551701: 0x27C0E284,
        0x80E5551801: 0x27C0E306,
        0x80E5551901: 0x27C0E384,
    }
    f.seek(location_to_addr[location])
    for c in player:
        if c.isspace():
            f.write(bytes([0x00, 0x20]))
        elif c.isascii():
            f.write(bytes([0xFF, ord(c)-0x20]))
        else:
            f.write(bytes([0xFF, 0x1F]))
    f.write(bytes([0xFF, 0x07, 0xFF, 0x53, 0x00, 0x20]))
    if flags & 0b011 == 0b011:
        f.write(bytes([0xF0, 0x09]))
    elif flags & 0b001:
        f.write(bytes([0xF0, 0x03]))
    elif flags & 0b010:
        f.write(bytes([0xF0, 0x08]))
    elif flags & 0b100:
        f.write(bytes([0xF0, 0x01]))
    else:
        f.write(bytes([0xF0, 0x0A]))
    for c in item[:20]:
        if c.isspace():
            f.write(bytes([0x00, 0x20]))
        elif c.isascii():
            f.write(bytes([0xFF, ord(c)-0x20]))
        else:
            f.write(bytes([0xFF, 0x1F]))
    f.write(bytes([0x00, 0x00]))

def update_goal_characters(f: BufferedRandom, goal_characters: int):
    for addr in [0x27BE2C52, 0x27BE2CEC, 0x27BFD5C6]:
        f.seek(addr)
        if goal_characters > 9:
            f.write(bytes([0xFF, 0x10 + (goal_characters // 10)]))
        else:
            f.seek(2, 1)
        f.write(bytes([0xFF, 0x10 + (goal_characters % 10)]))

with zipfile.ZipFile(argv[1]) as patch:
    manifest = json.load(patch.open("archipelago.json"))
    if manifest["patch_version"] == 0:
        f = open("tmp/DATA/files/dt_na.dat", "r+b")
        update_shop_text_lengths(f, 0x27BE1A88)
        update_shop_text_lengths(f, 0x27BE1AEC)
        update_shop_text_lengths(f, 0x27BE1B50)
        update_shop_text_lengths(f, 0x27BE1BB4)
        update_shop_text_lengths(f, 0x27BE1C10)
        update_shop_text_lengths(f, 0x27BE1CDC)
        # point Luigi's Flashlight in Secret Shop to Blue Pianta's shop
        f.seek(0x27BE1D08)
        f.write(0x14DAC.to_bytes(4, "big"))
        data = json.load(patch.open("mss.json"))
        update_goal_characters(f, data["goal_characters"])
        for location in data["locations"]:
            update_item_text(f, location["id"], location["player"], location["item"], location["flags"])
        f.close()
    else:
        print("Unsupported patch file version. Please update the patcher.")
