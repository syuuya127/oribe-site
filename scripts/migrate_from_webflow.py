"""
Webflow エクスポートを自社ホスティング用に変換するスクリプト。
(初回移行時に1回だけ実行したもの。記録として残しています)

やること:
  1. 内部リンクを  menu.html  →  /menu  に書き換え(公開中のURL構造を維持)
  2. css / js / images / videos への参照をルート絶対パスに統一
  3. Webflow CDN (cdn.prod.website-files.com / uploads-ssl.webflow.com) への
     残存参照をローカルの /images/ に置き換え(無ければダウンロード)
  4. jQuery を Webflow の CloudFront からローカル /js/ に切り替え
  5. canonical が無いページに追加、generator メタ削除
  6. 背景動画を再エンコード済みの軽量 mp4 に差し替え
"""
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://oribe-sushi.com.my"
PAGES = ["index", "menu", "our-chef", "gallery", "about",
         "sake-pairing", "omakase", "private-events"]
IMAGES = ROOT / "images"

# ファイル名に "(243)" のような括弧が含まれるので、区切りは引用符・空白・< のみ
CDN_RE = re.compile(r"https://cdn\.prod\.website-files\.com/[0-9a-f]+/[^\"'\s<]+")
UPLOADS_RE = re.compile(r"https://uploads-ssl\.webflow\.com/[0-9a-f]+/[^\"'\s<]+")

VIDEO_MAP = {
    "videos/Highlight-video---2026-Japan-Expo-Tuna-Cutting-3_mp4.mp4,"
    "videos/Highlight-video---2026-Japan-Expo-Tuna-Cutting-3_webm.webm":
        "/videos/japan-expo-tuna-cutting.mp4",
    "videos/Sushi-Oribe-Private-Birthday-Event--Highlight_mp4.mp4,"
    "videos/Sushi-Oribe-Private-Birthday-Event--Highlight_webm.webm":
        "/videos/private-birthday-event.mp4",
}


def local_name(cdn_url: str) -> str:
    """Webflow CDN の URL からエクスポート時のローカルファイル名を推定する。"""
    fname = urllib.parse.unquote(cdn_url.rsplit("/", 1)[1])
    if re.match(r"^[0-9a-f]{24}_", fname):
        fname = fname.split("_", 1)[1]
    base, ext = os.path.splitext(fname)
    base = re.sub(r"[()]", "", base)
    base = re.sub(r"\s+", "-", base.strip())
    return base + ext


def ensure_local(url: str) -> str:
    name = local_name(url)
    dest = IMAGES / name
    if not dest.exists():
        print(f"  download: {name}")
        urllib.request.urlretrieve(url, dest)
    return f"/images/{name}"


def absolutize_assets(html: str) -> str:
    for folder in ("images", "css", "js", "videos"):
        html = re.sub(rf"(?<![\w/.\-]){folder}/", f"/{folder}/", html)
    return html


def process_page(slug: str) -> None:
    path = ROOT / f"{slug}.html"
    html = path.read_text(encoding="utf-8")
    print(f"== {slug}.html")

    # 1. 内部リンク
    html = html.replace('href="index.html"', 'href="/"')
    for p in PAGES:
        if p != "index":
            html = html.replace(f'href="{p}.html"', f'href="/{p}"')

    # 6. 動画(絶対パス化の前に置換)
    for old, new in VIDEO_MAP.items():
        html = html.replace(old, new)

    # 2. アセットの絶対パス化
    html = absolutize_assets(html)

    # 3. CDN 参照のローカル化
    html = CDN_RE.sub(lambda m: ensure_local(m.group(0)), html)
    html = UPLOADS_RE.sub(lambda m: ensure_local(m.group(0)), html)

    # og:image と JSON-LD 内は絶対URLにする
    html = re.sub(r'(<meta content=")(/images/[^"]+)(" property="og:image">)',
                  lambda m: m.group(1) + SITE + m.group(2) + m.group(3), html)

    def abs_in_ld(m):
        return m.group(0).replace('"/images/', f'"{SITE}/images/')
    html = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  abs_in_ld, html, flags=re.S)

    # 4. jQuery
    html = re.sub(
        r'<script src="https://d3e54v103j8qbb\.cloudfront\.net/js/jquery[^>]*></script>',
        '<script src="/js/jquery-3.5.1.min.js" type="text/javascript"></script>',
        html)

    # 5. canonical / generator
    html = html.replace('  <meta content="Webflow" name="generator">\n', "")
    if 'rel="canonical"' not in html:
        canon = SITE if slug == "index" else f"{SITE}/{slug}"
        anchor = '<link href="/images/webclip.png" rel="apple-touch-icon">'
        assert anchor in html, f"anchor not found in {slug}"
        html = html.replace(anchor, anchor + f'\n  <link href="{canon}" rel="canonical">')
        print(f"  canonical added: {canon}")

    if slug == "private-events":
        html = html.replace(
            "<title>Private Events</title>",
            "<title>Private Events | Sushi Oribe KL – Omakase Dining for Groups in Kuala Lumpur</title>")

    path.write_text(html, encoding="utf-8")

    leftovers = re.findall(r"https://(?:cdn\.prod\.website-files|uploads-ssl\.webflow|d3e54v103j8qbb\.cloudfront)\.com[^\"']*", html)
    if leftovers:
        print("  !! leftovers:", leftovers[:3])


if __name__ == "__main__":
    for slug in PAGES:
        process_page(slug)
    print("done")
