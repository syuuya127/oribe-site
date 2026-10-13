"""
作り直したカードと、いまサイトに載っているカードを 1 枚ずつ比べる(道具が壊れていないかの確認用)。

使い方:  python scripts/menu_cards/compare.py <作り直したフォルダ> [images フォルダ]
1 画素あたりの平均の色の差(0〜255)を出す。圧縮のゆらぎ程度なら 1〜2 前後、
レイアウトや文字がずれていれば 10 以上になる。
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

new_dir = Path(sys.argv[1])
old_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent.parent / "images"
worst = 0.0
rows = 0
for f in sorted(new_dir.glob("*.webp")):
    if f.stem.endswith("-p-500"):
        continue
    old = old_dir / f.name
    if not old.exists():
        print(f"{f.name}: 比較先なし")
        continue
    a = Image.open(f).convert("RGB")
    b = Image.open(old).convert("RGB")
    if a.size != b.size:
        print(f"{f.name}: 大きさが違う {a.size} / {b.size}")
        worst = 999
        continue
    diff = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
    worst = max(worst, diff)
    rows += 1
    print(f"{f.name}: 平均の差 {diff:.2f}")
print(f"--- {rows} 枚を比較。最大の差 {worst:.2f}")
