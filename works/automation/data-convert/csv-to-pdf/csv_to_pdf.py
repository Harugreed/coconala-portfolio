"""CSV → PDF 変換（出荷伝票）自主制作サンプル

input/orders.csv（受注データ）を伝票番号ごとにまとめ、A4 1枚に2伝票ずつ並べた出荷伝票の PDF を作ります。

  python csv_to_pdf.py                          # input/orders.csv → output/shipping_slips.pdf
  python csv_to_pdf.py --csv 別の.csv --out 別の.pdf

しくみ：CSV から印刷用の HTML を組み立て、Google Chrome（または Microsoft Edge）の
ヘッドレス印刷で PDF にします。追加の Python ライブラリは不要です（Python 3.10 以上）。

CSV の列：伝票番号, 出荷日, お届け先名, 敬称（任意）, 郵便番号, 住所, 電話番号, 品名, 数量, 個口, 配達希望, 備考
  同じ伝票番号の行は1枚の伝票の明細としてまとめます。
"""
from __future__ import annotations

import argparse
import csv
import html
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).parent
SENDER = ("白杢珈琲 オンラインストア（架空）", "〒000-0000 みどり野市若葉台2-14-3", "000-0000-0000")
REQUIRED = ["伝票番号", "出荷日", "お届け先名", "郵便番号", "住所", "電話番号", "品名", "数量", "個口"]

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Yu Gothic", "Meiryo", "Noto Sans JP", sans-serif; color: #111; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sheet { width: 210mm; height: 297mm; padding: 10mm 12mm; display: grid; grid-template-rows: 1fr 1fr; gap: 8mm; break-after: page; }
.slip { border: .5mm solid #111; padding: 6mm 7mm; display: grid; grid-template-rows: auto auto 1fr auto; gap: 3mm; position: relative; }
.slip + .slip::before { content: "切り取り線"; position: absolute; top: -6.5mm; left: 0; right: 0; border-top: .3mm dashed #888; font-size: 7pt; color: #888; text-align: center; line-height: 0; }
.top { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: .8mm solid #111; padding-bottom: 2mm; }
.top h1 { margin: 0; font-size: 17pt; letter-spacing: .2em; }
.no { text-align: right; font-size: 9pt; line-height: 1.5; }
.no b { font-size: 15pt; letter-spacing: .05em; font-family: Consolas, monospace; }
.addr { display: grid; grid-template-columns: 1.35fr 1fr; gap: 5mm; font-size: 9pt; }
.addr .to { border: .3mm solid #111; padding: 3mm; }
.addr .lbl { font-size: 7.5pt; color: #444; }
.addr .zip { font-size: 10pt; }
.addr .name { font-size: 14pt; font-weight: 700; margin: 1mm 0; }
.addr .from { padding: 3mm; background: #F2F2F2; line-height: 1.6; }
table { width: 100%; border-collapse: collapse; font-size: 9.5pt; align-self: start; }
th, td { border: .3mm solid #111; padding: 1.6mm 2.5mm; }
th { background: #E6E6E6; font-weight: 700; text-align: left; }
td.q, th.q { text-align: right; width: 18mm; }
.foot { display: grid; grid-template-columns: repeat(4, 1fr); font-size: 8.5pt; border: .3mm solid #111; }
.foot div { padding: 1.6mm 2.5mm; border-left: .3mm solid #111; }
.foot div:first-child { border-left: 0; }
.foot span { display: block; font-size: 7pt; color: #444; }
.sample { position: absolute; right: 7mm; bottom: 1.2mm; font-size: 6.5pt; color: #999; }
"""


def find_browser() -> str:
    cands = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in cands + [shutil.which("google-chrome") or "", shutil.which("chromium") or ""]:
        if c and Path(c).exists():
            return c
    sys.exit("Chrome または Edge が見つかりません。インストール先を find_browser() に追加してください。")


def load(csv_path: Path) -> "OrderedDict[str, list[dict]]":
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"CSV に必要な列がありません：{'、'.join(missing)}")
        slips: "OrderedDict[str, list[dict]]" = OrderedDict()
        for i, row in enumerate(reader, start=2):
            if not row["伝票番号"].strip():
                print(f"  {i}行目：伝票番号が空のため飛ばしました")
                continue
            slips.setdefault(row["伝票番号"].strip(), []).append(row)
    return slips


def honorific(row: dict) -> str:
    """敬称：CSV の「敬称」列があればそれを使い、空なら法人格を含む宛先は「御中」、それ以外は「様」。"""
    v = (row.get("敬称") or "").strip()
    if v:
        return v
    return "御中" if any(k in row["お届け先名"] for k in ("株式会社", "有限会社", "合同会社", "一般社団法人")) else "様"


def slip_html(no: str, rows: list[dict]) -> str:
    h = rows[0]
    e = lambda s: html.escape(str(s or ""))
    items = "".join(f"<tr><td>{e(r['品名'])}</td><td class='q'>{e(r['数量'])}</td></tr>" for r in rows)
    total = sum(int(r["数量"] or 0) for r in rows)
    wish = next((r.get("配達希望") for r in rows if r.get("配達希望")), "指定なし")
    note = "・".join(sorted({r.get("備考", "") for r in rows if r.get("備考")})) or "―"
    return f"""
<section class="slip">
  <div class="top"><h1>出荷伝票</h1><p class="no">伝票番号<br><b>{e(no)}</b></p></div>
  <div class="addr">
    <div class="to"><span class="lbl">お届け先</span><div class="zip">〒{e(h['郵便番号'])}</div><div>{e(h['住所'])}</div><div class="name">{e(h['お届け先名'])} {e(honorific(h))}</div><div>電話 {e(h['電話番号'])}</div></div>
    <div class="from"><span class="lbl">ご依頼主</span><br>{e(SENDER[0])}<br>{e(SENDER[1])}<br>電話 {e(SENDER[2])}</div>
  </div>
  <table><thead><tr><th>品名</th><th class="q">数量</th></tr></thead><tbody>{items}<tr><th>合計</th><th class="q">{total}</th></tr></tbody></table>
  <div class="foot"><div><span>出荷日</span>{e(h['出荷日'])}</div><div><span>個口</span>{e(h['個口'])}</div><div><span>配達希望</span>{e(wish)}</div><div><span>備考</span>{e(note)}</div></div>
  <p class="sample">自主制作サンプル（架空のデータ）</p>
</section>"""


def build_html(slips) -> str:
    keys = list(slips)
    pages = []
    for i in range(0, len(keys), 2):
        pages.append('<div class="sheet">' + "".join(slip_html(k, slips[k]) for k in keys[i:i + 2]) + "</div>")
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'


def main() -> int:
    ap = argparse.ArgumentParser(description="CSV → 出荷伝票 PDF")
    ap.add_argument("--csv", default=str(HERE / "input" / "orders.csv"))
    ap.add_argument("--out", default=str(HERE / "output" / "shipping_slips.pdf"))
    a = ap.parse_args()
    slips = load(Path(a.csv))
    print(f"読み込み：{sum(len(v) for v in slips.values())}行 → 伝票 {len(slips)}枚")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "slips.html"
        page.write_text(build_html(slips), encoding="utf-8")
        out = Path(a.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([find_browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", page.as_uri()], check=True, capture_output=True, timeout=120)
    print(f"出力：{out.name}（A4 {-(-len(slips) // 2)}ページ）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
