"""
紅葉などの「白い背景で撮った素材写真」から葉だけを切り抜き、カードに重ねる部品。
cards.py から使う(単体では動かさない)。

- cutout(): 白背景を抜いて透過 PNG にする。葉の縁に白いにじみが残らないよう、背景色を色から差し引く
- split(): 1 枚の写真に散らばった葉を 1 枚ずつに分ける(赤くない塊=写真の四隅の影は捨てる)
- place(): 葉を位置・幅・角度・ぼかし・影つきでカードに重ねる
"""
from collections import deque

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def cutout(path) -> Image.Image:
    src = Image.open(path).convert("RGB")
    im = np.asarray(src).astype(float)
    # 背景は明るいグレーのムラがあるので、大きくぼかした画像を「その場所の背景色」とみなす
    bg = np.asarray(src.resize((48, 36), Image.BOX).resize((im.shape[1], im.shape[0]), Image.BILINEAR)).astype(float)
    # 背景推定に葉が混ざらないよう、明るい画素の値寄りにする
    bg = np.maximum(bg, np.percentile(im.reshape(-1, 3), 90, axis=0) * 0.97)
    diff = np.clip((bg - im).max(axis=2), 0, 255)          # 背景からどれだけ暗い/色づいているか
    a = np.clip((diff - 18) / 70, 0, 1)                     # 18 以下は背景、88 以上は完全に葉
    a = np.asarray(Image.fromarray((a * 255).astype("uint8"))
                   .filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))).astype(float) / 255
    a3 = a[..., None]
    fg = np.where(a3 > 0.02, (im - (1 - a3) * bg) / np.maximum(a3, 0.02), 0)  # 背景の白を色から抜く
    return Image.fromarray(np.dstack([np.clip(fg, 0, 255), a * 255]).astype("uint8"), "RGBA")


def split(cut: Image.Image) -> list:
    """透過画像に散らばった葉を 1 枚ずつ(上から順に)切り出す。"""
    A = np.asarray(cut)
    small = np.asarray(cut.split()[3].resize((cut.width // 8, cut.height // 8), Image.BOX)) > 150
    lab = np.zeros(small.shape, int)
    n = 0
    for y0 in range(small.shape[0]):
        for x0 in range(small.shape[1]):
            if small[y0, x0] and not lab[y0, x0]:
                n += 1
                q = deque([(y0, x0)])
                lab[y0, x0] = n
                while q:
                    y, x = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < small.shape[0] and 0 <= xx < small.shape[1] and small[yy, xx] and not lab[yy, xx]:
                            lab[yy, xx] = n
                            q.append((yy, xx))
    pieces = []
    for i in range(1, n + 1):
        # 塊の形を少し太らせてから元の大きさに戻す(ギザギザの境界が葉にかからないように)
        comp = Image.fromarray(((lab == i) * 255).astype("uint8")).filter(ImageFilter.MaxFilter(5))
        m = (np.asarray(comp.resize((cut.width, cut.height), Image.BILINEAR)) > 0) & (A[..., 3] > 0)
        if m.sum() < 20000:
            continue
        rgb = A[..., :3][m].astype(int)
        if (rgb[:, 0] - rgb[:, 2]).mean() < 60:   # 赤くない塊(写真の四隅の影)は捨てる
            continue
        ys, xs = np.where(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        piece = A[y0:y1, x0:x1].copy()
        piece[..., 3] = piece[..., 3] * m[y0:y1, x0:x1]
        pieces.append(Image.fromarray(piece, "RGBA"))
    return pieces


def place(card: Image.Image, leaf: Image.Image, x, y, width, angle=0, flip=False, blur=0,
          shadow=(10, 14, 12, 90), bright=1.0) -> None:
    """leaf を中心 (x, y)・幅 width・角度 angle で card に重ねる。shadow = (右へ, 下へ, ぼかし, 濃さ0-255)。"""
    lf = leaf.crop(leaf.getbbox())
    lf = ImageOps.mirror(lf) if flip else lf
    lf = lf.resize((width, int(lf.height * width / lf.width)), Image.LANCZOS)
    lf = lf.rotate(angle, resample=Image.BICUBIC, expand=True)
    if bright != 1.0:
        rgb = ImageEnhance.Brightness(lf.convert("RGB")).enhance(bright).convert("RGBA")
        rgb.putalpha(lf.split()[3])
        lf = rgb
    if blur:
        lf = lf.filter(ImageFilter.GaussianBlur(blur))
    px, py = int(x - lf.width / 2), int(y - lf.height / 2)
    if shadow:
        dx, dy, sb, op = shadow
        sh = Image.new("RGBA", lf.size, (20, 10, 0, 0))
        sh.putalpha(lf.split()[3].point(lambda v: v * op // 255))
        sh = sh.filter(ImageFilter.GaussianBlur(sb))
        layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
        layer.paste(sh, (px + dx, py + dy), sh)
        card.alpha_composite(layer)
    layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
    layer.paste(lf, (px, py), lf)
    card.alpha_composite(layer)
