import json
import os
import re
import time
import feedparser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

NIHAT_UK_URL = "https://yazilimtestmuhendisligi.com/feed/"

# ─────────────────────────────────────────
# GEMINI ÇAĞRISI (timeout ile)
# ─────────────────────────────────────────

def call_gemini(prompt, timeout=25):
    def _call():
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )
        return response.text.strip()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeout:
            print("   ⏰ Timeout! API yanıt vermedi.")
            return ""

# ─────────────────────────────────────────
# NİHAT ÜK KÖŞESİ
# ─────────────────────────────────────────

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

def analyze_nihat_uk(content):
    if not content:
        return ""
    try:
        prompt = (
            f"Aşağıdaki Nihat Ük'ün yazılım test yazılarını özetle ve "
            f"yazılım test mühendisleri için 3-4 cümlelik Türkçe bir köşe yazısı oluştur:\n\n"
            f"{content}"
        )
        return call_gemini(prompt)
    except Exception as e:
        print(f"⚠️ Nihat yorumu hatası: {e}")
        return ""

# ─────────────────────────────────────────
# HABER AI YORUMU
# ─────────────────────────────────────────

def analyze_with_ai(item):
    try:
        lang_note = "Haber İngilizce olsa da yorumu Türkçe yaz." if item.get('lang') == 'en' else ""
        prompt = (
            f"Aşağıdaki yazılım test haberi hakkında 2-3 cümlelik Türkçe yorum yaz. "
            f"Yazılım test mühendisleri için neden önemli olduğunu belirt. {lang_note}\n\n"
            f"Başlık: {item['title']}\n"
            f"Özet: {item['summary']}"
        )
        return call_gemini(prompt)
    except Exception as e:
        print(f"⚠️ AI yorum hatası: {e}")
        return ""

# ─────────────────────────────────────────
# MARKDOWN KAYDET
# ─────────────────────────────────────────

def save_bulletin_as_markdown(data):
    tarih = datetime.now().strftime("%Y-%m-%d")
    dosya = f"data/{tarih}.md"

    lines = []
    lines.append(f"# 📰 Yazılım Test Mühendisliği Bülteni — {tarih}\n")
    lines.append(f"> 🤖 Otomatik oluşturuldu | {len(data['items'])} yeni haber\n")
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
            flag = "🇹🇷" if article.get('lang') == 'tr' else "🌍"
            lines.append(f"#### {flag} [{article['title']}]({article['link']})")
            lines.append(f"- 📅 {article['date'][:10]}")
            lines.append(f"- 📝 {article['summary']}")
            if article.get('ai_comment'):
                lines.append(f"- 🤖 **AI Yorumu:** {article['ai_comment']}")
            lines.append("")

    os.makedirs('data', exist_ok=True)
    with open(dosya, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"✅ Markdown kaydedildi: {dosya}")
    return dosya

# ─────────────────────────────────────────
# ANA FONKSİYON
# ─────────────────────────────────────────

def run():
    print("🚀 AI Analiz başlıyor...\n")

    # fetch_news.py'nin kaydettiği JSON'u oku
    with open('data/weekly_news.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']

    if not items:
        print("⚠️ Haber bulunamadı, analiz yapılmıyor.")
        return

    print(f"📰 {len(items)} haber analiz edilecek\n")

    # Nihat Ük köşesi
    nihat_content = fetch_nihat_uk()

    # AI yorumları
    print("\n🤖 AI yorumları yazılıyor...")
    for i, item in enumerate(items):
        print(f"   {i+1}/{len(items)}: {item['title'][:50]}...")
        item['ai_comment'] = analyze_with_ai(item)
        time.sleep(1)  # Rate limit

    # Nihat Ük yorumu
    print("\n✍️ Nihat Ük köşe yazısı oluşturuluyor...")
    nihat_yorum = analyze_nihat_uk(nihat_content)

    # Güncel veriyi hazırla
    data['items'] = items
    data['nihat_yorum'] = nihat_yorum

    # JSON güncelle (publish_wordpress.py okuyacak)
    tarih = datetime.now().strftime("%Y-%m-%d")
    json_dosya = f"data/{tarih}.json"

    with open(json_dosya, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # weekly_news.json'u da güncelle (publish_wordpress.py bunu okuyor)
    with open('data/weekly_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON kaydedildi: {json_dosya}")

    # Markdown kaydet
    save_bulletin_as_markdown(data)

    print(f"\n🎉 Analiz tamamlandı! {len(items)} haber işlendi.")

if __name__ == "__main__":
    run()
