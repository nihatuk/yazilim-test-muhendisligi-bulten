import feedparser
import yaml
import json
import os
import re
import glob
from datetime import datetime, timedelta

def load_sources():
    with open('sources.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def is_recent(entry, days=7):
    try:
        published = datetime(*entry.published_parsed[:6])
        return published > datetime.now() - timedelta(days=days)
    except:
        return True

def clean_text(text, max_chars=300):
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('\n', ' ').strip()
    return clean[:max_chars] + "..." if len(clean) > max_chars else clean

# ─────────────────────────────────────────
# DUPLICATE KONTROL
# ─────────────────────────────────────────

def load_seen_links(data_dir="data", last_n_bulletins=2):
    """Son N bültendeki linkleri yükle — bunlar tekrar eklenmez"""
    seen = set()

    # ✅ weekly_news.json DIŞLANIR — sadece tarihli dosyalar kontrol edilir
    json_files = sorted(
        [
            f for f in glob.glob(os.path.join(data_dir, "*.json"))
            if os.path.basename(f) != "weekly_news.json"
        ],
        reverse=True
    )[:last_n_bulletins]

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('items', []):
                    link = item.get('link', '').strip()
                    if link:
                        seen.add(link)
            print(f"   📂 {os.path.basename(filepath)} → {len(seen)} link yüklendi")
        except Exception as e:
            print(f"   ⚠️ Dosya okunamadı {filepath}: {e}")

    return seen

# ─────────────────────────────────────────
# HABER ÇEKME
# ─────────────────────────────────────────

def fetch_weekly_news():
    sources = load_sources()
    news_items = []

    print("📂 Önceki bültenler kontrol ediliyor...")
    seen_links = load_seen_links(last_n_bulletins=2)
    print(f"   🔒 {len(seen_links)} link daha önce görülmüş\n")

    print("🔍 Haberler toplanıyor...\n")

    new_count = 0
    skip_count = 0

    for feed_info in sources['rss_feeds']:
        print(f"📡 {feed_info['name']} okunuyor...")
        try:
            feed = feedparser.parse(feed_info['url'])
            count = 0

            for entry in feed.entries:
                if not is_recent(entry):
                    continue

                link = entry.get('link', '').strip()

                # ✅ Duplicate kontrolü
                if link in seen_links:
                    skip_count += 1
                    continue

                summary = ""
                if hasattr(entry, 'summary'):
                    summary = clean_text(entry.summary)
                elif hasattr(entry, 'description'):
                    summary = clean_text(entry.description)

                news_items.append({
                    'title': entry.get('title', 'Başlık yok'),
                    'link': link,
                    'summary': summary,
                    'source': feed_info['name'],
                    'lang': feed_info.get('lang', 'en'),
                    'date': entry.get('published', datetime.now().isoformat()),
                    'ai_comment': ""
                })

                # Bu çalışmada da tekrar eklenmemesi için
                seen_links.add(link)
                count += 1
                new_count += 1

                if count >= 5:
                    break

            print(f"   ✅ {count} yeni haber")

        except Exception as e:
            print(f"   ❌ Hata ({feed_info['name']}): {e}")

    print(f"\n📊 Sonuç: {new_count} yeni | {skip_count} tekrar atlandı")

    if not news_items:
        print("⚠️ Yeni haber bulunamadı!")

    # ✅ Sadece bu günün haberlerini yaz (eski haberler dahil edilmez)
    os.makedirs('data', exist_ok=True)
    with open('data/weekly_news.json', 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'total': len(news_items),
            'items': news_items
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(news_items)} haber kaydedildi → data/weekly_news.json")
    return news_items

if __name__ == "__main__":
    fetch_weekly_news()
