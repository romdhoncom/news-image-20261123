"""News front page for Monday 23 November 2026 (make.fun news-image-20261123).

Pure Python standard library, no network at run time. Draws a dense 1024x1024
newspaper front page (masthead, 5 lead stories with drawn pictures, a world map
with 12 pins, 38 more stories, a date-check strip) with its own raster canvas
and its own PNG encoder, and writes it to /output/entry.png. Two runs write
byte-identical files. All text is set in an embedded 5x7 bitmap font.
"""

import binascii
import os
import struct
import zlib

# ---------------------------------------------------------------- font: 5x7 --
# Each glyph is 7 rows of 5 bits. Only capitals, digits and punctuation are
# needed: every string is upper-cased before it is drawn.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "X2": ("00000", "10001", "01010", "00100", "01010", "10001", "00000"),
    "BULL": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}

BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")


def norm(text):
    """Normalise a string for the font: upper case, ASCII punctuation only."""
    return (
        text.upper()
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u00d7", "X")
        .replace("\u2022", "-")
        .replace("\u00b7", "-")
    )


# --------------------------------------------------------------- colours -----
PAPER = (247, 243, 232)
INK = (17, 17, 17)
GREY = (90, 86, 76)
RED = (176, 30, 30)
BLUE = (28, 78, 138)
SKY = (178, 208, 232)
SEA = (70, 130, 180)
LAND = (216, 207, 174)
SAND = (238, 226, 190)
GREEN = (46, 110, 60)
GOLD = (198, 148, 32)
ORANGE = (224, 110, 30)
DARK = (40, 40, 44)
WHITE = (255, 255, 255)
LIGHT = (232, 226, 210)


# ---------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def _set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, 1px wide."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self._set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        """Filled circle."""
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def polygon(self, pts, color):
        """Filled polygon, even-odd scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, int(xs[k + 1]) - int(xs[k]) + 1, 1, color)

    # ---------------------------------------------------------------- text ---
    def text_width(self, text, scale):
        text = norm(text)
        if not text:
            return 0
        return len(text) * 6 * scale - scale

    def draw_text(self, text, x, y, scale, color, bold=False):
        """Draw text; returns the x just past the last character."""
        text = norm(text)
        cx = x
        for ch in text:
            glyph = FONT.get(ch, BLANK)
            for r in range(7):
                row = glyph[r]
                for c in range(5):
                    if row[c] == "1":
                        self.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
                        if bold and scale > 1:
                            self.fill_rect(cx + c * scale + 1, y + r * scale, scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, text, cx, y, scale, color, bold=False):
        w = self.text_width(text, scale)
        return self.draw_text(text, cx - w // 2, y, scale, color, bold)

    def wrap(self, text, max_w, scale):
        """Greedy word wrap; returns a list of lines that fit max_w pixels."""
        words = norm(text).split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ------------------------------------------------------------------- png -----
def png_bytes(w, h, px):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        return out + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", comp)
        + chunk(b"IEND", b"")
    )


# ------------------------------------------------------------ world map ------
# Coarse continent outlines in (lon, lat). The map is drawn equirectangular:
# lon -180..180 across the map box, lat 90..-60 down it.
CONTINENTS = [
    # North America
    [(-170, 70), (-140, 70), (-120, 70), (-95, 70), (-80, 65), (-60, 50),
     (-55, 45), (-65, 40), (-75, 35), (-80, 25), (-85, 20), (-90, 15),
     (-95, 15), (-100, 20), (-110, 25), (-115, 30), (-125, 40), (-125, 50),
     (-140, 60), (-160, 60), (-170, 65)],
    # South America
    [(-80, 10), (-70, 10), (-60, 5), (-50, 0), (-35, -5), (-40, -15),
     (-45, -25), (-50, -35), (-60, -45), (-70, -55), (-70, -40), (-75, -25),
     (-80, -15), (-80, 0)],
    # Europe
    [(-10, 70), (-5, 60), (0, 55), (5, 58), (10, 60), (20, 65), (30, 70),
     (40, 68), (35, 60), (30, 55), (25, 45), (20, 40), (15, 38), (10, 38),
     (5, 40), (0, 43), (-5, 48), (-10, 50)],
    # Africa
    [(-15, 35), (-5, 35), (5, 37), (10, 37), (20, 32), (30, 31), (35, 28),
     (40, 20), (45, 12), (50, 10), (45, 0), (40, -10), (35, -20), (30, -30),
     (20, -35), (15, -30), (12, -18), (10, -5), (8, 5), (0, 5), (-8, 5),
     (-15, 15), (-17, 25)],
    # Asia
    [(40, 70), (60, 70), (80, 73), (100, 75), (120, 75), (140, 72),
     (160, 70), (180, 65), (170, 60), (160, 55), (150, 50), (140, 45),
     (130, 40), (127, 35), (120, 30), (110, 20), (105, 10), (100, 5),
     (95, 10), (90, 20), (85, 25), (80, 15), (75, 10), (70, 20), (65, 25),
     (60, 25), (55, 25), (50, 30), (45, 35), (40, 40), (40, 50), (40, 60)],
    # Australia
    [(113, -22), (115, -32), (120, -34), (130, -32), (140, -38), (150, -37),
     (153, -27), (146, -19), (142, -11), (136, -12), (130, -13), (122, -14),
     (114, -22)],
    # Britain
    [(-5, 50), (-2, 58), (0, 55), (-3, 51)],
    # Japan
    [(130, 31), (135, 34), (140, 38), (142, 44), (140, 40), (135, 33)],
    # Indonesia
    [(95, 5), (105, 0), (115, -5), (125, -8), (135, -5), (140, -8),
     (130, -2), (120, 0), (110, 3), (100, 5)],
]

# (number, lon, lat, key text)
PINS = [
    (1, 30.7, 36.9, "ANTALYA - COP31 COLLAPSES"),
    (2, 56.5, 26.5, "HORMUZ - TANKERS BURN"),
    (3, 30.3, 50.8, "DYMER - FLATS HIT BY DRONE"),
    (4, 20.1, 32.1, "BENGHAZI - CORVETTE SUNK"),
    (5, 32.5, 15.6, "KHARTOUM - DRONE STRIKES"),
    (6, 106.2, -6.2, "CIKANDE - FACTORY FIRE"),
    (7, 35.2, 31.9, "RAMALLAH - VEHICLES TORCHED"),
    (8, 127.0, 37.5, "SEOUL - KOSPI -3.74%"),
    (9, 121.5, 25.0, "TAIPEI - TAIEX -0.93%"),
    (10, 77.2, 28.6, "NEW DELHI - NEPAL PM TALKS"),
    (11, -9.1, 38.7, "LISBON - COST-OF-LIVING MARCH"),
    (12, -8.5, 37.1, "PORTIMAO - MARQUEZ CROWNED"),
]


# ------------------------------------------------------- lead pictures -------
def pic_cop31(cv, x, y, w, h):
    """Antalya: pale sky, sun, sea, a white summit hall with flags."""
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + int(h * 0.55), w, h - int(h * 0.55), SEA)
    cv.circle(x + w - 46, y + 20, 12, GOLD)
    cv.fill_rect(x + 30, y + h - 40, 130, 40, WHITE)
    cv.fill_rect(x + 30, y + h - 48, 130, 8, RED)
    cv.fill_rect(x + 180, y + h - 30, 90, 30, WHITE)
    cv.fill_rect(x + 180, y + h - 36, 90, 6, INK)
    for i, fx in enumerate((x + 200, x + 240, x + 280, x + 330, x + 380)):
        cv.line(fx, y + h - 36, fx, y + 10, INK)
        cv.fill_rect(fx, y + 10, 16, 9, (RED, BLUE, GREEN, GOLD, ORANGE)[i])
    cv.fill_rect(x, y + h - 4, w, 4, SAND)


def pic_markets(cv, x, y, w, h):
    """A falling chart: grid, red line plunging, big -3.74%."""
    cv.fill_rect(x, y, w, h, WHITE)
    for gx in range(x + 20, x + w, 44):
        cv.line(gx, y + 6, gx, y + h - 6, (220, 220, 215))
    for gy in range(y + 10, y + h, 16):
        cv.line(x + 6, gy, x + w - 6, gy, (220, 220, 215))
    frac = [(0.03, 0.20), (0.15, 0.28), (0.27, 0.24), (0.40, 0.48),
            (0.52, 0.44), (0.65, 0.68), (0.77, 0.62), (0.89, 0.92), (0.97, 0.96)]
    pts = [(x + int(fx * w), y + int(fy * h)) for fx, fy in frac]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED)
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, RED)
    cv.draw_text("-3.74%", x + 16, y + h - 30, 3, RED, bold=True)


def pic_hormuz(cv, x, y, w, h):
    """Strait of Hormuz: blue sea, two tanker silhouettes, flames."""
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + int(h * 0.45), w, h - int(h * 0.45), SEA)
    cv.fill_rect(x + 18, y + h - 26, 110, 14, DARK)
    cv.fill_rect(x + 48, y + h - 36, 34, 10, DARK)
    cv.fill_rect(x + 170, y + h - 24, 96, 12, DARK)
    cv.fill_rect(x + 196, y + h - 34, 28, 10, DARK)
    for fx in (x + 60, x + 90, x + 210):
        base = y + h - 36
        cv.polygon([(fx - 9, base), (fx, base - 14), (fx + 9, base)], ORANGE)
        cv.polygon([(fx - 4, base), (fx, base - 8), (fx + 4, base)], GOLD)


def pic_marquez(cv, x, y, w, h):
    """Portimao: grey track sweeping, checkered flag, a racing bike."""
    cv.fill_rect(x, y, w, h, (196, 222, 178))
    cv.fill_rect(x, y + 18, w, 16, (90, 90, 92))
    cv.fill_rect(x, y + 40, w, 10, (150, 150, 148))
    for i in range(8):
        for j in range(2):
            col = WHITE if (i + j) % 2 == 0 else INK
            cv.fill_rect(x + 14 + i * 9, y + 8 + j * 7, 9, 7, col)
    cv.circle(x + 130, y + h - 16, 8, INK)
    cv.circle(x + 168, y + h - 16, 8, INK)
    cv.line(130 + x, y + h - 16, 152 + x, y + h - 34, RED)
    cv.line(152 + x, y + h - 34, 168 + x, y + h - 16, RED)
    cv.line(152 + x, y + h - 34, 148 + x, y + h - 44, INK)
    cv.draw_text("8", x + w - 46, y + 8, 3, RED, bold=True)


def pic_nepal(cv, x, y, w, h):
    """New Delhi: two flags and a domed building."""
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + h - 26, w, 26, SAND)
    # Nepal flag (crimson, blue border) and India flag (saffron/white/green)
    cv.fill_rect(x + 20, y + 10, 54, 36, BLUE)
    cv.fill_rect(x + 23, y + 13, 48, 30, (220, 20, 60))
    cv.fill_rect(x + 92, y + 10, 54, 36, WHITE)
    cv.fill_rect(x + 92, y + 10, 54, 12, (255, 153, 51))
    cv.fill_rect(x + 92, y + 34, 54, 12, (19, 136, 8))
    cv.circle(x + 119, y + 28, 5, BLUE)
    # domed building
    cv.fill_rect(x + 180, y + h - 34, 110, 34, WHITE)
    cv.circle(x + 235, y + h - 34, 14, (200, 170, 120))
    cv.fill_rect(x + 196, y + h - 24, 10, 24, INK)
    cv.fill_rect(x + 230, y + h - 24, 10, 24, INK)
    cv.fill_rect(x + 264, y + h - 24, 10, 24, INK)


# ---------------------------------------------------------------- stories ----
# (kicker, headline, sub-headline, body, picture function)
LEADS_BIG = [
    ("CLIMATE",
     "COP31 COLLAPSES",
     "NO DEAL IN ANTALYA - FIRST FAILURE SINCE 2009",
     "TALKS RAN TWO DAYS OVER TIME AND ENDED ON SUNDAY WITH NO DEAL. THE EU, "
     "BRITAIN AND ISLAND STATES REJECTED A DRAFT WITH NO MENTION OF FOSSIL "
     "FUELS. AUSTRALIA'S PM CALLED IT A SIGN OF DIFFICULT TIMES.",
     pic_cop31),
    ("MARKETS",
     "MARKETS IN FREEFALL",
     "ASIAN SHARES PLUNGE AS SELLING SWEEPS THE REGION",
     "SEOUL'S KOSPI FELL 3.74% AND TAIPEI 0.93% AS SELLING SWEPT ASIA. THE "
     "S&P 500 ENTERED MONDAY ON SEVEN STRAIGHT LOSSES AND IN CORRECTION. "
     "TAIWAN BANNED SHORT-SELLING FROM TODAY.",
     pic_markets),
]

LEADS_SMALL = [
    ("THE GULF",
     "TANKERS BURN IN HORMUZ",
     "TWO SUPERTANKERS HIT BY MINES, IRAN NAVY SAYS",
     "TWO SUPERTANKERS CAUGHT FIRE EAST OF THE STRAIT AFTER HITTING NAVAL "
     "MINES ON SUNDAY, IRAN'S NAVY SAID. TWO MORE TANKERS WERE HIT BY "
     "PROJECTILES ON SATURDAY NEAR OMAN. CRUDE FLOWS THROUGH THE STRAIT "
     "ARE DOWN NEARLY HALF AS THE US NAVAL BLOCKADE ENTERS DAY 130.",
     pic_hormuz),
    ("SPORT",
     "MARQUEZ: EIGHTH TITLE",
     "P8 IN PORTUGAL SEALS THE CROWN",
     "MARCO BEZZECCHI WON IN PORTUGAL AS APRILIA SWEPT THE PODIUM, BUT "
     "MARC MARQUEZ'S EIGHTH PLACE WAS ENOUGH TO CLINCH HIS EIGHTH "
     "PREMIER-CLASS TITLE - HIS TENTH GRAND PRIX CROWN - AFTER "
     "OVERTURNING A 102-POINT DEFICIT.",
     pic_marquez),
    ("SOUTH ASIA",
     "NEPAL PM IN DELHI",
     "SHAH HOLDS TALKS WITH MODI",
     "PRIME MINISTER BALENDRA SHAH HELD DELEGATION-LEVEL TALKS WITH "
     "NARENDRA MODI ON MONDAY, COVERING FLOOD RECONSTRUCTION AID, TRADE, "
     "ENERGY AND CONNECTIVITY. IT IS HIS FIRST VISIT TO INDIA SINCE "
     "TAKING OFFICE IN MARCH.",
     pic_nepal),
]

# (headline, one-line body) — 38 more stories, in column order.
MORE = [
    ("DYMER FLATS HIT BY DRONE",
     "DRONE HITS 5-STOREY BLOCK; 3 DEAD, 14 MISSING"),
    ("CORVETTE CAPSIZES AT BENGHAZI",
     "UKRAINIAN SEA DRONES HIT RUSSIAN WARSHIP; 10 HURT"),
    ("RUSSIAN SHIP STILL BURNING",
     "CARGO SHIP ON FIRE OFF FINLAND AFTER ATTACK"),
    ("KHARTOUM DRONE STRIKES",
     "UN FACILITY DAMAGED; THREE KILLED IN OMDURMAN"),
    ("FACTORY FIRE TOLL RISES",
     "24 BODY BAGS RECOVERED AT CIKANDE, BANTEN"),
    ("WEST BANK ARSON OVERNIGHT",
     "SETTLERS TORCH 12 VEHICLES NEAR RAMALLAH"),
    ("SOUTH SUDAN KILLINGS",
     "24 CIVILIANS KILLED IN FRESH VIOLENCE"),
    ("MYANMAR HITS BACK AT ASEAN",
     "JUNTA CALLS BLOC'S DECISION UNFAIR, IMBALANCED"),
    ("NIGERIA REVENGE ATTACKS",
     "35 FULANIS KILLED, AFP REPORTS FROM KANO"),
    ("POLAND: THEY WERE MISSILES",
     "THREE FALLEN OBJECTS WERE RUSSIAN CRUISE MISSILES"),
    ("IRAN STRIKE WOUNDS TWO",
     "ATTACK IN BAHRAIN CONDEMNED BY SAUDI ARABIA"),
    ("HOUTHI MISSILE INTERCEPTED",
     "SAUDI-LED COALITION STOPS MISSILE IN WEST"),
    ("ISRAEL TALKS END IN FAILURE",
     "NETANYAHU-EISENKOT REACH NO DEAL ON GOVERNMENT"),
    ("BOLSONARO STABLE IN ICU",
     "BRAZIL EX-LEADER UNDER OBSERVATION IN BRASILIA"),
    ("WHO PLEADS FOR EBOLA PEACE",
     "FIGHTING HAMPERING RESPONSE IN EASTERN CONGO"),
    ("KIM: SECURITY, NOT SUPREMACY",
     "NORTH KOREA SIGNALS DEFENSIVE POSTURE"),
    ("LAHORE MOST POLLUTED AGAIN",
     "AQI 538 ON SUNDAY MORNING, IQAIR SAYS"),
    ("MINISTER QUITS OVER AI CHEATING",
     "SOUTH KOREA EDUCATION SCANDAL CLAIMS MINISTER"),
    ("KILLER-ROBOT RULES BY 2028",
     "128 STATES AGREE TO PURSUE UN TALKS"),
    ("TRUMP COOL ON SCHUMER",
     "PRESIDENT: COOPERATION WOULD BE DIFFICULT"),
    ("HAWKS URGE IRAN STRIKE",
     "TRUMP SAYS THERE IS NO RUSH TO ACT"),
    ("HEGSETH CURBS CANADA TIES",
     "SECRET MEMO REPORTED BY WASHINGTON POST"),
    ("OHIO BABY SHOWER SHOOTING",
     "THREE KILLED, ONE WOUNDED; POLICE INVESTIGATE"),
    ("LISBON MARCH OVER PRICES",
     "THOUSANDS PROTEST LIVING COSTS IN CAPITAL"),
    ("BEPICOLOMBO REACHES MERCURY",
     "SECOND MISSION EVER IN ORBIT; CRAFT SAFE"),
    ("DELTA CHAOS AT THANKSGIVING",
     "SYSTEM FAILURE DELAYS NEARLY HALF ITS FLIGHTS"),
    ("SHURI CASTLE REOPENS",
     "OKINAWA LANDMARK OPENS 7 YEARS AFTER FIRE"),
    ("INDIA POST RECORD 720/9",
     "VISITORS PILE UP RUNS IN WELLINGTON TEST"),
    ("ALCARAZ WINS ATP FINALS",
     "SPANISH STAR BEATS ZVEREV TO TAKE TITLE"),
    ("VERSTAPPEN WINS IN VEGAS",
     "RED BULL STAR TRIUMPHS UNDER THE LIGHTS"),
    ("BOCA TAKE SUDAMERICANA",
     "BUENOS AIRES SIDE BEAT MINEIRO 2-0"),
    ("REAL WIN; DORTMUND GO TOP",
     "LEEDS BEAT CHELSEA 4-1; COMO WIN 2-0"),
    ("F1 AGREES V8 FOR 2030",
     "2.1-LITRE TURBO V8 FRAMEWORK SET BY FIA"),
    ("CHIEFS ROUT CARDINALS 34-7",
     "MAHOMES THROWS FOR 324 YARDS AND 3 TDS"),
    ("MUNOZ TAKES MAIDEN MOTO2 WIN",
     "CHAOTIC PORTUGAL RACE; QUILES TAKES MOTO3"),
    ("CHINA AGREES AI TALKS",
     "BEIJING TO SET UP DISCUSSION MECHANISM"),
    ("DENMARK PM WARNS OF 'ENEMY'",
     "FREDERIKSEN'S HAMAS REMARK DRAWS FIRE"),
    ("FBI PROBES DATABASE BREACH",
     "POSSIBLE HACK OF LAW ENFORCEMENT SYSTEM"),
]

DATE_STRIP = ("MONDAY 23 NOVEMBER 2026 - KOSPI -3.74% - TAIEX -0.93% - "
              "NEPAL PM IN DELHI - SHURI CASTLE OPENS - "
              "TAIWAN SHORT-SELLING BAN FROM TODAY")


# ---------------------------------------------------------------- layout -----
CAPTIONS = {
    "COP31 COLLAPSES": "ANTALYA - THE SUMMIT HALL AFTER THE TALKS FAILED",
    "MARKETS IN FREEFALL": "SEOUL - THE KOSPI'S WORST DAY IN WEEKS",
    "TANKERS BURN IN HORMUZ": "STRAIT OF HORMUZ - SMOKE OVER THE TANKERS",
    "MARQUEZ: EIGHTH TITLE": "PORTIMAO - MARQUEZ SEALS TITLE NO. 8",
    "NEPAL PM IN DELHI": "NEW DELHI - SHAH MEETS MODI",
}


def draw_big_lead(cv, x, y, w, lead):
    kicker, headline, sub, body, pic = lead
    cv.draw_text(kicker, x, y, 2, RED, bold=True)
    yy = y + 20
    for line in cv.wrap(headline, w, 3):
        cv.draw_text(line, x, yy, 3, INK, bold=True)
        yy += 21
    yy += 4
    for line in cv.wrap(sub, w, 2):
        cv.draw_text(line, x, yy, 2, INK, bold=True)
        yy += 17
    yy += 6
    pic(cv, x, yy, w, 72)
    yy += 72 + 4
    cv.draw_text(CAPTIONS[headline], x, yy, 1, GREY)
    yy += 7 + 5
    for line in cv.wrap(body, w, 2):
        cv.draw_text(line, x, yy, 2, INK)
        yy += 17
    return yy


def draw_small_lead(cv, x, y, w, lead):
    kicker, headline, sub, body, pic = lead
    cv.draw_text(kicker, x, y, 2, RED, bold=True)
    yy = y + 20
    for line in cv.wrap(headline, w, 2):
        cv.draw_text(line, x, yy, 2, INK, bold=True)
        yy += 14
    yy += 4
    for line in cv.wrap(sub, w, 1):
        cv.draw_text(line, x, yy, 1, INK, bold=True)
        yy += 9
    yy += 5
    pic(cv, x, yy, w, 56)
    yy += 56 + 4
    cv.draw_text(CAPTIONS[headline], x, yy, 1, GREY)
    yy += 7 + 5
    for line in cv.wrap(body, w, 1):
        cv.draw_text(line, x, yy, 1, INK)
        yy += 9
    return yy


def draw_map(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (188, 216, 232))
    for poly in CONTINENTS:
        pts = [
            (x + int((lon + 180) / 360.0 * w), y + int((90 - lat) / 150.0 * h))
            for lon, lat in poly
        ]
        cv.polygon(pts, LAND)
    for num, lon, lat, _key in PINS:
        px = x + int((lon + 180) / 360.0 * w)
        py = y + int((90 - lat) / 150.0 * h)
        cv.circle(px, py, 8, RED)
        label = str(num)
        tw = cv.text_width(label, 1)
        cv.draw_text(label, px - tw // 2, py - 3, 1, WHITE, bold=True)


def draw_more(cv, x, y, w, stories):
    yy = y
    for head, body in stories:
        cv.draw_text(head, x, yy, 1, INK, bold=True)
        yy += 8
        for line in cv.wrap(body, w, 1):
            cv.draw_text(line, x, yy, 1, GREY)
            yy += 9
        yy += 1
    return yy


def draw_page():
    cv = Canvas(1024, 1024, PAPER)
    # masthead
    cv.fill_rect(16, 10, 992, 3, INK)
    cv.text_centered("MONDAY 23 NOVEMBER 2026", 512, 22, 5, INK, bold=True)
    cv.text_centered("THE WORLD IN ONE PAGE", 512, 64, 2, INK)
    cv.fill_rect(16, 82, 992, 3, INK)
    cv.fill_rect(16, 87, 992, 2, RED)
    # two big leads
    y1 = draw_big_lead(cv, 16, 96, 484, LEADS_BIG[0])
    y2 = draw_big_lead(cv, 524, 96, 484, LEADS_BIG[1])
    y = max(y1, y2) + 8
    cv.fill_rect(16, y, 992, 2, INK)
    # three smaller leads
    y += 10
    cols = [16, 356, 696]
    ys = [draw_small_lead(cv, cx, y, 312, lead) for cx, lead in zip(cols, LEADS_SMALL)]
    y = max(ys) + 8
    cv.fill_rect(16, y, 992, 2, INK)
    # world map with pins
    y += 10
    cv.draw_text("WHERE IT HAPPENED", 16, y, 2, RED, bold=True)
    y += 20
    map_y = y
    draw_map(cv, 16, map_y, 684, 132)
    cv.draw_text("THE PLACES", 716, map_y, 1, INK, bold=True)
    ky = map_y + 14
    for num, _lon, _lat, key in PINS:
        cv.draw_text(str(num) + " " + key, 716, ky, 1, INK)
        ky += 10
    y = map_y + 132 + 8
    cv.fill_rect(16, y, 992, 2, INK)
    # more stories in three columns
    y += 10
    cv.draw_text("MORE FROM AROUND THE WORLD", 16, y, 2, RED, bold=True)
    y += 20
    cv.fill_rect(16, y, 992, 2, INK)
    y += 8
    cols = [16, 352, 688]
    chunks = [MORE[0:13], MORE[13:26], MORE[26:38]]
    ends = [draw_more(cv, cx, y, 320, chunk) for cx, chunk in zip(cols, chunks)]
    y = max(ends) + 6
    cv.fill_rect(16, y, 992, 2, INK)
    y += 6
    cv.text_centered(DATE_STRIP, 512, y, 1, INK, bold=True)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_page()
    data = png_bytes(1024, 1024, cv.px)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
