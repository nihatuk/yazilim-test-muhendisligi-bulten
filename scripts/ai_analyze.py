import feedparser
import json
import os
import time
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

FEEDS = [
    {"url": "https://www.ministryoftesting.com/feed", "source": "Ministry of Testing"},
    {"url": "https://feeds.feedburner.com/TestingCurator", "source": "Testing Curator"},
    {"url": "https://www.stickyminds.com/rss.xml", "source": "StickyMinds"},
    {"url": "https://feeds.feedburner.com/SoftwareTestingHelp", "source": "Software Testing Help"},
    {"url": "https://www.ontestautomation.com/feed/", "source": "On Test Automation"},
]

NIHAT_UK_URL = "https://nihatuk.com/feed/"

def fetch_feeds():
    items = []
    for feed_info in FEEDS:
        print(f"📡 Çekiliyor: {feed_info['source']}")
        try:
            feed = feedparser.parse(feed_info['url'])
            for entry in feed.entries[:4]:
                summary = entry.get('summary', '')
                if len(summary) > 300:
                    summary = summary[:300] + "..."
                items.append({
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "summary": summary,
                    "date": entry.get('published', str(datetime.now())),
                    "source": feed_info['source'],
                    "ai_comment": ""
                })
        except Exception as e:
            print(f"⚠️ Hata ({feed_info['source']}): {e}")
    return items

def fetch_nihat_uk():
    print("📡 Nihat Ük yazıları çekiliyor...")
    try:
        feed = feedparser.parse(NIHAT_UK_URL)
        entries = feed.entries[:3]
        texts = []
        for entry in entries:
            summary = entry.get('summary', '')
            if len(summary) > 500:
                summary = summary[:500] + "..."
            texts.append(f"Başlık: {entry.get('title', '')}\n{summary}")
        return "\n\n---\n\n".join(texts)
    except Exception as e:
        print(f"⚠️ Nihat Ük hatası: {e}")
        return ""

def analyze_with_ai(item):
    try:
        prompt = (
            f"Aşağıdaki yazılım test haberi hakkında 2-3 cümlelik Türkçe yorum yaz. "
            f"Yazılım test mühendisleri için neden önemli olduğunu belirt.\n\n"
            f"Başlık: {item['title']}\n"
            f"Özet: {item['summary']}"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ AI yorum hatası: {e}")
        return ""

def analyze_nihat_uk(content):
    if not content:
        return ""
    try:
        prompt = (
            f"Aşağıdaki Nihat Ük'ün yazılım test yazılarını özetle ve "
            f"yazılım test mühendisleri için 3-4 cümlelik Türkçe bir köşe yazısı oluştur:\n\n"
            f"{content}"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Nihat yorumu hatası: {e}")
        return ""

def save_bulletin_as_markdown(data):
    tarih = datetime.now().strftime("%Y-%m-%d")
    dosya = f"data/{tarih}.md"

    lines = []
    lines.append(f"# 📰 Yazılım Test Mühendisliği Bülteni — {tarih}\n")
    lines.append(f"> 🤖 Otomatik oluşturuldu | {len(data['items'])} haber\n")
    lines.append("---\n")

    if data.get('nihat_yorum'):
        lines.append("## 🎙️ Nihat Ük'ün Köşesi\n")
        lines.append(data['nihat_yorum'] + "\n")
        lines.append("---\n")

    sources = {}
    for item in data['items']:
        src = item['source']
        if src not in sources:
            sources[src] = []
        sources[src].append(item)

    lines.append("## 📡 Bu Haftanın Haberleri\n")

    for source_name, articles in sources.items():
        lines.append(f"### {source_name}\n")
        for article in articles:
            lines.append(f"#### [{article['title']}]({article['link']})")
            lines.append(f"- 📅 {article['date'][:10]}")
            lines.append(f"- 📝 {article['summary']}")
            if article.get('ai_comment'):
                lines.append(f"- 🤖 **AI Yorumu:** {article['ai_comment']}")
            lines.append("")

    with open(dosya, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"✅ Bülten kaydedildi: {dosya}")
    return dosya

def run():
    print("🚀 Bülten hazırlanıyor...")

    # Haberleri çek
    items = fetch_feeds()
    print(f"✅ {len(items)} haber bulundu")

    # Nihat Ük içeriğini çek
    nihat_content = fetch_nihat_uk()

    # Her haberi AI ile analiz et
    for i, item in enumerate(items):
        print(f"🤖 {i+1}/{len(items)}: {item['title'][:50]}...")
        item['ai_comment'] = analyze_with_ai(item)
        time.sleep(1)

    # Nihat Ük köşesini oluştur
    print("✍️ Nihat Ük'ün yorumu yazılıyor...")
    nihat_yorum = analyze_nihat_uk(nihat_content)

    # Veriyi kaydet
    data = {
        "fetched_at": str(datetime.now()),
        "items": items,
        "nihat_yorum": nihat_yorum
    }

    os.makedirs("data", exist_ok=True)

    with open("data/weekly_news.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Analiz tamamlandı ve kaydedildi!")

    # Bülteni Markdown olarak kaydet
    save_bulletin_as_markdown(data)

if __name__ == "__main__":
    run()
