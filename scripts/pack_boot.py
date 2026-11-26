#!/usr/bin/env python3
"""Self-contained repacker for sagit boot.img (header v0, 4096 page).

Extracts the stock ramdisk and the appended board DTB from the original image
every time (so it survives environment resets), splices in the new kernel, and
rebuilds a byte-compatible boot image padded to the stock partition size.
"""
import argparse
import hashlib
import re
import struct
import sys

SRC = "/workspace/.uploads/3f692417-e0dd-4079-94b2-6b42e6451b75_boot.img"
PAGE = 4096
HEADER_LEN = 1632


def pad(b, page=PAGE):
    return b + b"\0" * ((-len(b)) % page)


def extract_stock(src):
    d = open(src, "rb").read()
    assert d[:8] == b"ANDROID!"
    ks = struct.unpack_from("<I", d, 8)[0]
    rs = struct.unpack_from("<I", d, 16)[0]
    ss = struct.unpack_from("<I", d, 24)[0]
    assert ss == 0, "unexpected second stage"
    kernel = d[PAGE:PAGE + ks]
    rd_off = PAGE + ((ks + PAGE - 1) // PAGE) * PAGE
    ramdisk = d[rd_off:rd_off + rs]
    # stock layout: gzip(Image) + appended FDT, both inside kernel_size
    fdt = list(re.finditer(b"\xd0\x0d\xfe\xed", kernel))
    assert fdt, "no FDT found in stock kernel section"
    dtb = kernel[fdt[-1].start():]
    return d, kernel, ramdisk, dtb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel-gz", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--cmdline-append", default="")
    args = ap.parse_args()

    orig, _, ramdisk, dtb = extract_stock(args.src)
    hdr = bytearray(orig[:HEADER_LEN])
    if args.cmdline_append:
        cur = bytes(hdr[64:64 + 512]).split(b"\0")[0].decode()
        new = (cur + " " + args.cmdline_append).encode()
        assert len(new) < 512, "cmdline too long"
        hdr[64:64 + 512] = new + b"\0" * (512 - len(new))
        print("cmdline:", new.decode())
    kernel = open(args.kernel_gz, "rb").read() + dtb
    assert kernel[-len(dtb):] == dtb

    struct.pack_into("<I", hdr, 8, len(kernel))
    struct.pack_into("<I", hdr, 16, len(ramdisk))
    struct.pack_into("<I", hdr, 24, 0)

    sha = hashlib.sha1()
    sha.update(kernel)
    sha.update(ramdisk)
    sha.update(struct.pack("<III", len(kernel), len(ramdisk), 0))
    hdr[576:608] = sha.digest() + b"\0" * 12

    img = bytearray(hdr) + b"\0" * (PAGE - HEADER_LEN)
    img += pad(kernel)
    img += pad(ramdisk)
    if len(img) > len(orig):
        sys.exit("image bigger than stock partition dump")
    img += b"\0" * (len(orig) - len(img))
    open(args.out, "wb").write(img)
    print("wrote", args.out, len(img))


if __name__ == "__main__":
    main()
