"""
IndexNow で Bing などに「このページを更新した」と知らせるスクリプト。
ChatGPT の検索は Bing の登録を使うため、ページを直したあと再登録を早める目的で使う（2026-10-20 追加）。

使い方（cPanel で Deploy HEAD Commit を押して本番に出た「あと」に実行する）:
  python scripts/indexnow.py                 # sitemap.xml の全URLを送る
  python scripts/indexnow.py /omakase /private-events   # 指定ページだけ（各言語版も一緒に送る）
  python scripts/indexnow.py --dry-run       # 送らずに送る予定のURLだけ表示

確認キー: サイト直下の <KEY>.txt（中身はキーそのもの）。キーは公開してよい値（秘密情報ではない）。
.cpanel.yml でこのファイルも本番に配置している。
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "oribe-sushi.com.my"
KEY = "8e2643d6b5497d55227072f38b0495a9"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls() -> list[str]:
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    urls = sitemap_urls()
    if args:
        wanted = {a.strip("/") for a in args}
        urls = [u for u in urls if u.rstrip("/").split("/")[-1] in wanted]
    if not urls:
        print("送るURLがありません")
        return 1
    print(f"{len(urls)} URL:")
    for u in urls:
        print("  " + u)
    if dry:
        return 0

    # 送る前に、本番に確認キーが出ているかを確かめる（出ていないと 403 になる）
    key_url = f"https://{HOST}/{KEY}.txt"
    try:
        req = urllib.request.Request(key_url, headers={"User-Agent": "Mozilla/5.0 (OribeIndexNow)"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8").strip()
        if body != KEY:
            print(f"確認キーの中身が違います: {key_url}")
            return 2
    except urllib.error.URLError as e:
        print(f"確認キーが本番にありません（先に cPanel で Deploy HEAD Commit）: {key_url} {e}")
        return 2

    payload = {"host": HOST, "key": KEY, "keyLocation": key_url, "urlList": urls}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: HTTP {r.status}（200/202 なら受け付け済み）")
            return 0
    except urllib.error.HTTPError as e:
        print(f"IndexNow: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:200]}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
