# coconala-portfolio（ハル｜よろずサポート屋 自主制作サンプル集）

ココナラ出品用のポートフォリオ一式です。掲載している作品はすべて自主制作のサンプルで、店名・会社名・人名・数値は架空です。

- 索引ページ：`index.html`（GitHub Pages で公開する想定：https://harugreed.github.io/coconala-portfolio/ ・未公開）
- 作品と納品zipの対応表：`manifest.csv`
- Web制作のルール：`WEB_RULES.md`
- 元のプロンプト一式：`prompts/`

## フォルダ構成

```
coconala-portfolio/
  index.html  README.md  manifest.csv  WEB_RULES.md  .nojekyll
  works/
    web/         shop-cafe / shop-ramen / shop-salon / corporate / lp-service / lp-event / renewal
    video/       telop / reels / thumbnail
    writing/     it-article / seo-article / product-review / business-docs
    automation/  scraping / data-convert（csv-to-pdf・excel-invoice・data-cleaning）/ list-sample
    sns/         instagram-set
    design/      presentation / banner / uiux
  assets/        covers（出品カバー4枚）/ diagrams（図解3枚）/ thumbs（索引の縮小画像）
  extracts/      _template / web / video / writing / automation（案件別の取り出しセット）
  deliveries/    作品ごとの納品zip（公開しない）
  video-src/     動画の制作環境（Remotion・素材・合成音声。公開しない）
```

## 公開するときの手順（未実施）

1. GitHub に public のリポジトリ `coconala-portfolio` を作る
2. `deliveries/`・`video-src/`・`.tools/`・`.claude/` を除いて push する（`.gitignore` に書いてあります）
3. リポジトリの Settings → Pages で、ブランチ `main`・フォルダ `/ (root)` を選ぶ
4. 数分後に https://harugreed.github.io/coconala-portfolio/ で表示を確認する

動画ファイルは最大で約22MB（telop-main.mp4）です。GitHub のブラウザからのアップロードの上限（25MB）より小さく収めています。

## 案件に応募するとき

`manifest.csv` で案件のカテゴリの行を見て、`extracts/<カテゴリ>/README.md` の URL一覧と紹介文（3行）を使います。

## 素材のライセンス

- 写真：Unsplash License（各作品の credits.md に画像URL）
- 素材映像・音楽・効果音：Mixkit のライセンス（works/video/telop/credits.md）
- 書体：Google Fonts（SIL Open Font License）
- ナレーション：Irodori-TTS（MIT License）でローカル合成
