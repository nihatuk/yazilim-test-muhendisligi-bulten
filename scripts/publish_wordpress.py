import json
import os
import requests
from datetime import datetime

WP_URL = os.environ["WP_URL"]
WP_USERNAME = os.environ["WP_USERNAME"]
WP_PASSWORD = os.environ["WP_PASSWORD"]


def get_jwt_token():
    response = requests.post(
        f"{WP_URL.rstrip('/')}/wp-json/jwt-auth/v1/token",
        json={
            "username": WP_USERNAME,
            "password": WP_PASSWORD
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(
            f"JWT Login Failed ({response.status_code})\n{response.text}"
        )

    return response.json()["token"]


def build_html_content(data):

    items = data["items"]
    nihat_yorum = data.get("nihat_yorum", "")
    fetched_at = data["fetched_at"][:10]

    grouped = {}

    for item in items:
        grouped.setdefault(item["source"], []).append(item)

    html = f"""
<div style="font-family:Segoe UI,sans-serif;max-width:900px;margin:auto">

<div style="background:#f5f5f5;padding:15px;border-radius:10px;margin-bottom:30px">
<b>{fetched_at}</b><br>
Toplam <b>{len(items)}</b> haber derlendi.
</div>
"""

    if nihat_yorum:

        html += f"""
<div style="background:#16213e;color:white;padding:25px;border-radius:12px;margin-bottom:40px">
<h2>Nihat ÜK Köşesi</h2>

{nihat_yorum.replace(chr(10),"<br>")}

</div>
"""

    for source, articles in grouped.items():

        html += f"<h2>{source}</h2>"

        for article in articles:

            html += f"""
<div style="margin-bottom:30px">

<h3>
<a href="{article['link']}">
{article['title']}
</a>
</h3>

<p>
{article['summary']}
</p>
"""

            if article.get("ai_comment"):

                html += f"""
<div style="background:#eef6ff;padding:12px;border-left:4px solid #2563eb">

🤖 {article["ai_comment"]}

</div>
"""

            html += "</div>"

    html += """

<hr>

<p style="color:gray;font-size:13px">

Bu bülten otomatik olarak hazırlanmıştır.

</p>

</div>

"""

    return html


def publish_to_wordpress(html):

    token = get_jwt_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    today = datetime.now()

    payload = {

        "title": f"Yazılım Test Mühendisliği Bülteni - {today.strftime('%d %B %Y')}",

        "content": html,

        "status": "publish",

        "slug": f"bulten-{today.strftime('%Y-%m-%d')}"
    }

    response = requests.post(
        f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts",
        json=payload,
        headers=headers,
        timeout=30
    )

    print(response.status_code)
    print(response.text)

    if response.status_code != 201:
        raise Exception("WordPress yazısı oluşturulamadı.")

    print("Yayınlandı.")
    print(response.json()["link"])

    return response.json()["link"]


def run():

    print("Veriler okunuyor...")

    with open(
        "data/weekly_news.json",
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    print("HTML oluşturuluyor...")

    html = build_html_content(data)

    print("WordPress'e gönderiliyor...")

    publish_to_wordpress(html)

    print("Tamamlandı.")


if __name__ == "__main__":
    run()
