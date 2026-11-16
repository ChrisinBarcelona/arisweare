#!/usr/bin/env python3
"""Inspect or strip hidden metadata (EXIF, GPS, XMP, IPTC, text chunks) from web images.

    python3 tools/imgmeta.py report assets/img          # list what each image contains
    python3 tools/imgmeta.py strip  assets/img          # remove it in place (keeps colour profiles)

Handles JPEG, PNG and WebP using only the Python standard library.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

TAGS = {0x010F: "camera make", 0x0110: "camera model", 0x0131: "software", 0x0132: "date",
        0x013B: "artist", 0x8298: "copyright", 0x8825: "GPS location", 0x9003: "date taken"}


def exif_fields(tiff: bytes) -> dict[str, str]:
    """Read IFD0 (+ the Exif sub-IFD) of a TIFF/EXIF block."""
    out: dict[str, str] = {}
    if len(tiff) < 8 or tiff[:2] not in (b"II", b"MM"):
        return out
    end = "<" if tiff[:2] == b"II" else ">"

    def ifd(off: int, depth: int = 0) -> None:
        if off + 2 > len(tiff) or depth > 2:
            return
        (n,) = struct.unpack_from(end + "H", tiff, off)
        for i in range(n):
            p = off + 2 + i * 12
            if p + 12 > len(tiff):
                return
            tag, typ, cnt, val = struct.unpack_from(end + "HHII", tiff, p)
            if tag == 0x8769:                      # Exif sub-IFD
                ifd(val, depth + 1)
            elif tag in TAGS:
                if tag == 0x8825:
                    out[TAGS[tag]] = "present"
                elif typ == 2:                     # ASCII
                    raw = tiff[p + 8:p + 8 + cnt] if cnt <= 4 else tiff[val:val + cnt]
                    out[TAGS[tag]] = raw.rstrip(b"\x00").decode("latin-1", "replace").strip()
    (first,) = struct.unpack_from(end + "I", tiff, 4)
    ifd(first)
    return out


def xmp_fields(xmp: bytes) -> dict[str, str]:
    import re
    out = {}
    for key, pat in (("creator", rb"<dc:creator>.*?<rdf:li[^>]*>(.*?)</rdf:li>"),
                     ("rights", rb"<dc:rights>.*?<rdf:li[^>]*>(.*?)</rdf:li>"),
                     ("software", rb'xmp:CreatorTool="([^"]*)"'),
                     ("GPS location", rb"exif:GPSLatitude")):
        m = re.search(pat, xmp, re.S)
        if m:
            out[key] = "present" if key == "GPS location" else m.group(1).decode("utf-8", "replace")[:60]
    return out


# ------------------------------------------------------------------ JPEG
def jpeg_segments(b: bytes):
    i = 2
    while i + 4 <= len(b) and b[i] == 0xFF:
        marker = b[i + 1]
        if marker == 0xDA:                         # start of scan: rest is image data
            yield marker, i, len(b)
            return
        (ln,) = struct.unpack_from(">H", b, i + 2)
        yield marker, i, i + 2 + ln
        i += 2 + ln


def jpeg(b: bytes, strip: bool):
    found, keep = {}, [b[:2]]
    for marker, s, e in jpeg_segments(b):
        seg = b[s:e]
        body = seg[4:]
        meta = False
        if marker == 0xE1 and body.startswith(b"Exif\x00\x00"):
            found.update(exif_fields(body[6:])); found.setdefault("EXIF", "yes"); meta = True
        elif marker == 0xE1 and b"http://ns.adobe.com/xap/1.0/" in body[:40]:
            found.update(xmp_fields(body)); found.setdefault("XMP", "yes"); meta = True
        elif marker in (0xED, 0xEC, 0xFE):        # Photoshop/IPTC, Ducky, comment
            found.setdefault({0xED: "IPTC", 0xEC: "Ducky", 0xFE: "comment"}[marker], "yes"); meta = True
        if not (strip and meta):
            keep.append(seg)
    return found, b"".join(keep)


# ------------------------------------------------------------------ PNG
def png(b: bytes, strip: bool):
    found, out, i = {}, [b[:8]], 8
    while i + 12 <= len(b):
        (ln,) = struct.unpack_from(">I", b, i)
        typ = b[i + 4:i + 8]
        chunk = b[i:i + 12 + ln]
        meta = typ in (b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME")
        if meta:
            data = b[i + 8:i + 8 + ln]
            if typ == b"eXIf":
                found.update(exif_fields(data))
            elif b"xmpmeta" in data:
                found.update(xmp_fields(data)); found.setdefault("XMP", "yes")
            else:
                found.setdefault(typ.decode(), "yes")
        if not (strip and meta):
            out.append(chunk)
        i += 12 + ln
    return found, b"".join(out)


# ------------------------------------------------------------------ WebP
def webp(b: bytes, strip: bool):
    found, chunks, i = {}, [], 12
    while i + 8 <= len(b):
        fourcc = b[i:i + 4]
        (ln,) = struct.unpack_from("<I", b, i + 4)
        data = b[i + 8:i + 8 + ln]
        pad = ln & 1
        if fourcc == b"EXIF":
            found.update(exif_fields(data[6:] if data.startswith(b"Exif\x00\x00") else data)); found.setdefault("EXIF", "yes")
        elif fourcc == b"XMP ":
            found.update(xmp_fields(data)); found.setdefault("XMP", "yes")
        if not (strip and fourcc in (b"EXIF", b"XMP ")):
            if fourcc == b"VP8X" and strip:
                data = bytes([data[0] & ~0x0C]) + data[1:]   # clear the EXIF/XMP flags
            chunks.append(fourcc + struct.pack("<I", ln) + data + (b"\x00" if pad else b""))
        i += 8 + ln + pad
    body = b"WEBP" + b"".join(chunks)
    return found, b"RIFF" + struct.pack("<I", len(body)) + body


HANDLERS = {b"\xff\xd8": jpeg, b"\x89P": png, b"RI": webp}


def main(mode: str, root: str) -> None:
    total = changed = 0
    for f in sorted(Path(root).rglob("*")):
        if not f.is_file():
            continue
        b = f.read_bytes()
        handler = HANDLERS.get(b[:2])
        if not handler:
            continue
        total += 1
        found, cleaned = handler(b, strip=(mode == "strip"))
        if mode == "report":
            if found:
                print(f"{str(f):58} " + "; ".join(f"{k}: {v}" for k, v in found.items()))
        elif found and cleaned != b:
            f.write_bytes(cleaned)
            changed += 1
            print(f"stripped {f} ({len(b) - len(cleaned)} bytes of metadata)")
    print(f"{total} images checked" + (f", {changed} cleaned" if mode == "strip" else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
