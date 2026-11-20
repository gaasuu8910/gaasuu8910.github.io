#!/usr/bin/env python3
"""ヒント投稿用の画像を作る。スレの post.png の下部に「発見率○%」の帯と黒塗りを重ねる。
使い方: python3 tools/hint_card.py <slug> <黒塗りの文字数> <発見率%> <出力先.png>
（言葉そのものは画像に書かない。文字数ぶんの■だけ）
"""
import sys
from PIL import Image, ImageDraw, ImageFont

slug, n, rate, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
im = Image.open(f'threads/{slug}/post.png').convert('RGB')
W, H = im.size
d = ImageDraw.Draw(im, 'RGBA')
F = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
big = ImageFont.truetype(F, int(W * 0.085), index=0)
mid = ImageFont.truetype(F, int(W * 0.05), index=0)

band_h = int(H * 0.36)
d.rectangle([0, H - band_h, W, H], fill=(20, 20, 24, 255))
y = H - band_h + int(H * 0.035)
t1 = 'いちばん見つかっていない1個'
d.text(((W - d.textlength(t1, font=mid)) / 2, y), t1, font=mid, fill=(255, 255, 255))
y += int(H * 0.08)
box = '■' * max(2, n)
d.text(((W - d.textlength(box, font=big)) / 2, y), box, font=big, fill=(255, 255, 255))
y += int(H * 0.12)
t2 = f'発見率 {rate}%'
d.text(((W - d.textlength(t2, font=big)) / 2, y), t2, font=big, fill=(255, 214, 64))
im.save(out)
print(out)
