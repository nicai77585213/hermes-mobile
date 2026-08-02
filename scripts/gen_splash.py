# -*- coding: utf-8 -*-
"""生成衡鉴深色splash: 墨黑底#0D0F13 + 衡·枢金色H居中(替换Hermes原版白底蓝标)"""
from PIL import Image, ImageDraw, ImageFilter
import os

RES = r"C:\Users\密码88888\projects\hermes-mobile-main\android\app\src\main\res"


def draw_core(d, s, ox=0, oy=0):
    c = s / 2 + ox
    cy0 = s / 2 + oy
    R_ring = s * 0.30
    w_ring = max(1, s * 0.023)
    d.ellipse([c - R_ring, cy0 - R_ring, c + R_ring, cy0 + R_ring],
              outline=(212, 175, 106), width=int(w_ring))
    # 金色H
    g1, g2 = (245, 227, 184), (212, 175, 106)
    hx = s * 0.105
    hw = max(2, s * 0.035)
    for i in range(int(hw)):
        t = i / hw
        col = tuple(int(g1[k] + (g2[k] - g1[k]) * t) for k in range(3))
        d.rectangle([c - hx, cy0 - s * 0.16 + i, c - hx + 1, cy0 + s * 0.16 + i], fill=col)
        d.rectangle([c + hx, cy0 - s * 0.16 + i, c + hx + 1, cy0 + s * 0.16 + i], fill=col)
    bar_y = cy0 + s * 0.16 - hw
    for i in range(int(hw)):
        t = i / hw
        col = tuple(int(g1[k] + (g2[k] - g1[k]) * t) for k in range(3))
        d.rectangle([c - hx, bar_y + i, c + hx, bar_y + i + 1], fill=col)


def gen_splash(size, path):
    w, h = size
    img = Image.new("RGB", (w, h), (13, 15, 19))  # 墨黑底 #0D0F13
    d = ImageDraw.Draw(img)
    # 图标居中, 尺寸取min(w,h)*0.22
    s = int(min(w, h) * 0.22)
    draw_core(d, s, ox=w / 2 - s / 2, oy=h / 2 - s / 2)
    # 微光
    glow = img.filter(ImageFilter.GaussianBlur(max(2, s * 0.03)))
    img = Image.blend(img, glow, 0.25)
    img.save(path)
    print("生成:", os.path.basename(path), size)


def main():
    # 各density尺寸(Android splash标准)
    sizes = {
        "drawable": (480, 320),
        "drawable-port-hdpi": (480, 320),
        "drawable-port-mdpi": (320, 213),
        "drawable-port-xhdpi": (720, 480),
        "drawable-port-xxhdpi": (960, 640),
        "drawable-port-xxxhdpi": (1280, 853),
        "drawable-land-hdpi": (800, 480),
        "drawable-land-mdpi": (480, 320),
        "drawable-land-xhdpi": (1280, 720),
        "drawable-land-xxhdpi": (1600, 960),
        "drawable-land-xxxhdpi": (1920, 1280),
    }
    for folder, size in sizes.items():
        p = os.path.join(RES, folder, "splash.png")
        if os.path.exists(p):
            gen_splash(size, p)


if __name__ == "__main__":
    main()
