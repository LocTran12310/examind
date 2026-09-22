"""A tiny PNG writer (no Pillow dependency for the API image): the demo question and the sample files draw with it.
Sniffing uploaded images lives in app.shared.domain.images."""
import struct
import zlib


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
