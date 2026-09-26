"""
織部サイトの計測(js/site-tracking.js)で送っている項目を、GA4 のカスタムディメンション(イベント スコープ)として登録する。
登録済みの項目は飛ばすので、何度実行しても同じ結果になる。

必要な権限: サービスアカウント ga4-mcp@sustained-truck-492415-f0.iam.gserviceaccount.com に
GA4 プロパティ 384244847 の「編集者」権限(閲覧者だと 403 になる)。

実行: python scripts/register_ga4_dimensions.py
"""
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

SA = r"C:\Users\syuuy\.config\ga4-sa-key.json"
PROPERTY = "384244847"
DIMENSIONS = [
    # (パラメータ名, 表示名, 説明)
    ("cta_location", "CTA location", "予約ボタンなどが押された場所（header / home_hero / mobile_bottom_bar / footer など）"),
    ("site_language", "Site language", "イベントが起きたページの言語（en / zh / ja）"),
    ("to_language", "To language", "言語切替の切替先（en / zh / ja）"),
    ("course", "Menu course", "メニューページで選んだコース（lunch / dinner）"),
    ("platform", "Social platform", "SNS・外部リンクの行き先（instagram / facebook / tiktok / google）"),
    ("method", "Reserve method", "予約ボタンの種類（tablecheck / whatsapp）"),
]


def main() -> None:
    creds = service_account.Credentials.from_service_account_file(
        SA, scopes=["https://www.googleapis.com/auth/analytics.edit"])
    s = AuthorizedSession(creds)
    base = f"https://analyticsadmin.googleapis.com/v1beta/properties/{PROPERTY}/customDimensions"
    have = {d["parameterName"] for d in s.get(base).json().get("customDimensions", [])
            if d.get("scope") == "EVENT"}
    for param, name, desc in DIMENSIONS:
        if param in have:
            print(f"{param}: 登録済み")
            continue
        r = s.post(base, json={"parameterName": param, "displayName": name,
                               "description": desc[:150], "scope": "EVENT"})
        print(f"{param}: {'登録しました' if r.ok else f'失敗 {r.status_code} {r.text[:120]}'}")


if __name__ == "__main__":
    main()
