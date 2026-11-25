# news-image-20261125 entry (Python 3.13, standard library only):
# the image is entry.png beside this file, drawn by draw.py
# (Python PIL, code-rendered text and illustration, so nothing is
# garbled), and this program copies it to /output/entry.png.
# Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
# /output:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
DST_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(DST_DIR, exist_ok=True)
DST = os.path.join(DST_DIR, "entry.png")
shutil.copyfile(SRC, DST)
os.chmod(DST, 0o644)
print("wrote", DST, os.path.getsize(DST), "bytes")
