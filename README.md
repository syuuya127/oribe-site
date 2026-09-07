# Sushi Oribe KL 公式サイト

https://oribe-sushi.com.my の静的サイトです。2026年9月にWebflowから移行しました。
ビルド工程はなく、このフォルダの中身をそのままホスティングに置けば動きます。

## 構成

| パス | 内容 |
|---|---|
| `index.html` ほか 8 ページ | 各ページ本体。URL は `/menu` のように拡張子なし |
| `css/` | Webflow から書き出したスタイル(`new-sushi-oribe-b0dca6.webflow.css` がサイト固有) |
| `js/` | jQuery と Webflow のランタイム(スライダー・ライトボックス・背景動画) |
| `images/` | 画像。`-p-500` などの接尾辞はレスポンシブ用のサイズ違い |
| `videos/` | Private Events ページの背景動画(音声なし H.264) |
| `404.html` | 404 ページ |
| `sitemap.xml` / `robots.txt` | 検索エンジン向け |
| `_redirects` / `_headers` | Cloudflare Pages 用(www → 非 www、キャッシュ) |
| `.htaccess` | cPanel(Apache)に置く場合の同等設定 |
| `serve.py` | ローカル確認用サーバー |
| `scripts/migrate_from_webflow.py` | 移行時に使った変換スクリプト(記録用) |

ページ: `/` `/menu` `/our-chef` `/gallery` `/about` `/sake-pairing` `/omakase` `/private-events`

## ローカルで確認する

```bash
python serve.py
```

http://localhost:8080 で本番と同じ URL 構造で表示されます。

## 更新のしかた

1. 該当する `*.html` を編集する(メニュー画像の差し替えなら `menu.html` と `images/`)
2. 新しい画像は `images/` に入れ、HTML の `src` と `srcset` を書き換える
3. `python serve.py` で表示を確認する
4. `git commit` して `git push` すると Cloudflare Pages が自動で公開する

Claude Code に「menu.html の春メニュー画像を images/xxx.jpg に差し替えて」のように頼めば 1〜3 をまとめて行えます。

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

本番は Cloudflare Pages(無料プラン)。GitHub リポジトリと連携し、`main` ブランチへの push で自動デプロイ。
ビルドコマンドなし、出力ディレクトリは `/`(ルート)。

cPanel に置く場合は `.htaccess` がそのまま使えます。
