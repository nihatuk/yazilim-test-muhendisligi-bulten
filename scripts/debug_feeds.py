# scripts/debug_feeds.py
import feedparser
import yaml
from datetime import datetime, timedelta

def load_sources():
    with open('sources.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def check_feeds():
    sources = load_sources()
    total_available = 0

    for feed_info in sources['rss_feeds']:
        print(f"\n{'='*60}")
        print(f"📡 {feed_info['name']}")
        print(f"   URL: {feed_info['url']}")

        try:
            feed = feedparser.parse(feed_info['url'])
            entries = feed.entries
            print(f"   Toplam entry sayısı: {len(entries)}")

            if len(entries) == 0:
                print("   ⚠️  Feed boş veya erişilemiyor!")
                continue

            recent_count = 0
            for entry in entries[:5]:
                published_raw = entry.get('published', 'YOK')
                published_parsed = entry.get('published_parsed', None)

                # Tarih hesapla
                is_recent = False
                age_str = "?"
                if published_parsed:
                    try:
                        pub_date = datetime(*published_parsed[:6])
                        age = datetime.now() - pub_date
                        age_str = f"{age.days} gün önce"
                        is_recent = age.days <= 7
                    except:
                        age_str = "parse hatası"
                        is_recent = True
                else:
                    age_str = "tarih yok"
                    is_recent = True

                icon = "✅" if is_recent else "❌"
                print(f"   {icon} [{age_str}] {entry.get('title','')[:55]}")

                if is_recent:
                    recent_count += 1

            print(f"   📊 Son 7 günde: {recent_count} haber")
            total_available += recent_count

        except Exception as e:
            print(f"   ❌ HATA: {e}")

    print(f"\n{'='*60}")
    print(f"🎯 TOPLAM KULLANILABILIR HABER: {total_available}")

if __name__ == "__main__":
    check_feeds()
