"""リスト形式見本を作るスクリプト（自主制作サンプル）

営業リスト（50行）・SNSインフルエンサーリスト（30行）の「形式」を見せるための架空データです。
会社名・URL・連絡先・アカウントはすべて架空で、URL・メールは予約済みの .example ドメインを使っています。
  python make_lists.py   → sales_list.xlsx / sales_list.csv / influencer_list.xlsx / influencer_list.csv
"""
import csv
import random
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).parent
random.seed(20261122)
INK = "2B3038"

PREFS = [("東京都", "03"), ("大阪府", "06"), ("愛知県", "052"), ("福岡県", "092"), ("宮城県", "022"), ("北海道", "011"), ("広島県", "082"), ("京都府", "075")]
CITY = {"東京都": "港区芝", "大阪府": "大阪市北区梅田", "愛知県": "名古屋市中区栄", "福岡県": "福岡市博多区博多駅前",
        "宮城県": "仙台市青葉区中央", "北海道": "札幌市中央区北3条西", "広島県": "広島市中区八丁堀", "京都府": "京都市中京区烏丸通"}
INDUSTRY = ["飲食店", "美容室", "整体院", "工務店", "学習塾", "歯科医院", "不動産", "小売店"]
WORDS = ["あおば", "みなと", "さくら", "ひだまり", "つばさ", "こもれび", "わかば", "あさひ", "しらかわ", "つきみ", "かえで", "そよかぜ", "ほしの", "あかね", "すずらん"]
ROMA = {"あおば": "aoba", "みなと": "minato", "さくら": "sakura", "ひだまり": "hidamari", "つばさ": "tsubasa", "こもれび": "komorebi",
        "わかば": "wakaba", "あさひ": "asahi", "しらかわ": "shirakawa", "つきみ": "tsukimi", "かえで": "kaede", "そよかぜ": "soyokaze",
        "ほしの": "hoshino", "あかね": "akane", "すずらん": "suzuran"}
SUFFIX = {"飲食店": ("食堂", "shokudo"), "美容室": ("ヘアサロン", "hair"), "整体院": ("整体院", "seitai"), "工務店": ("工務店", "koumuten"),
          "学習塾": ("学習塾", "juku"), "歯科医院": ("歯科", "dental"), "不動産": ("不動産", "fudosan"), "小売店": ("商店", "shoten")}
STATUS = ["未連絡", "資料送付済み", "返信あり", "商談予定", "見送り"]


def style(ws, widths):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=INK)
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions


def save(name, head, rows, widths, validations=()):
    with (HERE / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(head); w.writerows(rows)
    wb = Workbook(); ws = wb.active; ws.title = "リスト"
    ws.append(head)
    for r in rows:
        ws.append(r)
    style(ws, widths)
    for col, opts in validations:
        dv = DataValidation(type="list", formula1='"' + ",".join(opts) + '"', allow_blank=True)
        ws.add_data_validation(dv); dv.add(f"{col}2:{col}{len(rows) + 1}")
    note = wb.create_sheet("説明")
    note.append(["このリストは形式見本です。会社名・URL・連絡先・アカウントはすべて架空で、実在の個人・企業の情報は含みません。"])
    note.column_dimensions["A"].width = 110
    wb.save(HERE / f"{name}.xlsx")


def sales():
    rows, used = [], set()
    for i in range(1, 51):
        ind = INDUSTRY[(i - 1) % len(INDUSTRY)]
        while True:
            w = random.choice(WORDS)
            if (w, ind) not in used:
                used.add((w, ind)); break
        pref, area = random.choice(PREFS)
        jp, en = SUFFIX[ind]
        name = f"{w}{jp}"
        url = f"https://www.{ROMA[w]}-{en}.example/"
        tel = f"{area}-{'0000-' if len(area) == 2 else '000-'}{i:04d}"
        mail = f"info@{ROMA[w]}-{en}.example"
        addr = f"{pref}{CITY[pref]}{random.randint(1, 5)}-{random.randint(1, 20)}-{random.randint(1, 12)}"
        has_form = random.choice(["あり", "あり", "なし"])
        sp = random.choice(["対応", "対応", "未対応"])
        memo = {"未対応": "スマートフォン表示に未対応", "対応": random.choice(["Instagramの更新が月1回以下", "予約ページが外部サービスのみ", "お知らせが1年以上更新なし", "特記事項なし"])}[sp]
        rows.append([f"S{i:03d}", name, ind, pref, addr, url, tel, mail, has_form, sp, memo, random.choice(STATUS)])
    head = ["No.", "会社名・店名", "業種", "都道府県", "住所", "URL", "電話番号", "メール", "問い合わせフォーム", "スマホ対応", "備考（サイトの状態）", "対応状況"]
    save("sales_list", head, rows, [7, 22, 10, 9, 34, 36, 15, 32, 10, 9, 28, 12], [("L", STATUS)])
    return len(rows)


def influencers():
    genres = ["カフェ巡り", "パン", "料理・レシピ", "ネイル", "ヘアアレンジ", "子育て", "インテリア", "キャンプ", "旅行", "ファッション"]
    rows = []
    for i in range(1, 31):
        g = genres[(i - 1) % len(genres)]
        followers = random.choice([random.randint(2000, 9999), random.randint(10000, 49999), random.randint(50000, 180000)])
        tier = "ナノ（1万未満）" if followers < 10000 else "マイクロ（1万〜5万）" if followers < 50000 else "ミドル（5万以上）"
        posts = random.randint(120, 1800)
        eng = round(random.uniform(1.2, 6.5), 1)
        pref = random.choice([p for p, _ in PREFS])
        rows.append([f"I{i:03d}", f"@sample_{ROMA[random.choice(WORDS)]}_{i:02d}", "Instagram", g, followers, tier, posts, eng, pref,
                     random.choice(["プロフィールのメールで受付", "DMで受付", "受付の記載なし"]), "架空アカウント"])
    head = ["No.", "アカウント", "SNS", "ジャンル", "フォロワー数", "規模", "投稿数", "平均エンゲージメント率（%）", "活動地域", "依頼の受付", "備考"]
    save("influencer_list", head, rows, [7, 26, 11, 13, 12, 18, 9, 24, 10, 24, 14])
    return len(rows)


if __name__ == "__main__":
    print(f"営業リスト {sales()}行・インフルエンサーリスト {influencers()}行を作成しました")
