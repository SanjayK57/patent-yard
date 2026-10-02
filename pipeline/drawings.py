"""Turn a USPTO drawing sheet (2560x3300, 1-bit PNG) into a small, cropped 4-level grayscale PNG.

Only the patent's own drawing is kept: the "U.S. Patent ... Sheet 1 of 9" header line and blank margins are
cropped away, nothing is added.
"""
import struct
import zlib

_HI = [bin(b >> 4).count("1") for b in range(256)]
_LO = [bin(b & 15).count("1") for b in range(256)]


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def decode_gray_png(png):
    """Non-interlaced grayscale PNG (bit depth 1, 2 or 8) -> (width, height, depth, scanlines)."""
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    i, idat, w, h, depth = 8, b"", 0, 0, 0
    while i < len(png):
        n, kind = struct.unpack(">I4s", png[i:i + 8])
        body = png[i + 8:i + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
            if ctype != 0 or depth not in (1, 2, 8):
                raise ValueError(f"unsupported PNG (color type {ctype}, depth {depth})")
        elif kind == b"IDAT":
            idat += body
        i += 12 + n
    raw = zlib.decompress(idat)
    stride, bpp = (w * depth + 7) // 8, max(1, depth // 8)
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                line[x] = (line[x] + ((line[x - bpp] if x >= bpp else 0) + prev[x]) // 2) & 255
        elif f == 4:
            for x in range(stride):
                a, b, c = (line[x - bpp] if x >= bpp else 0), prev[x], (prev[x - bpp] if x >= bpp else 0)
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, depth, rows


def shrink_sheet(png, max_w=560):
    """Cropped, 4x-downsampled, 4-level gray PNG (ink dark on white) -> (png bytes, width, height), or None if blank."""
    w, h, depth, rows = decode_gray_png(png)
    if depth != 1:
        raise ValueError("expected a 1-bit drawing sheet")
    ow, oh = w // 4, h // 4
    dark = []  # 0..16 ink coverage per 4x4 block; set bits are white in these sheets
    for oy in range(oh):
        acc = [0] * ow
        for r in rows[oy * 4:oy * 4 + 4]:
            for bx, byte in enumerate(r[:ow // 2]):
                acc[2 * bx] += 4 - _HI[byte]
                acc[2 * bx + 1] += 4 - _LO[byte]
        dark.append(acc)
    inkrow = lambda y: sum(1 for v in dark[y] if v > 3) > 1
    lim, top = int(oh * 0.15), 0
    while top < lim and not inkrow(top):  # top margin
        top += 1
    while top < lim and inkrow(top):  # the "U.S. Patent ... Sheet 1 of 9" header line
        top += 1
    if top >= lim:
        top = int(oh * 0.08)
    ink = [y for y in range(top, oh) if inkrow(y)]
    if not ink:
        return None
    y0, y1 = max(top, ink[0] - 6), min(oh, ink[-1] + 7)
    cols = [x for x in range(ow) if any(dark[y][x] > 3 for y in range(y0, y1, 2))]
    x0, x1 = max(0, cols[0] - 6), min(ow, cols[-1] + 7)
    crop = [row[x0:x1] for row in dark[y0:y1]]
    cw, ch = x1 - x0, y1 - y0
    if cw > max_w:  # nearest-neighbour second pass keeps files small
        k = cw / max_w
        crop = [[crop[int(y * k)][int(x * k)] for x in range(max_w)] for y in range(int(ch / k))]
        cw, ch = max_w, int(ch / k)
    lut = [3 if v == 0 else 2 if v <= 2 else 1 if v <= 5 else 0 for v in range(17)]  # boosted so thin lines survive
    raw = bytearray()
    for row in crop:
        raw.append(0)
        vals = [lut[v] for v in row] + [3] * ((4 - cw % 4) % 4)
        raw.extend((vals[i] << 6) | (vals[i + 1] << 4) | (vals[i + 2] << 2) | vals[i + 3] for i in range(0, len(vals), 4))
    out = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", cw, ch, 2, 0, 0, 0, 0)) \
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b"")
    return out, cw, ch


def one_bit_png(w, h, black_rows=()):
    """Test helper: a white 1-bit sheet with some fully black rows."""
    stride = (w + 7) // 8
    raw = b"".join(b"\x00" + (b"\x00" if y in black_rows else b"\xff") * stride for y in range(h))
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 1, 0, 0, 0, 0)) \
        + _chunk(b"IDAT", zlib.compress(raw)) + _chunk(b"IEND", b"")
