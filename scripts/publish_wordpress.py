import json
import os
from datetime import datetime

import requests

# ===========================
# Environment Variables
# ===========================

WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

print("WP_URL =", repr(WP_URL))

print("========== WORDPRESS ENV ==========")
print("WP_URL       :", WP_URL if WP_URL else "YOK")
print("WP_USERNAME  :", WP_USERNAME if WP_USERNAME else "YOK")
print("WP_PASSWORD  :", "SET" if WP_PASSWORD else "YOK")
print("===================================")

if not WP_URL:
    raise RuntimeError("WP_URL bulunamadı.")

if not WP_USERNAME:
    raise RuntimeError("WP_USERNAME bulunamadı.")

if not WP_PASSWORD:
    raise RuntimeError("WP_PASSWORD bulunamadı.")


# ===========================
# JWT LOGIN
# ===========================

def get_jwt_token():

    url = f"{WP_URL.rstrip('/')}/wp-json/jwt-auth/v1/token"

    print(f"JWT Login -> {url}")

    response = requests.post(
        url,
        json={
            "username": WP_USERNAME,
            "password": WP_PASSWORD
        },
        timeout=30
    )

    print("JWT Status :", response.status_code)

    if response.status_code != 200:
        print(response.text)
        raise Exception("JWT giriş başarısız.")

    token = response.json()["token"]

    print("JWT alındı.")

    return token


# ===========================
# HTML
# ===========================

def build_html_content(data):

    items = data["items"]
    fetched_at = data["fetched_at"][:10]
    nihat_yorum = data.get("nihat_yorum", "")

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
<div style="background:#eef6ff;
padding:12px;
border-left:4px solid #2563eb;
margin-top:10px;">

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


# ===========================
# PUBLISH
# ===========================

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

    print("WordPress REST API'ye gönderiliyor...")

    response = requests.post(
        f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts",
        json=payload,
        headers=headers,
        timeout=30
    )

    print("POST Status :", response.status_code)
    print(response.text)

    if response.status_code != 201:
        raise Exception("WordPress yazısı oluşturulamadı.")

    print("")
    print("Yayın başarılı.")
    print(response.json()["link"])


# ===========================
# MAIN
# ===========================

def run():

    print("weekly_news.json okunuyor...")

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
