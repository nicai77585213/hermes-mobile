# -*- coding: utf-8 -*-
"""生成御衡「衡·枢」Android图标 PNG (各density + adaptive foreground)
运行: python gen_icon.py
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter

RES = {
    'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192,
}
FORE = {  # adaptive foreground 108dp基准
    'mdpi': 108, 'hdpi': 162, 'xhdpi': 216, 'xxhdpi': 324, 'xxxhdpi': 432,
}

GOLD_HI = (245, 227, 184)
GOLD = (212, 175, 106)
GOLD_LO = (168, 132, 60)
STEEL_HI = (58, 74, 94)
STEEL_LO = (35, 44, 58)
BG_HI = (23, 26, 32)
BG_LO = (7, 8, 10)


def radial_bg(size, r=9):
    """圆角矩形 + 径向渐变底"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    grad = Image.new('L', (size * 2, size * 2))
    d = ImageDraw.Draw(grad)
    cx, cy = size, int(size * 0.82)
    R = size
    for i in range(R * 2, 0, -1):
        t = i / (R * 2)
        c = int(BG_HI[0] + (BG_LO[0] - BG_HI[0]) * t)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=c)
    grad = grad.resize((size, size))
    # 用gradient作为alpha来源组合到底色上
    base = Image.new('RGBA', (size, size), BG_LO + (255,))
    mask = grad.point(lambda p: 255)
    base.paste(Image.new('RGBA', (size, size), BG_HI + (255,)), (0, 0), grad)
    base = base.point(lambda p: p)  # noop
    # 圆角裁剪
    mask_round = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask_round).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * r / 48), fill=255)
    base.putalpha(mask_round)
    return base


def draw_core(d, s):
    """在 s 尺寸画布上绘制核心符号(居中)"""
    c = s / 2
    R_ring = s * 0.316
    w_ring = max(1, s * 0.023)
    # 金环
    d.ellipse([c - R_ring, c - R_ring, c + R_ring, c + R_ring], outline=GOLD, width=int(w_ring))
    # 环上菱形点(上下左右)
    for dx, dy, op in [(0, -1, 255), (0, 1, 180), (-1, 0, 180), (1, 0, 180)]:
        px, py = c + dx * R_ring, c + dy * R_ring
        r = s * 0.02
        d.polygon([(px, py - r), (px + r, py), (px, py + r), (px - r, py)], fill=GOLD_HI + (op,))
    # 内六边形(钢蓝)
    hex_r = s * 0.23
    pts = [(c + hex_r * math.cos(math.radians(a)), c + hex_r * math.sin(math.radians(a)))
           for a in range(-90, 270, 60)]
    d.polygon(pts, outline=STEEL_HI, width=int(max(1, s * 0.027)))
    # 核心H(金色)
    hw = s * 0.075   # 笔划宽
    x1, x2 = c - s * 0.105, c + s * 0.105
    y1, y2 = c - s * 0.14, c + s * 0.14
    d.line([(x1, y1), (x1, y2)], fill=GOLD, width=int(max(1,hw)))
    d.line([(x2, y1), (x2, y2)], fill=GOLD, width=int(max(1,hw)))
    d.line([(x1, c), (x2, c)], fill=GOLD, width=int(max(1,hw)))
    # H中点亮点
    dot_r = s * 0.028
    d.ellipse([c - dot_r, c - dot_r, c + dot_r, c + dot_r], fill=GOLD_HI)


def gen_launcher(size, path):
    img = radial_bg(size)
    d = ImageDraw.Draw(img)
    draw_core(d, size)
    # 收敛微光
    glow = img.filter(ImageFilter.GaussianBlur(size * 0.02))
    img = Image.blend(glow, img, 0.72)
    img.save(path)


def gen_foreground(size, path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # adaptive前景: 内容缩到中心70%(安全区)
    draw_core(d, size * 0.72)
    # 前景需要可缩放的圆形裁剪(系统做), 直接输出透明底即可
    img.save(path)


BASE = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(BASE, '..', 'android', 'app', 'src', 'main', 'res')
os.makedirs(RES_DIR, exist_ok=True)

for name, size in RES.items():
    d = os.path.join(RES_DIR, f'mipmap-{name}')
    os.makedirs(d, exist_ok=True)
    gen_launcher(size, os.path.join(d, 'ic_launcher.png'))
    gen_launcher(size, os.path.join(d, 'ic_launcher_round.png'))
    gen_foreground(FORE[name], os.path.join(d, 'ic_launcher_foreground.png'))
    print(f'✅ {name}: launcher {size}px + foreground {FORE[name]}px')

print('完成')
