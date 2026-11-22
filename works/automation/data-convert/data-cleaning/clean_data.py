"""データ整形スクリプト（自主制作サンプル）

before_customers.csv（表記がばらばらな顧客リスト）を整え、after_customers.xlsx に保存します。

  python clean_data.py

整える内容：
  - 氏名：前後の空白を除き、姓と名の間を全角スペース1つにそろえる
  - フリガナ：ひらがな・半角カナを全角カタカナにそろえる
  - 電話番号：全角数字・括弧・空白を除き、ハイフン区切り（携帯 3-4-4／固定 2〜4桁の市外局番）にそろえる
  - 郵便番号：〒・全角を除き 123-4567 の形にそろえる
  - 登録日：2026/1/5・2026-01-05・令和8年1月5日・R8.1.5 などを 2026-01-05 にそろえる
  - 購入金額：¥・円・カンマ・全角数字を除き、数値にする
  - 重複：電話番号が同じ行は、登録日が新しい行を残す
  - 直せなかった値は「要確認」シートに理由と一緒に出す
すべての変更は「変更ログ」シートに、行番号・項目・変更前・変更後で残します。

必要なもの：Python 3.10 以上、openpyxl
"""
from __future__ import annotations

import csv
import re
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

HERE = Path(__file__).parent
SRC = HERE / "before_customers.csv"
OUT = HERE / "after_customers.xlsx"
REIWA = 2018  # 令和n年 = 2018 + n


def z2h(s: str) -> str:
    return unicodedata.normalize("NFKC", s or "").strip()


def clean_name(v):
    s = re.sub(r"[\s　]+", "　", (v or "").strip())
    return s, None


def clean_kana(v):
    s = unicodedata.normalize("NFKC", v or "").strip()
    s = "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)
    s = re.sub(r"[\s]+", "　", s)
    if s and not re.fullmatch(r"[ァ-ヶー　]+", s):
        return s, "カタカナ以外の文字が含まれています"
    return s, None


def clean_tel(v):
    d = re.sub(r"\D", "", z2h(v))
    if re.fullmatch(r"0[789]0\d{8}", d):
        return f"{d[:3]}-{d[3:7]}-{d[7:]}", None
    if re.fullmatch(r"0[789]0\d{7}", d):
        return z2h(v), "携帯電話の番号が10桁しかありません"
    if re.fullmatch(r"0\d{9}", d):
        if d[:2] in ("03", "06"):
            return f"{d[:2]}-{d[2:6]}-{d[6:]}", None
        return f"{d[:3]}-{d[3:6]}-{d[6:]}", None
    return z2h(v), "電話番号の桁数が合いません"


def clean_zip(v):
    d = re.sub(r"\D", "", z2h(v))
    if len(d) == 7:
        return f"{d[:3]}-{d[3:]}", None
    return z2h(v), "郵便番号が7桁ではありません"


def clean_date(v):
    s = z2h(v).replace(" ", "")
    m = re.fullmatch(r"(?:令和|R)(\d{1,2})[.年/](\d{1,2})[.月/](\d{1,2})日?", s)
    if m:
        y, mo, d = REIWA + int(m[1]), int(m[2]), int(m[3])
    else:
        m = re.fullmatch(r"(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?", s)
        if not m:
            return s, "日付として読めません"
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
    try:
        return date(y, mo, d), None
    except ValueError:
        return s, "存在しない日付です"


def clean_amount(v):
    s = re.sub(r"[¥￥円,\s]", "", z2h(v))
    if re.fullmatch(r"\d+", s):
        return int(s), None
    return z2h(v), "金額として読めません"


RULES = {"氏名": clean_name, "フリガナ": clean_kana, "電話番号": clean_tel,
         "郵便番号": clean_zip, "登録日": clean_date, "購入金額": clean_amount}


def main():
    with SRC.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    log, check, cleaned = [], [], []
    for i, row in enumerate(rows, start=2):
        new = dict(row)
        for col, fn in RULES.items():
            before = row.get(col, "")
            after, err = fn(before)
            new[col] = after
            shown = after.isoformat() if isinstance(after, date) else str(after)
            if shown != before:
                log.append((i, col, before, shown))
            if err:
                check.append((i, col, before, err))
        new["_src"] = i
        cleaned.append(new)

    # 重複：電話番号が同じなら登録日が新しい行を残す
    best: dict[str, dict] = {}
    for r in cleaned:
        key = r["電話番号"]
        cur = best.get(key)
        rd = r["登録日"] if isinstance(r["登録日"], date) else date.min
        if cur is None or rd > (cur["登録日"] if isinstance(cur["登録日"], date) else date.min):
            if cur is not None:
                log.append((cur["_src"], "重複", f"{cur['氏名']}（{key}）", f"{r['_src']}行目を残して削除"))
            best[key] = r
        else:
            log.append((r["_src"], "重複", f"{r['氏名']}（{key}）", f"{cur['_src']}行目を残して削除"))
    result = sorted(best.values(), key=lambda r: r["_src"])

    wb = Workbook()
    ws = wb.active
    ws.title = "整形後"
    ws.append(cols)
    for r in result:
        ws.append([r[c] for c in cols])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2B3038")
    di, ai = cols.index("登録日") + 1, cols.index("購入金額") + 1
    for row in ws.iter_rows(min_row=2):
        row[di - 1].number_format = "yyyy-mm-dd"
        row[ai - 1].number_format = "#,##0"
    for col, w in zip("ABCDEFGH", [8, 16, 20, 16, 11, 34, 12, 11]):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"

    lg = wb.create_sheet("変更ログ")
    lg.append(["元の行", "項目", "変更前", "変更後"])
    for r in log:
        lg.append(r)
    ck = wb.create_sheet("要確認")
    ck.append(["元の行", "項目", "値", "理由"])
    for r in check:
        ck.append(r)
    for sh, widths in ((lg, [8, 10, 34, 34]), (ck, [8, 10, 30, 30])):
        for c in sh[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="2B3038")
        for col, w in zip("ABCD", widths):
            sh.column_dimensions[col].width = w
    wb.save(OUT)
    print(f"入力 {len(rows)}行 → 整形後 {len(result)}行（重複 {len(rows) - len(result)}行を削除）")
    print(f"変更 {len(log)}件・要確認 {len(check)}件 → {OUT.name}")


if __name__ == "__main__":
    main()
