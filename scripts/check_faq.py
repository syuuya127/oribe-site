"""
FAQ と構造化データ（JSON-LD）の点検。ページを直したあと・本番に出したあとに実行する（2026-10-20 追加）。

  python scripts/check_faq.py            # 手元のファイルを点検
  python scripts/check_faq.py --live     # 本番 https://oribe-sushi.com.my を点検

見ること:
  1. 全24ページの JSON-LD が壊れていない（JSON として読める）
  2. /omakase と /private-events の FAQPage の質問が、画面に見える質問と一致している
     （画面に無い質問を構造化データだけに書くと Google の規約違反になる）
  3. servesCuisine に Kaiseki が無い（織部は江戸前おまかせで、懐石ではない）
  4. 中国語・日本語ページで、追加した質問が英語のまま残っていない
  5. IndexNow の確認キーが置いてある
最後に FAIL の数を出す。0 なら合格。
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://oribe-sushi.com.my"
PAGES = ["index", "menu", "our-chef", "gallery", "about", "sake-pairing", "omakase", "private-events"]
LANGS = ["", "zh/", "ja/"]
KEY = "8e2643d6b5497d55227072f38b0495a9"
LIVE = "--live" in sys.argv
fails = 0


def get(path: str) -> str:
    if LIVE:
        url = SITE + "/" + path
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OribeCheck)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8")
    p = ROOT / (path or "index.html")
    if p.is_dir():
        p = p / "index.html"
    elif not p.suffix:
        p = p.with_suffix(".html")
    return p.read_text(encoding="utf-8")


def fail(msg: str) -> None:
    global fails
    fails += 1
    print("  FAIL " + msg)


def ld_blocks(src: str) -> list:
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            out.append(json.loads(m.group(1)))
        except json.JSONDecodeError as e:
            fail(f"JSON-LD が壊れている: {e}")
    return out


def faq_names(blocks: list) -> list[str]:
    for b in blocks:
        if b.get("@type") == "FAQPage":
            return [q["name"] for q in b["mainEntity"]]
    return []


def visible_text(src: str) -> str:
    body = src[src.find("<body"):]
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


print(f"点検先: {'本番 ' + SITE if LIVE else '手元 ' + str(ROOT)}")
for lang in LANGS:
    for page in PAGES:
        path = lang + ("" if page == "index" else page)
        try:
            src = get(path)
        except Exception as e:
            fail(f"/{path} を開けない: {e}")
            continue
        blocks = ld_blocks(src)
        if '"Kaiseki"' in json.dumps([b.get("@graph", b) for b in blocks]).replace(" ", "") and \
                re.search(r'"servesCuisine":\s*\[[^\]]*"Kaiseki"', src):
            fail(f"/{path} servesCuisine に Kaiseki が残っている")
        if page in ("omakase", "private-events"):
            names = faq_names(blocks)
            want = 15 if page == "omakase" else 4
            if len(names) != want:
                fail(f"/{path} FAQPage の質問数 {len(names)}（期待 {want}）")
            if lang == "":
                vis = visible_text(src)
                for n in names:
                    if n not in vis:
                        fail(f"/{path} 画面に無い質問が構造化データにある: {n}")
            else:
                vis = visible_text(src)
                for en_q in ["Is there parking?", "Can I book the whole restaurant?", "Private Events FAQ",
                             "Do you serve a more affordable lunch?"]:
                    if en_q in vis:
                        fail(f"/{path} 英語のまま: {en_q}")
        print(f"  ok   /{path}  JSON-LD {len(blocks)} 個")

try:
    k = get(f"{KEY}.txt").strip()
    if k != KEY:
        fail("IndexNow 確認キーの中身が違う")
    else:
        print("  ok   IndexNow 確認キー")
except Exception as e:
    fail(f"IndexNow 確認キーが無い: {e}")

print(f"\nFAIL: {fails}")
sys.exit(1 if fails else 0)
