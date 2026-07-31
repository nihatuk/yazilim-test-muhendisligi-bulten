import feedparser
import yaml
import json
import os
from datetime import datetime, timedelta

def load_sources():
    with open('sources.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def clean_text(text, max_chars=300):
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('\n', ' ').strip()
    return clean[:max_chars] + "..." if len(clean) > max_chars else clean

def fetch_weekly_news():
    sources = load_sources()
    news_items = []

    print("🔍 Haberler toplanıyor...\n")

    for feed_info in sources['rss_feeds']:
        print(f"📡 {feed_info['name']} okunuyor...")
        print(f"   URL: {feed_info['url']}")

        try:
            feed = feedparser.parse(feed_info['url'])
            
            # 🔍 DEBUG - kaç entry var?
            print(f"   📊 Toplam entry sayısı: {len(feed.entries)}")
            
            if len(feed.entries) == 0:
                print(f"   ⚠️  Feed boş veya URL hatalı!")
                print(f"   Feed status: {feed.get('status', 'bilinmiyor')}")
                continue

            count = 0
            for entry in feed.entries:
                
                # 🔍 DEBUG - tarih bilgisi var mı?
                pub_date = entry.get('published', None)
                pub_parsed = entry.get('published_parsed', None)
                
                if count == 0:  # Sadece ilk entry için göster
                    print(f"   📅 İlk haber tarihi: {pub_date}")

                summary = ""
                if hasattr(entry, 'summary'):
                    summary = clean_text(entry.summary)
                elif hasattr(entry, 'description'):
                    summary = clean_text(entry.description)

                news_items.append({
                    'title': entry.get('title', 'Başlık yok'),
                    'link': entry.get('link', ''),
                    'summary': summary,
                    'source': feed_info['name'],
                    'date': pub_date or datetime.now().isoformat()
                })
                count += 1

                if count >= 5:
                    break

            print(f"   ✅ {count} haber eklendi\n")

        except Exception as e:
            print(f"   ❌ Hata: {e}\n")

    # Kaydet
    os.makedirs('data', exist_ok=True)
    output_file = 'data/weekly_news.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'total': len(news_items),
            'items': news_items
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Toplam {len(news_items)} haber kaydedildi!")
    print(f"📄 Dosya: {output_file}")
    return news_items

if __name__ == "__main__":
    fetch_weekly_news()
