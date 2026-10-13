"""
トップページとメニューページに「貸切・プライベートイベント」への案内枠を入れる(英語ページのみ)。
中国語・日本語ページは、このあと build_i18n.py build で反映する。

使い方:  python scripts/private_events_promo.py
目印コメント(pe-promo:start / end)の中を毎回作り直すので、何度実行しても同じ結果になる。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- pe-promo:start -->", "<!-- pe-promo:end -->"

BLOCK = (
    START
    + '<section class="pe-promo"><div class="pe-promo-inner">'
    + '<div class="pe-promo-photo"><img src="/images/oribe-private-room-course-p-800.webp" '
    + 'srcset="/images/oribe-private-room-course-p-800.webp 800w, /images/oribe-private-room-course.webp 1600w" '
    + 'sizes="(max-width: 767px) 100vw, 560px" loading="lazy" width="1600" height="1067" '
    + 'alt="A private room at Sushi Oribe set with a full omakase course"/></div>'
    + '<div class="pe-promo-text">'
    + '<div class="pe-promo-eyebrow">Private Events &amp; Off-Site Catering</div>'
    + '<h2 class="pe-promo-heading">Omakase, Wherever You Celebrate</h2>'
    + '<p class="pe-promo-body">In our private room or at your home, office or event venue. '
    + 'Birthdays, anniversaries, business dinners and full buyouts, with Chef Naoya Kawasaki tailoring '
    + 'the omakase to your guests and occasion.</p>'
    + '<a href="/private-events" class="pe-promo-btn">Explore Private Events</a>'
    + "</div></div></section>"
    + END
)

# ページごとの差し込み位置(この文字列の直前に入れる)
ANCHORS = {
    "index.html": '<section class="section-8">',      # Meet Our Chef の前(季節メニューの後)
    "menu.html": '<section id="seasonal-omakase">',  # コース一覧(lunch/dinner)の後、季節メニューの前
}


def insert(page: str) -> None:
    path = ROOT / page
    s = path.read_text(encoding="utf-8")
    if START in s:  # 既にある → 作り直す
        a, b = s.index(START), s.index(END) + len(END)
        s = s[:a] + s[b:]
    pos = s.index(ANCHORS[page])
    s = s[:pos] + BLOCK + s[pos:]
    path.write_text(s, encoding="utf-8")
    print(f"{page}: 案内枠 {s.count(START)} 個")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for page in ANCHORS:
        insert(page)
