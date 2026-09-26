"""
多言語ページ(/zh/ 中国語簡体字, /ja/ 日本語)を英語ページから生成するスクリプト。

英語の *.html が原本。翻訳は i18n/zh.json と i18n/ja.json に
「英語の文字列 → 訳文」の辞書として持つ。

使い方:
  python scripts/build_i18n.py extract   # 翻訳対象の文字列を i18n/_keys.json に書き出す
  python scripts/build_i18n.py build     # zh/ ja/ を生成し、全ページに言語切替と hreflang を入れる
  python scripts/build_i18n.py check     # 辞書に無い文字列(未翻訳)を一覧表示する

英語ページの文章を変えたら:
  1. python scripts/build_i18n.py check で未翻訳を確認
  2. i18n/zh.json と i18n/ja.json に訳を追加
  3. python scripts/build_i18n.py build
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://oribe-sushi.com.my"
PAGES = ["index", "menu", "our-chef", "gallery", "about",
         "sake-pairing", "omakase", "private-events"]
LANGS = {
    # code: (hreflang, <html lang>, og:locale, 切替表示名)
    "en": ("en", "en", "en_MY", "EN"),
    "zh": ("zh-Hans", "zh-Hans", "zh_CN", "中文"),
    "ja": ("ja", "ja", "ja_JP", "日本語"),
}
TRANSLATED = ["zh", "ja"]

ATTR_NAMES = ("alt", "title", "aria-label", "placeholder")
META_KEYS = {"description", "og:title", "og:description",
             "twitter:title", "twitter:description"}

I18N_START = "<!-- i18n:start -->"
I18N_END = "<!-- i18n:end -->"
SWITCH_START = "<!-- i18n-switch:start -->"
SWITCH_END = "<!-- i18n-switch:end -->"

SKIP_BLOCK = re.compile(r"(<(script|style|noscript)\b.*?</\2>)", re.S | re.I)
TEXT_SEG = re.compile(r">([^<]+)<")
WORDY = re.compile(r"[A-Za-z぀-ヿ㐀-鿿]")


def norm(s: str) -> str:
    """辞書の見出し用に正規化(実体参照を戻し、空白をまとめる)。"""
    s = html.unescape(s).replace("‍", "").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def translatable(key: str) -> bool:
    return bool(key) and bool(WORDY.search(key))


def page_url(lang: str, page: str) -> str:
    slug = "" if page == "index" else page
    if lang == "en":
        return f"{SITE}/{slug}" if slug else SITE
    return f"{SITE}/{lang}/{slug}" if slug else f"{SITE}/{lang}/"


def page_path(lang: str, page: str) -> str:
    slug = "" if page == "index" else page
    if lang == "en":
        return f"/{slug}"
    return f"/{lang}/{slug}"


# ---------------------------------------------------------------- 抽出

def split_protected(src: str):
    """script/style/noscript を保護しつつ、それ以外の部分を順に返す。"""
    parts = []
    pos = 0
    for m in SKIP_BLOCK.finditer(src):
        parts.append((False, src[pos:m.start()]))
        parts.append((True, m.group(0)))
        pos = m.end()
    parts.append((False, src[pos:]))
    return parts


def iter_keys(src: str):
    head_end = src.find("</head>")
    title = re.search(r"<title>(.*?)</title>", src, re.S)
    if title:
        yield norm(title.group(1))
    for m in re.finditer(r"<meta\s[^>]*>", src[:head_end]):
        tag = m.group(0)
        name = re.search(r'(?:name|property)="([^"]+)"', tag)
        content = re.search(r'content="([^"]*)"', tag)
        if name and content and name.group(1) in META_KEYS:
            yield norm(content.group(1))
    body = src[src.find("<body"):]
    for protected, chunk in split_protected(body):
        if protected:
            continue
        for m in TEXT_SEG.finditer(chunk):
            k = norm(m.group(1))
            if translatable(k):
                yield k
        for m in re.finditer(r'\s(%s)="([^"]*)"' % "|".join(ATTR_NAMES), chunk):
            k = norm(m.group(2))
            if translatable(k):
                yield k


def extract():
    seen = {}
    for p in PAGES:
        src = (ROOT / f"{p}.html").read_text(encoding="utf-8")
        # 言語切替は翻訳しないので対象外
        src = re.sub(re.escape(SWITCH_START) + r".*?" + re.escape(SWITCH_END), "", src, flags=re.S)
        for k in iter_keys(src):
            seen.setdefault(k, []).append(p)
    out = {k: sorted(set(v)) for k, v in seen.items()}
    (ROOT / "i18n" / "_keys.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out)} keys -> i18n/_keys.json")
    return out


# ---------------------------------------------------------------- 生成

def load_dict(lang: str) -> dict:
    p = ROOT / "i18n" / f"{lang}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def esc_text(s: str) -> str:
    return html.escape(s, quote=False)


def esc_attr(s: str) -> str:
    return html.escape(s, quote=True)


def translate_html(src: str, d: dict, missing: set) -> str:
    def tr(raw: str, is_attr: bool) -> str:
        k = norm(raw)
        if not translatable(k):
            return raw
        if k not in d:
            missing.add(k)
            return raw
        v = d[k]
        if is_attr:
            # 改行位置の目印(ゼロ幅スペース)は本文の見出し用。title・meta・alt には入れない
            v = v.replace("​", "")
        lead = raw[: len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        return lead + (esc_attr(v) if is_attr else esc_text(v)) + trail

    # <title>
    src = re.sub(r"(<title>)(.*?)(</title>)",
                 lambda m: m.group(1) + tr(m.group(2), False).replace("​", "") + m.group(3),
                 src, count=1, flags=re.S)

    # meta description / og / twitter
    head_end = src.find("</head>")
    head, rest = src[:head_end], src[head_end:]

    def meta_repl(m):
        tag = m.group(0)
        name = re.search(r'(?:name|property)="([^"]+)"', tag)
        if not name or name.group(1) not in META_KEYS:
            return tag
        return re.sub(r'content="([^"]*)"',
                      lambda c: 'content="' + tr(c.group(1), True) + '"', tag, count=1)
    head = re.sub(r"<meta\s[^>]*>", meta_repl, head)
    src = head + rest

    # body のテキストと属性
    b = src.find("<body")
    pre, body = src[:b], src[b:]
    out = []
    for protected, chunk in split_protected(body):
        if protected:
            out.append(chunk)
            continue
        chunk = TEXT_SEG.sub(lambda m: ">" + tr(m.group(1), False) + "<", chunk)
        chunk = re.sub(r'(\s(?:%s)=")([^"]*)(")' % "|".join(ATTR_NAMES),
                       lambda m: m.group(1) + tr(m.group(2), True) + m.group(3), chunk)
        out.append(chunk)
    return pre + "".join(out)


def rewrite_links(src: str, lang: str) -> str:
    """サイト内リンクを /zh/... /ja/... に向け直す。"""
    def repl(m):
        path, frag = m.group(1), m.group(2) or ""
        slug = path.strip("/")
        if slug == "":
            return f'href="/{lang}/{frag}"'
        if slug in PAGES:
            return f'href="/{lang}/{slug}{frag}"'
        return m.group(0)
    return re.sub(r'href="(/[a-z-]*)(#[^"]*)?"', repl, src)


def set_html_lang(src: str, lang: str) -> str:
    code = LANGS[lang][1]
    def repl(m):
        tag = re.sub(r'\slang="[^"]*"', "", m.group(0))
        return tag[:-1] + f' lang="{code}">'
    return re.sub(r"<html\b[^>]*>", repl, src, count=1)


def head_block(lang: str, page: str) -> str:
    lines = [I18N_START]
    for l in ["en"] + TRANSLATED:
        lines.append(f'  <link rel="alternate" hreflang="{LANGS[l][0]}" href="{page_url(l, page)}">')
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="{page_url("en", page)}">')
    lines.append(f'  <meta property="og:locale" content="{LANGS[lang][2]}">')
    for l in ["en"] + TRANSLATED:
        if l != lang:
            lines.append(f'  <meta property="og:locale:alternate" content="{LANGS[l][2]}">')
    lines.append("  " + I18N_END)
    return "\n  ".join(lines)


def switch_html(lang: str, page: str) -> str:
    links = []
    for l in ["en"] + TRANSLATED:
        label = LANGS[l][3]
        cur = ' aria-current="true" class="is-current"' if l == lang else ""
        links.append(f'<a href="{page_path(l, page)}" hreflang="{LANGS[l][0]}" lang="{LANGS[l][1]}"{cur}>{label}</a>')
    return (f'{SWITCH_START}<div class="lang-switch" role="navigation" aria-label="Language">'
            + '<span class="lang-switch-sep">·</span>'.join(links)
            + f"</div>{SWITCH_END}")


def apply_common(src: str, lang: str, page: str) -> str:
    # 以前の挿入分を消してから入れ直す(何度実行しても同じ結果)
    src = re.sub(r"\s*" + re.escape(I18N_START) + r".*?" + re.escape(I18N_END) + r"[ \t]*\n?", "", src, flags=re.S)
    src = re.sub(re.escape(SWITCH_START) + r".*?" + re.escape(SWITCH_END), "", src, flags=re.S)

    src = set_html_lang(src, lang)

    # canonical と og:url を言語ごとの URL に
    url = page_url(lang, page)
    src = re.sub(r'<link href="[^"]*" rel="canonical"\s*/?>',
                 f'<link href="{url}" rel="canonical">', src, count=1)
    if 'property="og:url"' in src:
        src = re.sub(r'<meta content="[^"]*" property="og:url"\s*/?>',
                     f'<meta content="{url}" property="og:url">', src)

    # hreflang と og:locale
    src = src.replace("</head>", "  " + head_block(lang, page) + "\n</head>", 1)

    # 言語切替: ヘッダー(固定ナビ)の先頭とフッターのコピーライトの前
    sw = switch_html(lang, page)
    src = re.sub(r'(<div[^>]*class="navbar-logo-center-container-2[^"]*shadow-three[^"]*"[^>]*>)',
                 lambda m: m.group(1) + sw, src)
    return src


def build():
    total_missing = {}
    for page in PAGES:
        en_path = ROOT / f"{page}.html"
        en = en_path.read_text(encoding="utf-8")
        en_out = apply_common(en, "en", page)
        if en_out != en:
            en_path.write_text(en_out, encoding="utf-8")

        for lang in TRANSLATED:
            d = load_dict(lang)
            missing = set()
            base = re.sub(re.escape(SWITCH_START) + r".*?" + re.escape(SWITCH_END), "", en_out, flags=re.S)
            base = re.sub(r"\s*" + re.escape(I18N_START) + r".*?" + re.escape(I18N_END) + r"[ \t]*\n?", "", base, flags=re.S)
            out = translate_html(base, d, missing)
            out = rewrite_links(out, lang)
            out = apply_common(out, lang, page)
            dest = ROOT / lang / f"{page}.html"
            dest.parent.mkdir(exist_ok=True)
            dest.write_text(out, encoding="utf-8")
            for k in missing:
                total_missing.setdefault(lang, set()).add(k)
    for lang in TRANSLATED:
        n = len(total_missing.get(lang, ()))
        print(f"{lang}: built {len(PAGES)} pages, untranslated strings: {n}")
    return total_missing


def check():
    keys = extract()
    for lang in TRANSLATED:
        d = load_dict(lang)
        miss = [k for k in keys if k not in d]
        extra = [k for k in d if k not in keys]
        print(f"--- {lang}: missing {len(miss)}, unused {len(extra)}")
        for k in miss:
            print("  MISSING:", k[:120])


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    {"extract": extract, "build": build, "check": check}[cmd]()
