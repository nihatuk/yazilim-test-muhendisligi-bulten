import json
import os
import requests
import base64
from datetime import datetime

WP_URL = os.environ.get("WP_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

def get_auth_header():
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {token}"}

def build_html_content(data):
    items = data['items']
    nihat_yorum = data.get('nihat_yorum', '')
    fetched_at = data['fetched_at'][:10]

    sources = {}
    for item in items:
        src = item['source']
        if src not in sources:
            sources[src] = []
        sources[src].append(item)

    nihat_html = ""
    if nihat_yorum:
        nihat_html = (
            '<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);'
            'color:white;border-radius:12px;padding:30px;margin-bottom:40px;">'
            '<h2 style="color:#ffd700;margin-bottom:16px;">Nihat Uk Kosesi</h2>'
            '<div style="line-height:1.8;font-size:1.05em;opacity:0.95;">'
            + nihat_yorum.replace('\n', '<br>') +
            '</div></div>'
        )

    news_html = ""
    for source_name, articles in sources.items():
        articles_html = ""
        for article in articles:
            ai_comment = article.get('ai_comment', '')
            ai_block = ""
            if ai_comment:
                ai_block = (
                    '<div style="background:#f0f7ff;border-left:3px solid #2563eb;'
                    'padding:10px 14px;margin-top:8px;border-radius:4px;'
                    'font-size:0.9em;color:#1e40af;">'
                    '🤖 <em>' + ai_comment + '</em></div>'
                )

            articles_html += (
                '<div style="margin-bottom:20px;padding-bottom:20px;'
                'border-bottom:1px solid #f0f4f8;">'
                '<a href="' + article['link'] + '" target="_blank" '
                'style="font-weight:600;color:#2563eb;font-size:1em;">'
                + article['title'] + '</a>'
                '<p style="color:#666;font-size:0.9em;margin-top:6px;line-height:1.5;">'
                + article['summary'] + '</p>'
                + ai_block +
                '<span style="font-size:0.8em;color:#999;">📅 '
                + article['date'][:10] + '</span></div>'
            )

        news_html += (
            '<div style="background:white;border-radius:12px;padding:24px;'
            'margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">'
            '<h3 style="color:#1a1a2e;border-bottom:2px solid #e2e8f0;'
            'padding-bottom:10px;margin-bottom:16px;">📡 '
            + source_name + '</h3>'
            + articles_html + '</div>'
        )

    full_html = (
        '<div style="font-family:Segoe UI,sans-serif;max-width:860px;margin:0 auto;">'
        '<div style="background:#f0f4f8;border-radius:8px;padding:16px;'
        'margin-bottom:30px;text-align:center;color:#666;">'
        '🗓️ <strong>' + fetched_at + '</strong> tarihli haftalik bulten — '
        '<strong>' + str(len(items)) + '</strong> haber derlendi</div>'
        + nihat_html +
        '<h2 style="color:#1a1a2e;margin-bottom:20px;">📰 Bu Haftanin Haberleri</h2>'
        + news_html +
        '<div style="text-align:center;padding:20px;color:#999;font-size:0.85em;">'
        '🤖 Bu bulten otomatik olarak yapay zeka destekli sistem tarafindan hazirlanmistir.'
        '</div></div>'
    )

    return full_html

def test_auth():
    print("=== AUTH TEST ===")
    print("WP_URL:", WP_URL)
    print("WP_USERNAME:", WP_USERNAME)
    print("WP_APP_PASSWORD uzunlugu:", len(WP_APP_PASSWORD) if WP_APP_PASSWORD else "YOK!")

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    test = requests.get(
        WP_URL.rstrip("/") + "/wp-json/wp/v2/users/me",
        headers=headers
    )
    print("Auth Status:", test.status_code)
    print("Auth Response:", test.text[:400])
    print("=================")
    return test.status_code == 200

def publish_to_wordpress(html_content):
    tarih = datetime.now().strftime("%d %B %Y")
    title = "Yazilim Test Muhendisligi Bulteni - " + tarih

    post_data = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "slug": "bulten-" + datetime.now().strftime("%Y-%m-%d")
    }

    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    print("Post verisi gonderiliyor...")
    response = requests.post(
        WP_URL.rstrip("/") + "/wp-json/wp/v2/posts",
        json=post_data,
        headers=headers,
        timeout=30
    )

    print("Status Code:", response.status_code)
    print("Response:", response.text[:500])

    if response.status_code == 201:
        post = response.json()
        print("WordPress'e yayinlandi!")
        print("URL: " + post.get('link', ''))
        return post.get('link', '')
    else:
        print("HATA: Post olusturulamadi!")
        return None

def test_auth():
    print("=== AUTH TEST ===")
    print("WP_URL:", WP_URL)
    print("WP_USERNAME:", WP_USERNAME)
    print("WP_APP_PASSWORD uzunlugu:", len(WP_APP_PASSWORD) if WP_APP_PASSWORD else "YOK!")

    # Gizli karakter kontrolü
    if WP_APP_PASSWORD:
        print("ilk 3 karakter:", repr(WP_APP_PASSWORD[:3]))
        print("son 3 karakter:", repr(WP_APP_PASSWORD[-3:]))
        print("Bosluk var mi?:", " " in WP_APP_PASSWORD)
        print("\\n var mi?:", "\n" in WP_APP_PASSWORD)
        print("\\r var mi?:", "\r" in WP_APP_PASSWORD)
        print("\\t var mi?:", "\t" in WP_APP_PASSWORD)

    # Base64 token
    import base64
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    print("Credentials repr:", repr(credentials[:10]), "...")
    print("Token (ilk 20):", token[:20])

    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

    url = WP_URL.rstrip("/") + "/wp-json/wp/v2/users/me"
    print("İstek URL:", url)

    test = requests.get(url, headers=headers)
    print("Auth Status:", test.status_code)
    print("Auth Response:", test.text[:400])
    print("Gonderilen Header:", test.request.headers.get("Authorization", "YOK")[:40])
    print("=================")
    return test.status_code == 200

def run():
    print("=== SCRIPT BASLADI ===")

    auth_ok = test_auth()
    if not auth_ok:
        print("AUTH BASARISIZ! Devam edilmiyor.")
        return

    print("Auth basarili, devam ediliyor...")

    with open('data/weekly_news.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("HTML icerik olusturuluyor...")
    html_content = build_html_content(data)

    print("WordPress'e gonderiliyor...")
    publish_to_wordpress(html_content)

if __name__ == "__main__":
    run()
