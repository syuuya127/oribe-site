"""
公開中の oribe-sushi.com.my(Webflow ホスティング)をそのまま取り込むスクリプト。
2026-09-07 の移行時に使用。Webflow の Export は編集画面の下書きを含んでいたため、
公開サイトと完全に同じ内容にするためにこちらを使った。

やること:
  1. 公開中の 7 ページの HTML を取得
  2. HTML と CSS が参照する Webflow CDN 上のアセット(画像 / CSS / JS / 動画)を
     すべてローカル (images/ css/ js/ videos/) にダウンロード
  3. 参照をローカルパスに書き換え(og:image と JSON-LD は絶対 URL のまま)
  4. jQuery を CloudFront からローカルに切り替え、canonical が無いページに追加
"""
import hashlib
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://oribe-sushi.com.my"
PAGES = ["", "menu", "our-chef", "gallery", "about", "sake-pairing", "omakase"]
UA = {"User-Agent": "Mozilla/5.0 (site-mirror; oribe-sushi migration)"}

# ファイル名に "(1)" のような括弧が含まれるので括弧は許可し、
# CSS の url(...) の閉じ括弧だけを後から取り除く
RAW_RE = re.compile(
    r"https://(?:cdn\.prod\.website-files\.com|assets(?:-global)?\.website-files\.com|"
    r"uploads-ssl\.webflow\.com|d3e54v103j8qbb\.cloudfront\.net)/[^\"'\s<>&]+")


def balanced(u: str) -> str:
    while u.endswith(")") and u.count(")") > u.count("("):
        u = u[:-1]
    return u


def find_assets(text: str) -> set[str]:
    return {balanced(m) for m in RAW_RE.findall(text)}

url_to_local: dict[str, str] = {}
FAILED: list[tuple[str, str]] = []
local_names: dict[str, str] = {}   # local path -> source url (衝突検出用)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def local_path_for(url: str) -> str:
    """CDN URL → /images/xxx のようなローカルパス。"""
    if url in url_to_local:
        return url_to_local[url]
    clean = url.split("?")[0]
    fname = urllib.parse.unquote(clean.rsplit("/", 1)[1])
    if re.match(r"^[0-9a-f]{24}_", fname):
        fname = fname.split("_", 1)[1]
    base, ext = os.path.splitext(fname)
    base = re.sub(r"[()]", "", base)
    base = re.sub(r"\s+", "-", base.strip())
    ext = ext.lower()
    if ext == ".css":
        folder = "css"
    elif ext == ".js":
        folder = "js"
    elif ext in (".mp4", ".webm"):
        folder = "videos"
    else:
        folder = "images"
    local = f"/{folder}/{base}{ext}"
    if local in local_names and local_names[local] != url:
        local = f"/{folder}/{base}-{hashlib.md5(url.encode()).hexdigest()[:6]}{ext}"
    local_names[local] = url
    url_to_local[url] = local
    return local


def download(url: str, local: str) -> None:
    dest = ROOT / local.lstrip("/")
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  get {local}")
    try:
        dest.write_bytes(fetch(url))
    except Exception as e:  # noqa: BLE001
        FAILED.append((url, str(e)))
        print(f"  !! FAILED {url} ({e})")


def localize_css(css_text: str) -> str:
    def repl(m):
        url = balanced(m.group(0))
        tail = m.group(0)[len(url):]
        local = local_path_for(url)
        download(url, local)
        return ".." + local + tail   # css/ からの相対パス
    return RAW_RE.sub(repl, css_text)


def process_page(slug: str) -> None:
    html = fetch(f"{SITE}/{slug}").decode("utf-8")
    name = slug or "index"
    print(f"== {name}.html")

    urls = sorted(find_assets(html), key=len, reverse=True)
    for url in urls:
        local = local_path_for(url)
        download(url, local)
        if local.endswith(".css"):
            p = ROOT / local.lstrip("/")
            p.write_text(localize_css(p.read_text(encoding="utf-8")), encoding="utf-8")
        html = html.replace(url, local)

    # og:image と JSON-LD は絶対 URL に戻す
    html = re.sub(r'(<meta content=")(/images/[^"]+)(" property="og:image")',
                  lambda m: m.group(1) + SITE + m.group(2) + m.group(3), html)
    html = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  lambda m: m.group(0).replace('"/images/', f'"{SITE}/images/'),
                  html, flags=re.S)

    # jQuery (cloudfront) → ローカル
    html = re.sub(r'<script src="/js/jquery-[^"]*"[^>]*>',
                  '<script src="/js/jquery-3.5.1.min.js" type="text/javascript">', html)
    jq = [l for l in url_to_local.values() if "/js/jquery-" in l]
    for l in jq:
        src = ROOT / l.lstrip("/")
        if src.name != "jquery-3.5.1.min.js":
            src.replace(ROOT / "js" / "jquery-3.5.1.min.js")

    # canonical が無ければ追加(表示には影響しない)
    if 'rel="canonical"' not in html:
        canon = SITE if not slug else f"{SITE}/{slug}"
        html = html.replace("</title>", f'</title>\n  <link href="{canon}" rel="canonical">', 1)
        print(f"  canonical added: {canon}")

    left = find_assets(html)
    if left:
        print("  !! leftovers:", left[:3])
    (ROOT / f"{name}.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    for slug in PAGES:
        process_page(slug)
    print(f"done: {len(url_to_local)} assets, {len(FAILED)} failed")
    for u, e in FAILED:
        print("  FAILED", u, e)
