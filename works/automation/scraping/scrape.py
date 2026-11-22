"""公開商品ページの収集デモ（自主制作サンプル）

対象：books.toscrape.com
  スクレイピングの練習用に公開されているサンドボックスのECサイトです。
  価格・評価はサイト側でランダムに付けられた値で、実在の商品情報ではありません。

内容：一覧ページから商品を順に読み、詳細ページで分類・在庫数・商品コードを取得して Excel に保存します。
  - ログインが必要なページ・認証を回避する処理は扱いません
  - 1リクエストごとに間隔（既定 1.0 秒）をあけ、サーバーに負荷をかけないようにします
  - robots.txt を最初に確認し、禁止されたパスは取得しません

使い方：
  python scrape.py                 # 100件を取得して output/books_100.xlsx に保存
  python scrape.py --limit 40      # 件数を変える
  python scrape.py --wait 2.0      # 間隔を変える

必要なもの：Python 3.10 以上、openpyxl（pip install openpyxl）
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

BASE = "https://books.toscrape.com/"
UA = "PortfolioScrapingDemo/1.0 (sample; polite crawler)"
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass
class Book:
    title: str
    price_gbp: float
    rating: int
    in_stock: int
    category: str
    upc: str
    url: str


def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


class Fetcher:
    """間隔をあけて取得し、失敗時は3回まで再試行する。"""

    def __init__(self, wait: float):
        self.wait = wait
        self.last = 0.0
        self.robots = urllib.robotparser.RobotFileParser(urllib.parse.urljoin(BASE, "robots.txt"))
        try:
            self.robots.read()
        except urllib.error.URLError:
            self.robots = None  # robots.txt が取得できない場合は制限なしとして扱う

    def get(self, url: str) -> str:
        if self.robots and not self.robots.can_fetch(UA, url):
            raise PermissionError(f"robots.txt で禁止されています: {url}")
        for attempt in range(1, 4):
            sleep = self.wait - (time.monotonic() - self.last)
            if sleep > 0:
                time.sleep(sleep)
            self.last = time.monotonic()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=20) as r:
                    return r.read().decode("utf-8")
            except (urllib.error.URLError, TimeoutError) as e:
                log(f"  再試行 {attempt}/3：{e}")
                time.sleep(2 * attempt)
        raise RuntimeError(f"取得できませんでした: {url}")


class ListParser(HTMLParser):
    """一覧ページから商品のURL・タイトル・価格・評価・次ページを取り出す。"""

    def __init__(self):
        super().__init__()
        self.items: list[dict] = []
        self.next: str | None = None
        self._in_price = False
        self._in_next = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "article" and "product_pod" in cls:
            self.items.append({})
        elif tag == "p" and cls.startswith("star-rating") and self.items:
            self.items[-1]["rating"] = RATING.get(cls.split()[-1], 0)
        elif tag == "a" and self.items and "title" in a:
            self.items[-1].update(title=a["title"], href=a["href"])
        elif tag == "p" and cls == "price_color":
            self._in_price = True
        elif tag == "li" and cls == "next":
            self._in_next = True
        elif tag == "a" and self._in_next:
            self.next = a.get("href")
            self._in_next = False

    def handle_data(self, data):
        if self._in_price and self.items:
            self.items[-1]["price"] = float(re.sub(r"[^0-9.]", "", data))
            self._in_price = False


def parse_detail(html: str) -> tuple[str, int, str]:
    """詳細ページから分類・在庫数・商品コード（UPC）を取り出す。"""
    crumbs = re.findall(r'<li>\s*<a href="[^"]+">([^<]+)</a>\s*</li>', html)
    category = crumbs[-1].strip() if crumbs else ""
    stock = re.search(r"In stock \((\d+) available\)", html)
    upc = re.search(r"<th>UPC</th>\s*<td>([^<]+)</td>", html)
    return category, int(stock.group(1)) if stock else 0, upc.group(1) if upc else ""


def collect(limit: int, wait: float) -> list[Book]:
    f = Fetcher(wait)
    url = BASE
    books: list[Book] = []
    page = 1
    while url and len(books) < limit:
        log(f"一覧 {page}ページ目を取得：{url}")
        lp = ListParser()
        lp.feed(f.get(url))
        for it in lp.items:
            if len(books) >= limit:
                break
            detail = urllib.parse.urljoin(url, it["href"])
            category, stock, upc = parse_detail(f.get(detail))
            books.append(Book(it["title"], it["price"], it.get("rating", 0), stock, category, upc, detail))
            log(f"  {len(books):>3}/{limit}  £{it['price']:>6.2f}  {it['title'][:42]}")
        url = urllib.parse.urljoin(url, lp.next) if lp.next else None
        page += 1
    return books


def save_xlsx(books: list[Book], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "商品一覧"
    head = ["No.", "商品名", "価格（£）", "評価（5段階）", "在庫数", "分類", "商品コード（UPC）", "URL"]
    ws.append(head)
    for i, b in enumerate(books, 1):
        ws.append([i, b.title, b.price_gbp, b.rating, b.in_stock, b.category, b.upc, b.url])
        ws.cell(row=i + 1, column=8).hyperlink = b.url
        ws.cell(row=i + 1, column=8).font = Font(color="1D4E89", underline="single")
    fill = PatternFill("solid", fgColor="2B3038")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = fill
        c.alignment = Alignment(vertical="center")
    for col, w in zip("ABCDEFGH", [6, 48, 11, 13, 9, 18, 20, 60]):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2, min_col=3, max_col=3):
        for c in row:
            c.number_format = "£#,##0.00"
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:H{len(books) + 1}"

    info = wb.create_sheet("取得条件")
    rows = [
        ("対象サイト", BASE),
        ("サイトの性格", "スクレイピング練習用のサンドボックス。価格・評価はランダムに付けられた値"),
        ("取得日時", f"{dt.datetime.now():%Y-%m-%d %H:%M}"),
        ("取得件数", len(books)),
        ("取得間隔", "1リクエストごとに1.0秒"),
        ("取得しない情報", "ログインが必要な情報・個人情報"),
        ("平均価格（£）", f"=ROUND(AVERAGE('商品一覧'!C2:C{len(books) + 1}),2)"),
        ("在庫数の合計", f"=SUM('商品一覧'!E2:E{len(books) + 1})"),
    ]
    for r in rows:
        info.append(r)
    info.column_dimensions["A"].width = 18
    info.column_dimensions["B"].width = 70
    for c in info["A"]:
        c.font = Font(bold=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="公開商品ページの収集デモ")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--wait", type=float, default=1.0)
    ap.add_argument("--out", default=str(Path(__file__).with_name("output") / "books_100.xlsx"))
    args = ap.parse_args()
    if args.wait < 0.5:
        print("間隔は0.5秒以上にしてください。", file=sys.stderr)
        return 2
    start = time.monotonic()
    log(f"開始：対象 {BASE} ／ 件数 {args.limit} ／ 間隔 {args.wait}秒")
    books = collect(args.limit, args.wait)
    save_xlsx(books, Path(args.out))
    shown = Path(args.out).relative_to(Path(__file__).parent) if Path(args.out).is_relative_to(Path(__file__).parent) else Path(args.out).name
    log(f"完了：{len(books)}件を保存しました → {shown}（{time.monotonic() - start:.0f}秒）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
