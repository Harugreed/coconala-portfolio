"""請求書自動生成ブックを作るスクリプト（自主制作サンプル）

作られる invoice_book.xlsx のしくみ：
  - 「明細（入力）」シートに取引を1行ずつ入力する
  - 「請求書」シートで取引先コードと請求月を選ぶと、その取引先・その月の明細だけが
    数式で請求書に並び、税率別の小計・消費税・合計が計算される
  - マクロは使っていません（.xlsx のまま動きます）。Excel 2010 以降で動く関数だけを使っています

  python make_invoice_book.py      # → invoice_book.xlsx を作り直す
必要なもの：Python 3.10 以上、openpyxl
"""
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).with_name("invoice_book.xlsx")
INK, TINT, KEY = "2B3038", "F2F3F5", "FFF4CC"
thin = Side(style="thin", color="9AA0A6")
B = Border(left=thin, right=thin, top=thin, bottom=thin)
MAXROW = 300   # 明細の数式を用意しておく行数
LINES = 15     # 請求書に並べる明細の行数

CLIENTS = [
    ("C001", "株式会社 青葉商事", "御中", "980-0000", "宮城県仙台市青葉区一番町1-2-3", "月末締め翌月末払い"),
    ("C002", "喫茶 こもれび", "御中", "460-0000", "愛知県名古屋市中区栄3-5-1", "月末締め翌月20日払い"),
    ("C003", "有限会社 みなと設備", "御中", "231-0000", "神奈川県横浜市中区海岸通1-1", "月末締め翌月末払い"),
]
ITEMS = [  # 日付, 取引先, 品名, 数量, 単価, 税率
    (date(2026, 10, 3), "C001", "コーヒー豆 1kg（若葉ブレンド）", 4, 6800, 0.08),
    (date(2026, 10, 3), "C001", "ペーパーフィルター 100枚", 10, 450, 0.10),
    (date(2026, 10, 10), "C002", "コーヒー豆 1kg（エチオピア）", 3, 8200, 0.08),
    (date(2026, 10, 15), "C001", "ドリップポット 1.0L", 1, 5800, 0.10),
    (date(2026, 10, 17), "C003", "焼き菓子ギフト 8個入", 12, 2400, 0.08),
    (date(2026, 10, 24), "C001", "コーヒー豆 1kg（若葉ブレンド）", 4, 6800, 0.08),
    (date(2026, 10, 24), "C002", "マグカップ（白）", 6, 1600, 0.10),
    (date(2026, 10, 31), "C001", "抽出器具の点検作業", 1, 8000, 0.10),
    (date(2026, 11, 7), "C001", "コーヒー豆 1kg（若葉ブレンド）", 5, 6800, 0.08),
    (date(2026, 11, 7), "C002", "コーヒー豆 1kg（エチオピア）", 2, 8200, 0.08),
]


def head(ws, row, values, widths=None):
    for i, v in enumerate(values, 1):
        c = ws.cell(row=row, column=i, value=v)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=INK)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = B
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[chr(64 + i)].width = w


def main():
    wb = Workbook()

    # 取引先マスタ
    m = wb.active
    m.title = "取引先"
    head(m, 1, ["取引先コード", "取引先名", "敬称", "郵便番号", "住所", "支払条件"], [13, 26, 7, 11, 34, 20])
    for r in CLIENTS:
        m.append(r)
    m.freeze_panes = "A2"

    # 明細（入力）
    d = wb.create_sheet("明細（入力）")
    head(d, 1, ["日付", "取引先コード", "品名", "数量", "単価", "税率", "金額", "（自動）対象", "（自動）連番"],
         [12, 13, 34, 7, 10, 7, 12, 12, 12])
    for i in range(2, MAXROW + 2):
        if i - 2 < len(ITEMS):
            dt_, code, name, q, price, tax = ITEMS[i - 2]
            for col, v in zip("ABCDEF", (dt_, code, name, q, price, tax)):
                d[f"{col}{i}"] = v
        d[f"A{i}"].number_format = "yyyy/mm/dd"
        d[f"E{i}"].number_format = "#,##0"
        d[f"F{i}"].number_format = "0%"
        d[f"G{i}"] = f'=IF(OR(D{i}="",E{i}=""),"",D{i}*E{i})'
        d[f"G{i}"].number_format = "#,##0"
        # 請求書シートで選んだ取引先・請求月に一致する行を 1 とする
        d[f"H{i}"] = (f'=IF(AND(B{i}=請求書!$C$4,A{i}<>"",TEXT(A{i},"yyyy/mm")=請求書!$C$5),1,0)')
        d[f"I{i}"] = f'=IF(H{i}=1,COUNTIF($H$2:H{i},1),"")'
        for col in "GHI":
            d[f"{col}{i}"].fill = PatternFill("solid", fgColor=TINT)
            d[f"{col}{i}"].font = Font(color="5D626B")
    d.freeze_panes = "A2"
    dv_tax = DataValidation(type="list", formula1='"0.08,0.1"', allow_blank=True)
    d.add_data_validation(dv_tax)
    dv_tax.add(f"F2:F{MAXROW + 1}")
    dv_code = DataValidation(type="list", formula1="=取引先!$A$2:$A$100", allow_blank=True)
    d.add_data_validation(dv_code)
    dv_code.add(f"B2:B{MAXROW + 1}")

    # 請求書（出力）
    s = wb.create_sheet("請求書", 0)
    for col, w in zip("ABCDEFG", [3, 13, 36, 8, 12, 9, 14]):
        s.column_dimensions[col].width = w
    s["B2"] = "請求書"
    s["B2"].font = Font(size=20, bold=True)
    s["B4"], s["B5"] = "取引先コード", "請求月"
    s["C4"], s["C5"] = "C001", "2026/10"
    for c in ("C4", "C5"):
        s[c].fill = PatternFill("solid", fgColor=KEY)
        s[c].border = B
        s[c].font = Font(bold=True)
    s["C5"].number_format = "@"  # 2026/10 が日付に変換されないよう文字列にする
    s["I4"] = "← C4・C5 の黄色のセルを選ぶと請求書が切り替わります（この列は印刷されません）"
    s["I5"] = "← 請求月は 2026/10 の形で入力します"
    s["I5"].font = Font(color="5D626B", size=9)
    s["I4"].font = Font(color="5D626B", size=9)
    dv_sel = DataValidation(type="list", formula1="=取引先!$A$2:$A$100")
    s.add_data_validation(dv_sel)
    dv_sel.add("C4")

    s["B7"] = '=VLOOKUP($C$4,取引先!$A:$F,2,FALSE)&" "&VLOOKUP($C$4,取引先!$A:$F,3,FALSE)'
    s["B7"].font = Font(size=14, bold=True)
    s["B8"] = '="〒"&VLOOKUP($C$4,取引先!$A:$F,4,FALSE)&" "&VLOOKUP($C$4,取引先!$A:$F,5,FALSE)'
    s["E7"] = "請求日"
    s["F7"] = '=TEXT(EOMONTH(DATEVALUE($C$5&"/1"),0),"yyyy/mm/dd")'
    s["E8"] = "支払条件"
    s["F8"] = "=VLOOKUP($C$4,取引先!$A:$F,6,FALSE)"
    s["E10"], s["E11"], s["E12"] = "白杢珈琲 卸部（架空）", "登録番号 T0000000000000", "電話 000-0000-0000"
    for c in ("E10", "E11", "E12"):
        s[c].font = Font(size=9)

    s["B14"] = "ご請求金額（税込）"
    s["B14"].font = Font(bold=True)
    s["D14"] = "=G38"
    s["D14"].number_format = '"¥"#,##0'
    s["D14"].font = Font(size=16, bold=True)
    s.merge_cells("D14:E14")

    hdr = ["日付", "品名", "数量", "単価", "税率", "金額"]
    for i, v in enumerate(hdr):
        c = s.cell(row=16, column=2 + i, value=v)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=INK)
        c.border = B
        c.alignment = Alignment(horizontal="center")
    rng = lambda col: f"'明細（入力）'!${col}$2:${col}${MAXROW + 1}"
    for n in range(1, LINES + 1):
        r = 16 + n
        pos = f"MATCH({n},{rng('I')},0)"
        for j, col in enumerate("ACDEFG"):
            cell = s.cell(row=r, column=2 + j, value=f'=IFERROR(INDEX({rng(col)},{pos}),"")')
            cell.border = B
        s.cell(row=r, column=2).number_format = "mm/dd"
        s.cell(row=r, column=5).number_format = "#,##0"
        s.cell(row=r, column=6).number_format = "0%"
        s.cell(row=r, column=7).number_format = "#,##0"
    s["B33"] = f'=IF(COUNTIF({rng("H")},1)>{LINES},"※明細が{LINES}行を超えています。行を増やしてください","")'
    s["B33"].font = Font(color="C0392B", size=9)

    labels = [(34, "10%対象 小計", f'=SUMIFS({rng("G")},{rng("H")},1,{rng("F")},0.1)'),
              (35, "10%対象 消費税", "=ROUNDDOWN(G34*0.1,0)"),
              (36, "8%対象 小計（軽減税率）", f'=SUMIFS({rng("G")},{rng("H")},1,{rng("F")},0.08)'),
              (37, "8%対象 消費税", "=ROUNDDOWN(G36*0.08,0)"),
              (38, "合計（税込）", "=G34+G35+G36+G37")]
    for r, label, f in labels:
        s[f"E{r}"] = label
        s[f"G{r}"] = f
        s[f"G{r}"].number_format = "#,##0"
        s[f"G{r}"].border = B
        s.merge_cells(f"E{r}:F{r}")
    s["E38"].font = s["G38"].font = Font(bold=True)
    s["B40"] = "※消費税は税率ごとに合計した金額から計算し、1円未満を切り捨てています。"
    s["B41"] = "※自主制作サンプルです。取引先・金額・登録番号は架空です。"
    for c in ("B40", "B41"):
        s[c].font = Font(size=9, color="5D626B")
    s.print_area = "A1:G41"
    s.page_setup.paperSize = s.PAPERSIZE_A4
    s.sheet_properties.pageSetUpPr.fitToPage = True
    s.page_setup.fitToWidth = 1
    s.page_setup.fitToHeight = 1

    wb.save(OUT)
    print(f"作成：{OUT.name}")


if __name__ == "__main__":
    main()
