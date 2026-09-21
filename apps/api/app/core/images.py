"""Image sniffing + a tiny PNG writer (no Pillow dependency for the API image)."""
import struct
import zlib

ALLOWED = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/webp": "webp"}


def sniff(data: bytes) -> tuple[str | None, int | None, int | None]:
    """Return (mime, width, height) from magic bytes, or (None, None, None). SVG is rejected on purpose."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return "image/png", w, h
    if data[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", data[6:10])
        return "image/gif", w, h
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", None, None
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return "image/jpeg", w, h
            seg = struct.unpack(">H", data[i + 2:i + 4])[0]
            i += 2 + seg
        return "image/jpeg", None, None
    return None, None, None


def png(width: int, height: int, pixels: list[list[tuple[int, int, int]]]) -> bytes:
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)

    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


class Canvas:
    def __init__(self, w: int, h: int, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.px = [[bg] * w for _ in range(h)]

    def dot(self, x: float, y: float, color=(30, 60, 200), r: int = 1):
        xi, yi = int(round(x)), int(round(y))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if 0 <= xi + dx < self.w and 0 <= yi + dy < self.h:
                    self.px[yi + dy][xi + dx] = color

    def line(self, x0, y0, x1, y1, color=(40, 40, 40), r=0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.dot(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, color, r)

    def encode(self) -> bytes:
        return png(self.w, self.h, self.px)
