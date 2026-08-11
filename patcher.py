from sys import argv
from io import BufferedRandom
import json
import random
import zipfile

def calc_dol_offset(addr: int) -> int:
    if addr < 0x80622C00:
        return addr - 0x80060300
    else:
        return addr - 0x80003F00

def read_str(f: BufferedRandom, offset: int) -> str:
    f.seek(0x27BE2060 + offset * 2)
    s = ""
    c = f.read(2)
    while c != bytes([0,0]):
        if c[0] == 0: s += " "
        elif c[0] == 0xFF: s += chr(c[1] + 0x20)
        c = f.read(2)
    return s

def write_str(f: BufferedRandom, s: str) -> None:
    for c in s:
        if c.isspace():
            f.write(bytes([0x00, ord(c)]))
        elif c.isascii():
            f.write(bytes([0xFF, ord(c)-0x20]))
        else:
            f.write(bytes([0xFF, 0x1F]))
    f.write(bytes([0x00, 0x00]))

def apply_base_patch(h: BufferedRandom, dol: BufferedRandom, v: int) -> None:
    MOVED_FLAGS = [
        0x8006BABA, 0x801945B6, 0x80194626, 0x8019466A, 0x801946DA, 0x801960AA, 0x8019619E, 0x801962AA, 0x801964E2,
        0x80196C62, 0x80196CAE, 0x801BE38E, 0x801C35D2, 0x801C360E, 0x801C367E, 0x801C3C9E, 0x801C3F22, 0x801C4196,
        0x801C41B6, 0x801C41D6, 0x801C41F6, 0x801C4216, 0x801C4236, 0x801C4256, 0x801C4772, 0x801C4EDA, 0x801C522E,
        0x801C69D6, 0x801C6B6E, 0x801C6E86, 0x801C8042, 0x801C8152, 0x801C8322, 0x801D8606, 0x801D8632, 0x801D9526,
        0x801D954A, 0x801D956E, 0x801D9592, 0x801D95B6, 0x801D95DA, 0x801D95FE, 0x801E304E, 0x801E34A2, 0x801E824E,
        0x801E8272, 0x801E8DF6, 0x801EBCFE, 0x801EBD1A, 0x801EEBB6, 0x801EEBD6, 0x801EEBFA, 0x801EEC1E, 0x801EEC42,
        0x801EEECA, 0x801F4BC6, 0x801F524E, 0x801F5A0A, 0x801F5C0E, 0x801F5D62, 0x801F62D6, 0x801F69EE, 0x801F6EC6,
        0x801F768E, 0x802024AA, 0x80202522, 0x8020253A, 0x802025B2, 0x802025BE, 0x80202636, 0x80203382, 0x80204FFA,
        0x80207B8E, 0x80207BBA, 0x80207BE2, 0x80207C0E, 0x80207C36, 0x80207C62, 0x8020BCBA, 0x8020BCC6, 0x8020BF36,
        0x8020C43A, 0x8020EEAE, 0x8020F482, 0x802153EE, 0x80231906, 0x80231A86, 0x80231CEA, 0x8023405A
    ]

    ZERO_SHORTS = [
        0x80657A3C, 0x80657A3E, 0x80657A40, 0x80657A42, 0x80657A44, 0x80657A46, 0x80657A48, 0x80657A4A, 0x80657A4C,
        0x80657A4E, 0x80657A50, 0x80657A52, 0x80657A54, 0x80657A56, 0x80657A70, 0x80657A72, 0x80657A74, 0x80657A76,
        0x80657A78, 0x80657A7A, 0x80657A7C, 0x80657A7E, 0x80657A80, 0x80657A82, 0x80657A84, 0x80657A86, 0x80657A88,
        0x80657A8A, 0x80657A8C, 0x80657A8E, 0x80657A90, 0x80657A7C, 0x80657AB4, 0x80657AB6, 0x80657AB8, 0x80657ABA,
        0x80657AC0, 0x80657AC2, 0x80657AC4, 0x80657AC6, 0x80657AC8, 0x80657ACA, 0x80657AD8, 0x80657ADA, 0x80657ADC,
        0x80657ADE, 0x80657AE0, 0x80657AE2, 0x80657AE4, 0x80657AE6, 0x80657AE8, 0x80657AEA, 0x80657AEC, 0x80657AEE,
        0x80657AF0, 0x80657AF2, 0x80657AF4, 0x80657AF6, 0x80657AF8, 0x80657AFA, 0x80657AFC, 0x80657AFE, 0x80657B0C,
        0x80657B0E, 0x80657B10, 0x80657B12, 0x80657B14, 0x80657B16, 0x80657B18, 0x80657B1A, 0x80657B1C, 0x80657B1E,
    ]

    NOPS = [0x801D9810, 0x801D9818, 0x801D9820, 0x801E0270, 0x801E3114, 0x801E4AF8, 0x801E4B74, 0x801E6684, 0x802390F0]

    BRANCH = [0x801E8E18]

    CUSTOM_WORDS = {
        0x8020F99C: 0x8803024C,
        0x8020EDC0: 0x388000AD,
        0x8020EDC4: 0x8803014F,
        0x8020EDC8: 0x2C000004,
        0x8020EDCC: 0x40820034,
        0x8020EDD0: 0x88030011,
        0x8020EDD4: 0x2C000002,
        0x8020EDD8: 0x40820028,
        0x8020EDDC: 0x38600001,
        0x8020EDE0: 0x987C01B5,
        0x8020EDE4: 0x881C01EF,
        0x8020EDE8: 0x2C000000,
        0x8020EDEC: 0x40820008,
        0x8020EDF0: 0x987C01EF,
        0x8020EDF4: 0x38000001,
        0x8020EDF8: 0x981503A0,
        0x8020EDFC: 0x38840001,
        0x8020EE00: 0x7F63DB78,
        0x8020EE04: 0x38A00001,
        0x8020EE08: 0x4BFB0489,
        0x8020EE0C: 0x60000000,
        0x80214890: 0x881604F2,
        0x80214894: 0x2C000000,
        0x80214898: 0x4082005C,
        0x8021489C: 0x8803000B,
        0x802148A0: 0x28000001,
        0x802148A4: 0x40820010,
        0x802148A8: 0x881DF81B,
        0x802148BC: 0x2C000002,
        0x802148B0: 0x4182005C,
        0x8065771E: 0x001E001E
    }

    h.seek(0x10)
    h.write(bytes([0x41, 0x50, 0x00, v]))
    for addr in MOVED_FLAGS:
        dol.seek(calc_dol_offset(addr))
        b = int.from_bytes(dol.read(1), "big")
        dol.seek(-1, 1)
        dol.write(bytes([b | 0xF8]))
    for addr in ZERO_SHORTS:
        dol.seek(calc_dol_offset(addr))
        dol.write(bytes([0, 0]))
    for addr in NOPS:
        dol.seek(calc_dol_offset(addr))
        dol.write(0x60000000.to_bytes(4, "big"))
    for addr in BRANCH:
        dol.seek(calc_dol_offset(addr))
        dol.write(bytes([0x48, 0x00]))
    for addr in CUSTOM_WORDS:
        dol.seek(calc_dol_offset(addr))
        dol.write(CUSTOM_WORDS[addr].to_bytes(4, "big"))

def update_shop_text_lengths(f: BufferedRandom, start_addr: int) -> None:
    f.seek(start_addr)
    base: int = int.from_bytes(f.read(4), "big")
    addr: int = base
    for _ in range(7):
        addr += 41
        f.write(addr.to_bytes(4, "big"))

def update_item_text(f: BufferedRandom, location: int, player: str, item: str, flags: int) -> None:
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
    write_str(f, item[:20])

def update_goal_characters(dol: BufferedRandom, dat: BufferedRandom, goal_characters: int) -> None:
    for addr in [0x27BE2C52, 0x27BE2CEC, 0x27BFD5C6]:
        dat.seek(addr)
        if goal_characters > 9:
            dat.write(bytes([0xFF, 0x10 + (goal_characters // 10)]))
        else:
            dat.seek(2, 1)
        dat.write(bytes([0xFF, 0x10 + (goal_characters % 10)]))
    for addr in [0x80205F57, 0x801E8E2B, 0x801ABC2B, 0x801AB6E7]:
        dol.seek(calc_dol_offset(addr))
        dol.write(bytes([goal_characters]))

def read_stats(f: BufferedRandom) -> list[bytes]:
    stats = []
    offset = 0x6CAAA9
    for i in range(71):
        f.seek(offset)
        stats.append(f.read(0x26))
        offset += 0x8E
    return stats

def update_stats(f: BufferedRandom, stats: list[dict[str, int]]) -> None:
    v = read_stats(f)
    STAT_OFFSETS = {
        "pitch": [0x1B, 0x20, 0x22, 0x24],
        "bat": [0x10, 0x12, 0x1C],
        "field": [0x1A, 0x1D],
        "run": [0x16, 0x1E]
    }
    offset = 0x6CAAA9
    for c in stats:
        for s in c:
            for o in STAT_OFFSETS[s]:
                f.seek(offset + o)
                f.write(bytes([v[c[s]][o]]))
        offset += 0x8E

def shuffle_text(f: BufferedRandom) -> None:
    excluded = [
        28, 29, 50, 51, 52, 53, 58, 59, 60, 61, 80, 81, 82, 86, 87, 88, 112, 113, 114, 115, 116, 117, 118, 119, 120,
        121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142,
        143, 144, 145, 146, 147, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166,
        167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188,
        189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210,
        211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232,
        233, 234, 235, 236, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 504, 505, 509, 515, 516, 517, 518, 519,
        520, 524, 525, 528, 531, 532, 533, 534, 537, 538, 540, 546, 547, 548, 549, 562, 565, 567, 568, 569, 570, 572,
        573, 580, 590, 591, 592, 593, 594, 595, 601, 602, 607, 610, 611, 612, 613, 618, 619, 622, 630, 631, 632, 633,
        655, 662, 664, 665, 666, 667, 670, 671, 675, 683, 684, 685, 686, 687, 688, 695, 696, 699, 702, 703, 704, 705,
        711, 712, 715, 723, 724, 725, 726, 743, 750, 754, 755, 756, 757, 760, 761, 765, 771, 772, 773, 774, 775, 776,
        780, 781, 784, 788, 789, 790, 791, 795, 796, 799, 806, 807, 808, 809, 822, 827, 830, 831, 832, 833, 836, 837,
        838, 839, 840, 841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857, 858, 859,
        860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 880, 881,
        882, 883, 884, 885, 886, 887, 888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898, 899, 900, 901, 902, 903,
        904, 905, 906, 907, 908, 909, 910, 911, 912, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925,
        926, 927, 928, 929, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942, 943, 944, 945, 946, 947,
        948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 960, 961, 962, 963, 964, 965, 966, 967, 968, 969,
        970, 971, 972, 973, 974, 975, 976, 977, 978, 979, 1175, 1176, 1177, 1178, 1179, 1180, 1181, 1182, 1183, 1184,
        1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199, 1200, 1201, 1202,
        1203, 1204, 1205, 1206, 1207, 1208, 1209, 1210, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220,
        1221, 1222, 1223, 1224, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1258, 1388, 1389, 1390,
        1430, 1431, 1432, 1433, 1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1450, 1453, 1454, 1455, 1456, 1457,
        1458, 1459, 1460, 1461, 1543, 1544, 1545, 1546, 1547, 1548, 1549, 1550, 1551, 1552, 1553, 1672, 1673, 1674,
        1675, 1676, 1677, 1678, 1679, 1680, 1681, 1682, 1683, 1684, 1685, 1686, 1687, 1688, 1689, 1690, 1691, 1692,
        1693, 1694, 1695, 1696, 1697, 1698, 1699, 1700, 1701, 1702, 1703, 1704, 1705, 1706, 1707, 1708, 1709, 1710,
        1711, 1712, 1713, 1714, 1715, 1716, 1717, 1718, 1719, 1720, 1721, 1722, 1723, 1724, 1725, 1726, 1727, 1728,
        1729, 1730, 1731, 1732, 1733, 1734, 1735, 1736, 1737, 1738, 1739, 1740, 1741, 1742, 1743, 1744, 1745, 1746,
        1747, 1748, 1749, 1750, 1751, 1752, 1753, 1754, 1755, 1756, 1757, 1758, 1759, 1760, 1761, 1762, 1763, 1764,
        1765, 1766, 1767, 1768, 1769, 1770, 1771, 1772, 1773, 1774, 1775, 1776, 1777, 1778, 1779, 1780, 1781, 1782,
        1783, 1784, 1785, 1786, 1787, 1788, 1789, 1790, 1791, 1792, 1793, 1794, 1795, 1796, 1797, 1798, 1799, 1800,
        1801, 1802, 1803, 1804, 1805, 1806, 1807, 1808, 1809, 1810, 1811, 1812, 1813, 1814
    ]
    f.seek(0x27BE0064)
    keys = []
    vals = []
    for i in range(1821):
        if i not in excluded:
            keys.append(i)
            vals.append(f.read(4))
        else:
            f.seek(4, 1)
    random.shuffle(vals)
    for i, k in enumerate(keys):
        f.seek(0x27BE0064 + k * 4)
        f.write(vals[i])

def shuffle_quiz(dol: BufferedRandom, dat: BufferedRandom, qsets: list[str], goal_characters: int) -> None:
    questions: dict[str, list[tuple[str, int]]] = {
        "sluggers": [
            ("How many characters are playable in this game?", 71),
            ("In what year was this game released?", 2008),
            ("How many characters do you need to play against the Bowser Jr. Rookies?", goal_characters),
            ("How many unlockable error items are there in this game?", 3),
            ("How many questions are in this quiz?", 5),
            ("How many colors of Noki are playable in this game?", 3),
            ("What did Baby Daisy lose?\r1. Rattle\r2. Pacifier\r3. Crown", 1),
            ("How many flower bushes are in DK Jungle?", 6),
            ("How many Yoshi colors are playable in this game?", 6),
            ("How many trash cans are in Wario City?", 2),
        ],
        "math": [
            ("(30 + 47) * (610 - 586) = ?", 1848),
            ("217 / 7 = ?", 31),
            ("Starting at 0, what is the 15th number in the Fibonacci sequence?", 377),
            ("If you have 6 Yoshis, 5 Shy Guys, Birdo, and Wiggler, how many legs do you have?", 30),
            ("How many prime numbers are less than 100?", 25),
            ("Solve for x:\r38 - 6x = -4 + x", 6),
            ("If you have a right triangle with legs of length 12 and 16, how long is the hypotenuse?", 20),
            ("How many yards are in a mile?", 1760),
            ("Solve for x:\r3x + 24 = 7x + 4", 5),
            ("9 + 10 = ?", 19),
        ],
        "meme": [
            ("Nice.", 69),
            ("Blaze it.", 420),
            ("___ no scope", 360),
            ("What's 9 + 10?", 21),
            ("Get pwn'd n00b", 1337),
            ("The answer to the ultimate question of life, the universe, and everything is...", 42),
            ("What's funnier than 24?", 25),
            ("Why is 6 afraid of 7?", 789),
            ("Electric Boogaloo", 2),
            ("It's over ____!", 9000),
        ]
    }
    chosen = random.choices(qsets, k = 10)
    indexes = [0x27C04E70, 0x27C04ED0, 0x27C04F2C, 0x27C04FC0, 0x27C0506E, 0x27C050C4, 0x27C05142, 0x27C051F6, 0x27C0525C, 0x27C052DA]
    dol.seek(0x653550)
    for i, q in enumerate(chosen):
        if q in questions:
            qa = questions[q][i]
            dat.seek(indexes[i])
            write_str(dat, qa[0])
            dol.write(bytes([int(x) for x in f"{qa[1]:04}"]))
        else:
            dol.seek(4, 1)

def randomize_puzzles(dol: BufferedRandom, dat: BufferedRandom) -> None:
    maze_order = [i for i in range(9)]
    random.shuffle(maze_order)
    dol.seek(0x6282BC)
    for o in maze_order:
        dol.write(bytes([random.randrange(-1, 3) * 4 % 256, 0, 0, o]))
    dol.seek(0x7046EC)
    dat.seek(0x27BFFC93)
    for i in range(5):
        d = random.randrange(2)
        dol.write(bytes([d + 1]))
        dat.write(bytes([d + 0x34]))
        dat.seek(3, 1)

with zipfile.ZipFile(argv[1]) as patch:
    manifest = json.load(patch.open("archipelago.json"))
    if manifest["patch_version"] <= 1:
        h = open("tmp/disc/header.bin", "r+b")
        dol = open("tmp/sys/main.dol", "r+b")
        dat = open("tmp/files/dt_na.dat", "r+b")
        # point Luigi's Flashlight in Secret Shop to Blue Pianta's shop
        dat.seek(0x27BE1D08)
        dat.write(0x14DAC.to_bytes(4, "big"))
        data = json.load(patch.open("mss.json"))
        update_goal_characters(dol, dat, data["goal_characters"])
        if data["randomize_shops"] == 2:
            update_shop_text_lengths(dat, 0x27BE1A88)
            update_shop_text_lengths(dat, 0x27BE1AEC)
            update_shop_text_lengths(dat, 0x27BE1B50)
            update_shop_text_lengths(dat, 0x27BE1BB4)
            update_shop_text_lengths(dat, 0x27BE1C10)
            update_shop_text_lengths(dat, 0x27BE1CDC)
        for location in data["locations"]:
            update_item_text(dat, location["id"], location["player"], location["item"], location["flags"])
        if (manifest["patch_version"] >= 1):
            apply_base_patch(h, dol, manifest["patch_version"])
            dol.seek(0x179127)
            dol.write(bytes([data["starting_captain"]]))
            if data["randomize_shops"] == 2:
                SHOP_WORDS = {
                    0x80231A50: 0x38E00001,
                    0x80231A64: 0x98E3F9E3,
                    0x80231A70: 0x60000000,
                    0x80231B3C: 0x8806F916,
                    0x80231B50: 0x8806F917,
                    0x80231B80: 0x8806F916,
                    0x80231B94: 0x8806F917,
                    0x80231BC4: 0x8806F916,
                    0x80231BD8: 0x8806F917,
                    0x80657708: 0x00030005,
                    0x8065770C: 0x00050005,
                    0x80657710: 0x0005000A,
                    0x80657714: 0x000A000F,
                    0x80657718: 0x000A000F,
                    0x8065771C: 0x000F001E,
                }
                for addr in SHOP_WORDS:
                    dol.seek(calc_dol_offset(addr))
                    dol.write(SHOP_WORDS[addr].to_bytes(4, "big"))
            if len(data["music"]) > 0:
                MUSIC = {
                    0x06: [0x8062E60B],
                    0x07: [0x8062E613],
                    0x08: [0x8062E627],
                    0x09: [0x8062E623],
                    0x0A: [0x8062E62B],
                    0x0B: [0x8062E61B],
                    0x0C: [0x8062E61F],
                    0x0D: [0x8062E60F],
                    0x0E: [0x8062E617],
                    0x0F: [0x8062E62C],
                    0x12: [0x80204B87, 0x80204B9F, 0x80205503],
                    0x13: [0x80205557],
                    0x14: [0x8018933F, 0x80192037],
                    0x15: [0x8020ACC7, 0x8020ACAF],
                    0x16: [0x8020D92B, 0x8020D943],
                    0x17: [0x80200927, 0x8020093F],
                    0x18: [0x802129C7, 0x802129DF],
                    0x19: [0x8021866B, 0x80218683],
                    0x4B: [0x801A0A23, 0x80205583],
                }
                for track in data["music"]:
                    for addr in MUSIC[int(track)]:
                        dol.seek(calc_dol_offset(addr))
                        dol.write(bytes([data["music"][track]]))
            update_stats(dol, data["stats"])
            if len(data["randomize_quiz"]) == 0:
                data["randomize_quiz"] = ["vanilla"]
            shuffle_quiz(dol, dat, data["randomize_quiz"], data["goal_characters"])
            if data["randomize_puzzles"]:
                randomize_puzzles(dol, dat)
            if data["randomize_text"]:
                shuffle_text(dat)
        h.close()
        dol.close()
        dat.close()
    else:
        print("Unsupported patch file version. Please update the patcher.")
