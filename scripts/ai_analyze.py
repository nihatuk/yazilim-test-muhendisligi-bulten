import feedparser
import yaml
import json
import os
import re
import time
from datetime import datetime, timedelta
#from openai import OpenAI

#client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
client = genai.GenerativeModel("gemini-1.5-flash")

NIHAT_UK_URL = "https://yazilimtestmuhendisligi.com/feed/"

# ─────────────────────────────────────────
# 1. KAYNAK YÜKLEME
# ─────────────────────────────────────────

def load_sources():
    """sources.yaml dosyasını oku"""
    with open('sources.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ─────────────────────────────────────────
# 2. HABER ÇEKME
# ─────────────────────────────────────────

def is_recent(entry, days=7):
    """Haberin son 7 günde olup olmadığını kontrol et"""
    try:
        published = datetime(*entry.published_parsed[:6])
        return published > datetime.now() - timedelta(days=days)
    except:
        return True  # Tarih yoksa dahil et

def clean_text(text, max_chars=300):
    """HTML taglarını temizle ve kısalt"""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('\n', ' ').strip()
    return clean[:max_chars] + "..." if len(clean) > max_chars else clean

def fetch_feeds():
    """sources.yaml'daki RSS kaynaklarından haber çek"""
    sources = load_sources()
    items = []

    print("🔍 Haberler toplanıyor...\n")

    for feed_info in sources['rss_feeds']:
        print(f"📡 {feed_info['name']} okunuyor...")
        try:
            feed = feedparser.parse(feed_info['url'])
            count = 0

            for entry in feed.entries:
                if not is_recent(entry):
                    continue

                summary = ""
                if hasattr(entry, 'summary'):
                    summary = clean_text(entry.summary)
                elif hasattr(entry, 'description'):
                    summary = clean_text(entry.description)

                items.append({
                    "title": entry.get('title', 'Başlık yok'),
                    "link": entry.get('link', ''),
                    "summary": summary,
                    "date": entry.get('published', datetime.now().isoformat()),
                    "source": feed_info['name'],
                    "ai_comment": ""
                })
                count += 1

                if count >= 5:  # Her kaynaktan max 5 haber
                    break

            print(f"   ✅ {count} haber bulundu")

        except Exception as e:
            print(f"   ❌ Hata ({feed_info['name']}): {e}")

    return items

def fetch_nihat_uk():
    """Nihat Ük blogundan son yazıları çek"""
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

# ─────────────────────────────────────────
# 3. AI ANALİZ
# ─────────────────────────────────────────

def analyze_with_ai(item):
    """Tek bir haber için AI yorumu üret"""
    try:
        prompt = (
            f"Aşağıdaki yazılım test haberi hakkında 2-3 cümlelik Türkçe yorum yaz. "
            f"Yazılım test mühendisleri için neden önemli olduğunu belirt.\n\n"
            f"Başlık: {item['title']}\n"
            f"Özet: {item['summary']}"
        )
        (#response = client.chat.completions.create(
            #model="gpt-4o-mini",  # gpt-3.5-turbo yerine daha iyi ve ucuz!
            #messages=[{"role": "user", "content": prompt}],
            #max_tokens=150
        response = client.generate_content(prompt)
        )
        #return response.choices[0].message.content.strip()
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI yorum hatası: {e}")
        return ""

def analyze_nihat_uk(content):
    """Nihat Ük yazılarından köşe yazısı oluştur"""
    if not content:
        return ""
    try:
        prompt = (
            f"Aşağıdaki Nihat Ük'ün yazılım test yazılarını özetle ve "
            f"yazılım test mühendisleri için 3-4 cümlelik Türkçe bir köşe yazısı oluştur:\n\n"
            f"{content}"
        )
        (#response = client.chat.completions.create(
            #model="gpt-4o-mini",
            #messages=[{"role": "user", "content": prompt}],
            #max_tokens=250
            response = client.generate_content(prompt)
        )
        return response.text.strip()
        #return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Nihat yorumu hatası: {e}")
        return ""

# ─────────────────────────────────────────
# 4. BÜLTEN KAYDETME
# ─────────────────────────────────────────

def save_bulletin_as_markdown(data):
    """Bülteni Markdown formatında kaydet"""
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

    # Haberleri kaynağa göre grupla
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

    os.makedirs('data', exist_ok=True)
    with open(dosya, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"✅ Bülten kaydedildi: {dosya}")
    return dosya

# ─────────────────────────────────────────
# 5. ANA FONKSİYON
# ─────────────────────────────────────────

def run():
    print("🚀 Bülten hazırlanıyor...")

    # Haberleri çek
    items = fetch_feeds()
    print(f"\n✅ Toplam {len(items)} haber bulundu")

    # Nihat Ük içeriğini çek
    nihat_content = fetch_nihat_uk()

    # Her haberi AI ile analiz et
    print("\n🤖 AI yorumları yazılıyor...")
    for i, item in enumerate(items):
        print(f"   {i+1}/{len(items)}: {item['title'][:50]}...")
        item['ai_comment'] = analyze_with_ai(item)
        time.sleep(1)  # Rate limit için bekle

    # Nihat Ük köşesini oluştur
    print("\n✍️ Nihat Ük'ün yorumu yazılıyor...")
    nihat_yorum = analyze_nihat_uk(nihat_content)

    # JSON olarak kaydet
    data = {
        "fetched_at": datetime.now().isoformat(),
        "total": len(items),
        "items": items,
        "nihat_yorum": nihat_yorum
    }

    os.makedirs("data", exist_ok=True)
    with open("data/weekly_news.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ JSON kaydedildi: data/weekly_news.json")

    # Markdown bülten oluştur
    save_bulletin_as_markdown(data)

    print("\n🎉 Bülten hazır!")

if __name__ == "__main__":
    run()
