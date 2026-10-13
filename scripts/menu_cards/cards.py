"""
季節メニューのカード画像(表紙 + 料理)を、撮影写真から作る。

使い方:
  python scripts/menu_cards/cards.py scripts/menu_cards/autumn-2026.json
    → images/ に <file_prefix>-Lunch-01<suffix>.webp, -02.webp ... と、表示用の -p-500 版を書き出す
  python scripts/menu_cards/cards.py <設定.json> --out <フォルダ>     書き出し先を変える(試作・見比べ用)
  python scripts/menu_cards/cards.py <設定.json> --only Lunch-01      1 枚だけ作る

次の季節の手順:
  1. 設定ファイルをコピー(例: winter-2026.json)し、season / year / file_prefix / 写真の番号を書き換える
     写真の番号 → Google Drive のファイル ID は "photos" に書く(共有フォルダのファイルを開いた URL の /d/<ID>/)
  2. このスクリプトで画像を作る → 見て、表紙の title_top(文字の高さ)や葉の位置を調整する
  3. seasonal-menus/<季節>.json に画像名と料理名を書き、scripts/seasonal_menu.py でサイトに反映する

写真は Drive の縮小表示(横 1600px)を取ってくる。原本(20〜40MB)は使わないし、リポジトリにも入れない。
取ってきた写真と葉の素材は scripts/menu_cards/.cache/ に置く(git には入れない)。
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import leaves

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FONTS = HERE / "fonts"
CACHE = HERE / ".cache"
LOGO = ROOT / "images" / "logo_03-white.png"
W, H = 1000, 1500
DARK = (74, 50, 28)   # 背景が明るい所では焦げ茶のロゴにする
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
            dest.write_bytes(r.read())
    return dest


def photo(cfg: dict, num: str) -> Path:
    fid = cfg["photos"][num]
    return fetch(f"https://drive.google.com/thumbnail?id={fid}&sz=w1600", CACHE / "photos" / f"{num}.jpg")


def font(name, size, wght):
    f = ImageFont.truetype(str(FONTS / name), size)
    f.set_variation_by_axes([wght])
    return f


def fit(path: Path, focus_y=0.5) -> Image.Image:
    """写真を 2:3 に切り抜いて 1000x1500 にする。"""
    im = Image.open(path).convert("RGB")
    r = W / H
    if im.width / im.height > r:          # 横長 → 左右を切る
        nw = int(im.height * r)
        x = (im.width - nw) // 2
        im = im.crop((x, 0, x + nw, im.height))
    else:                                  # 縦長 → 上下を切る
        nh = int(im.width / r)
        y = int((im.height - nh) * focus_y)
        im = im.crop((0, y, im.width, y + nh))
    return im.resize((W, H), Image.LANCZOS)


def shadowed(base: Image.Image, layer: Image.Image, blur=10, opacity=110):
    """layer(RGBA) の形の柔らかい影を base に落としてから layer を重ねる。"""
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(layer.split()[3].point(lambda v: v * opacity // 255))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(layer)


def logo_color_for(card, top=40, width=230, height=70):
    """ロゴが乗る範囲の明るさを測り、明るすぎれば焦げ茶を返す(白いロゴが読めないため)。"""
    x = (W - width) // 2
    lum = card.convert("L").crop((x, top, x + width, top + height)).resize((1, 1), Image.BOX).getpixel((0, 0))
    return DARK if lum > 170 else None


def add_logo(card: Image.Image, width=230, top=40, color=None):
    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.resize((width, int(logo.height * width / logo.width)), Image.LANCZOS)
    if color:
        solid = Image.new("RGBA", logo.size, color + (255,))
        solid.putalpha(logo.split()[3])
        logo = solid
    layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
    layer.paste(logo, ((W - logo.width) // 2, top), logo)
    shadowed(card, layer, blur=9, opacity=150 if not color else 0)


def title_block(card, season, course, year, top, ink=(255, 255, 255), k=0.8):
    """表紙の文字。春の表紙と同じ構成: 季節(斜体)/ Omakase / コース名(右寄せ)/ 年(縦書き)。
    k = 文字の大きさの倍率(Omakase が横幅の約半分になる 0.8)。"""
    layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f_season = font("CormorantItalic.ttf", round(92 * k), 600)
    f_main = font("Playfair.ttf", round(150 * k), 500)
    f_course = font("CormorantItalic.ttf", round(78 * k), 600)
    f_year = font("Cormorant.ttf", round(30 * k), 600)
    c = ink + (255,)
    ob = d.textbbox((0, 0), "Omakase", font=f_main)
    ox = (W - (ob[2] - ob[0])) // 2 - ob[0]
    oy = top + round(88 * k)
    d.text((ox, oy), "Omakase", font=f_main, fill=c)
    sb = d.textbbox((0, 0), season, font=f_season)
    d.text(((W - (sb[2] - sb[0])) // 2 - sb[0], top), season, font=f_season, fill=c)
    cb = d.textbbox((0, 0), course, font=f_course)
    right = ox + ob[2]
    d.text((right - (cb[2] - cb[0]) - cb[0] - 6, oy + ob[3] - round(18 * k)), course, font=f_course, fill=c)
    yx = right + round(16 * k)                 # 年は Omakase の右肩に縦書き
    for i, ch in enumerate(year):
        d.text((yx, oy + round(34 * k) + i * round(30 * k)), ch, font=f_year, fill=c)
    shadowed(card, layer, blur=12, opacity=120)


def leaf_set(cfg: dict) -> dict:
    """葉の素材(枝 1 本 + 葉 1 枚ずつ)を用意する。名前: branch, leaf_0, leaf_1 ..."""
    src = cfg.get("leaf_sources")
    if not src:
        return {}
    out = {"branch": leaves.cutout(fetch(src["branch"], CACHE / "leaves" / "branch.jpg"))}
    for i, piece in enumerate(leaves.split(leaves.cutout(fetch(src["circle"], CACHE / "leaves" / "circle.jpg")))):
        out[f"leaf_{i}"] = piece
    return out


def save(card: Image.Image, out_dir: Path, name: str):
    rgb = card.convert("RGB")
    rgb.save(out_dir / f"{name}.webp", "WEBP", quality=82, method=6)
    rgb.resize((500, 750), Image.LANCZOS).save(out_dir / f"{name}-p-500.webp", "WEBP", quality=85, method=6)
    print("  ", f"{name}.webp")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--out", default=str(ROOT / "images"))
    ap.add_argument("--only", help="例: Lunch-01 / Dinner-05")
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lv = None
    for course, c in cfg["courses"].items():
        jobs = [("01", c["cover"])] + [(f"{i:02d}", {"photo": p}) for i, p in enumerate(c["dishes"], start=2)]
        for no, job in jobs:
            if a.only and a.only != f"{course}-{no}":
                continue
            card = fit(photo(cfg, job["photo"]), job.get("focus_y", 0.5)).convert("RGBA")
            if no == "01":
                add_logo(card)
                title_block(card, cfg["season"], course, cfg["year"], job.get("title_top", 150))
                if job.get("leaves"):
                    lv = lv or leaf_set(cfg)
                    for p in job["leaves"]:
                        opts = {k: v for k, v in p.items() if k != "leaf"}
                        if "shadow" in opts:
                            opts["shadow"] = tuple(opts["shadow"])
                        leaves.place(card, lv[p["leaf"]], **opts)
            else:
                add_logo(card, color=logo_color_for(card))
            save(card, out, f"{cfg['file_prefix']}-{course}-{no}{job.get('file_suffix', '')}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
