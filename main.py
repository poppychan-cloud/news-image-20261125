# news-image-20261125 entry, v2 (Python 3.13, standard library only).
#
# The image is entry.png beside this file, drawn by draw.py (Python PIL,
# code-rendered text and illustration, so nothing is garbled). This
# program validates the finished image against the competition caps
# (1024x1024, 1 MiB) and copies it to /output/entry.png.
#
# Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
# /output:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024


def check_image(path):
    """Read the PNG header for size; refuse anything over the caps."""
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("entry.png is not a PNG")
    width = int.from_bytes(head[16:20], "big")
    height = int.from_bytes(head[20:24], "big")
    if width > MAX_SIDE or height > MAX_SIDE:
        raise SystemExit("image is %dx%d, over the 1024 cap" % (width, height))
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise SystemExit("image is %d bytes, over the 1 MiB cap" % size)
    return width, height, size


def main():
    if not os.path.exists(SRC):
        raise SystemExit("entry.png missing — run draw.py first")
    width, height, size = check_image(SRC)
    dst_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, "entry.png")
    shutil.copyfile(SRC, dst)
    os.chmod(dst, 0o644)
    print("wrote %s (%dx%d, %d bytes)" % (dst, width, height, size))


if __name__ == "__main__":
    main()
