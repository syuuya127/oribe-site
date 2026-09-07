# Sushi Oribe KL 公式サイト

https://oribe-sushi.com.my の静的サイトです。2026年9月にWebflowから移行しました。
公開中だった Webflow サイト(2026年8月3日公開版)をそのまま取り込んだもので、内容は同一です。
ビルド工程はなく、このフォルダの中身をそのままホスティングに置けば動きます。

## 構成

| パス | 内容 |
|---|---|
| `index.html` ほか 7 ページ | 各ページ本体。URL は `/menu` のように拡張子なし |
| `css/` | サイトのスタイルシート(Webflow 生成) |
| `js/` | jQuery と Webflow のランタイム(スライダー・ライトボックスなど) |
| `images/` | 画像。`-p-500` などの接尾辞はレスポンシブ用のサイズ違い |
| `404.html` | 404 ページ |
| `sitemap.xml` / `robots.txt` | 検索エンジン向け |
| `_redirects` / `_headers` | Cloudflare Pages 用(www → 非 www、キャッシュ) |
| `.htaccess` | cPanel(Apache)に置く場合の同等設定 |
| `serve.py` | ローカル確認用サーバー |
| `scripts/mirror_live_site.py` | 移行時に公開サイトを取り込んだスクリプト(記録用) |

ページ: `/` `/menu` `/our-chef` `/gallery` `/about` `/sake-pairing` `/omakase`

Webflow の編集画面には未公開の下書き(Private Events ページ、ナビの変更、Omakase ページの写真差し替え)が残っていました。
移行時には公開版に合わせたため、それらは含まれていません。必要になったら HTML を追加してください。

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

## 計測タグ

`<head>` に以下が入っています。変更する場合は 7 ページすべてを直してください。

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
