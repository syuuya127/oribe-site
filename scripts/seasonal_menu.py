"""
季節メニュー(トップページと /menu のスライダー)を seasonal-menus/<季節>.json の内容に差し替える。

使い方:
  python scripts/seasonal_menu.py seasonal-menus/autumn-2026.json
  → index.html と menu.html のスライダー・見出し・ひと言を書き換える(英語ページのみ)
  → そのあと build_i18n.py check / build で中国語・日本語ページに反映する

スライダーの中身は毎回まるごと作り直すので、何度実行しても同じ結果になる。
見出し(Autumn Omakase など)とひと言は、今入っている文字を json の値に置き換える。
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# ページごとのスライダーの目印(Webflow のクラス名)
MASKS = {"index.html": '<div class="mask home w-slider-mask">',
         "menu.html": '<div class="mask menus w-slider-mask">'}
TITLE = re.compile(r'(<div class="text-block-23b">)([^<]*)(</div>)')
TAGLINE = re.compile(r'(<div class="text-block-27[^"]*">)([^<]*)(</div>)')
# メニューページの季節の背景(パソコン用 image-89 / スマホ用 image-90。クラス名は Webflow 時代のまま sakura-v2)
BG = {"desktop": re.compile(r'<img[^>]*class="image-89 sakura-v2"[^>]*>'),
      "mobile": re.compile(r'<img[^>]*class="image-90 sakura-v2-m"[^>]*>')}
BG_CLASS = {"desktop": "image-89 sakura-v2", "mobile": "image-90 sakura-v2-m"}


def slide(img: str, lines=None) -> str:
    alt = html.escape(" / ".join(lines)) if lines else ""
    # 表示は春と同じ 500px 幅。高精細画面には 1000px 版を出す(画像は 1000x1500 で作り、-p-500 を縮小版として置く)
    small = img.replace(".webp", "-p-500.webp")
    inner = (f'<img loading="lazy" src="/images/{small}" srcset="/images/{small} 500w, /images/{img} 1000w" '
             f'sizes="500px" width="500" height="750" alt="{alt}" class="image-9"/>')
    if lines:
        text = "<br/>".join(html.escape(t, quote=False) for t in lines)
        inner += f'<div class="div-block-55"></div><div class="text-block-6">{text}</div>'
    return f'<div class="dish-slide w-slide"><div class="div-block-54">{inner}</div></div>'


def slides(menu: dict) -> str:
    out = []
    for course in ("lunch", "dinner"):
        out.append(slide(menu[course]["cover"]))
        out += [slide(img, lines) for img, lines in menu[course]["dishes"]]
    return "".join(out)


def apply(page: str, menu: dict) -> None:
    path = ROOT / page
    s = path.read_text(encoding="utf-8")
    start = s.index(MASKS[page]) + len(MASKS[page])
    # マスクの閉じタグ = 左矢印の <div の直前にある </div>
    arrow = s.rindex("<div", 0, s.index("w-slider-arrow-left", start))
    end = s.rindex("</div>", start, arrow)
    s = s[:start] + slides(menu) + s[end:]
    s, n1 = TITLE.subn(lambda m: m[1] + menu["title"] + m[3], s, count=1)
    s, n2 = TAGLINE.subn(lambda m: m[1] + menu["tagline"] + m[3], s, count=1)
    if not (n1 and n2):
        sys.exit(f"{page}: 見出し/ひと言の場所が見つからない")
    if page == "menu.html" and "background" in menu:
        for kind, pat in BG.items():
            tag = f'<img src="/images/{menu["background"][kind]}" loading="lazy" alt="" class="{BG_CLASS[kind]}"/>'
            s, n = pat.subn(tag, s, count=1)
            if not n:
                sys.exit(f"{page}: 背景({kind})の場所が見つからない")
            if not (ROOT / "images" / menu["background"][kind]).exists():
                sys.exit(f"画像が無い: images/{menu['background'][kind]}")
    for course in ("lunch", "dinner"):
        for img in [menu[course]["cover"]] + [d[0] for d in menu[course]["dishes"]]:
            for name in (img, img.replace(".webp", "-p-500.webp")):
                if not (ROOT / "images" / name).exists():
                    sys.exit(f"画像が無い: images/{name}")
    path.write_text(s, encoding="utf-8")
    print(f"{page}: スライド {s.count('dish-slide w-slide')} 枚")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    menu = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for page in MASKS:
        apply(page, menu)
