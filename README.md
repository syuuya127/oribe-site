# Sushi Oribe KL 公式サイト

https://oribe-sushi.com.my の静的サイトです。2026年9月にWebflowから移行しました。
公開中だった Webflow サイト(2026年8月3日公開版)をそのまま取り込んだもので、内容は同一です。
ビルド工程はなく、このフォルダの中身をそのままホスティングに置けば動きます。

## 構成

| パス | 内容 |
|---|---|
| `index.html` ほか 8 ページ | 各ページ本体。URL は `/menu` のように拡張子なし |
| `css/` | サイトのスタイルシート(Webflow 生成) |
| `js/` | jQuery と Webflow のランタイム(スライダー・ライトボックスなど) |
| `images/` | 画像。`-p-500` などの接尾辞はレスポンシブ用のサイズ違い |
| `videos/` | Private Events ページの背景動画(音声なし H.264) |
| `css/site-overrides.css` | 移行後に追加したスタイル調整(Webflow 生成の CSS は直接触らない) |
| `404.html` | 404 ページ |
| `sitemap.xml` / `robots.txt` | 検索エンジン向け |
| `_redirects` / `_headers` | Cloudflare Pages 用(www → 非 www、キャッシュ) |
| `.htaccess` | cPanel(Apache)に置く場合の同等設定 |
| `serve.py` | ローカル確認用サーバー |
| `scripts/mirror_live_site.py` | 移行時に公開サイトを取り込んだスクリプト(記録用) |
| `zh/` `ja/` | 中国語(簡体字)・日本語のページ。**直接編集しない**(下記スクリプトで生成) |
| `i18n/zh.json` `i18n/ja.json` | 翻訳辞書(英語の文 → 訳文) |
| `scripts/build_i18n.py` | 英語ページと翻訳辞書から `zh/` `ja/` を生成し、言語切替と hreflang を入れる |

ページ: `/` `/menu` `/our-chef` `/gallery` `/about` `/sake-pairing` `/omakase` `/private-events`

中国語版は `/zh/...`、日本語版は `/ja/...`(例: `/zh/menu`, `/ja/omakase`)。

Private Events ページは Webflow の未公開下書きから 2026年9月に公開しました(スタイルは下書き時の `css/new-sushi-oribe-b0dca6.webflow.css` を使用)。
同じ下書きにあった Omakase ページの写真差し替えは未反映です。

## ローカルで確認する

```bash
python serve.py
```

http://localhost:8080 で本番と同じ URL 構造で表示されます。

## 更新のしかた

1. 該当する `*.html` を編集する(メニュー画像の差し替えなら `menu.html` と `images/`)
2. 新しい画像は `images/` に入れ、HTML の `src` と `srcset` を書き換える
3. `python serve.py` で表示を確認する
4. `git commit` して `git push` し、cPanel の Git Version Control で「Deploy HEAD Commit」を押す

Claude Code に「menu.html の春メニュー画像を images/xxx.jpg に差し替えて」のように頼めば 1〜3 をまとめて行えます。

## 多言語(中国語・日本語)の更新

英語の `*.html` が原本です。`zh/` `ja/` は生成物なので直接編集しないでください。

1. 英語ページを編集する
2. 未翻訳の文を確認する

```bash
python scripts/build_i18n.py check
```

3. 表示された文の訳を `i18n/zh.json` と `i18n/ja.json` に追加する(Claude Code に「未翻訳を訳して」と頼めば済みます)
4. 中国語・日本語ページを作り直す

```bash
python scripts/build_i18n.py build
```

メニュー画像は英語のまま全言語で共通です。画像だけの差し替えなら 2〜4 は不要です(ただし build は実行してください。画像のパスが各言語に反映されます)。

以下は意図的に英語のまま残しています: お客様のレビュー、人名、住所、日本酒の銘柄名、価格。
About ページの英日併記の段落は、日本語版では英語のまま(隣に日本語の段落があるため)、中国語版では英語部分だけを中国語にしています。
WhatsApp ボタンの定型文は、スタッフが読めるよう全言語とも英語です。

## 計測タグ

`<head>` に以下が入っています。変更する場合は 8 ページすべてを直してください。

- GA4: `G-VR69HZB6WG`
- Google Tag Manager: `GTM-K32VKRM`
- Meta Pixel: `3545309522196977`
- 予約ボタンのクリック計測(`reserve_click` イベント)は各ページ末尾のインラインスクリプト

## 外部サービス

- 予約: TableCheck(リンクのみ)
- WhatsApp 予約ボタン: `wa.me` リンク
- ツナ注文フォーム: `jemy26tunaorderform.vercel.app`(別途運用)
- フォント: Google Fonts(Varela / EB Garamond / Lateef)

## ホスティング

本番は mschosting の cPanel(既存契約)。cPanel の **Git Version Control** でこのリポジトリを clone してあり、
「Pull or Deploy」→「Deploy HEAD Commit」を押すと `.cpanel.yml` の手順で Document Root に配置されます。
`.htaccess` が拡張子なし URL・www 統一・404 ページを担当します。

Cloudflare Pages に移す場合は `_redirects` / `_headers` がそのまま使えます(ドメインの DNS を Cloudflare に移す必要あり)。
