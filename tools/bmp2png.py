#!/usr/bin/env python3
"""Convert SameBoy tester BMP (V3 header, 32bpp BGRA) to PNG, scaled 3x."""
import struct, sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
off = struct.unpack_from('<I', d, 10)[0]
w, h = struct.unpack_from('<ii', d, 18)
top_down = h < 0; h = abs(h)
im = Image.frombytes('RGBA', (w, h), d[off:off + w * h * 4], 'raw', 'ABGR')
if not top_down: im = im.transpose(Image.FLIP_TOP_BOTTOM)
im.convert('RGB').resize((w * 3, h * 3), Image.NEAREST).save(dst)
print(dst, w, h)
