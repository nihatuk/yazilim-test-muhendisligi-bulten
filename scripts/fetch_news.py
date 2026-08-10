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
# DUPLICATE KONTROL — .md dosyalarından
# ─────────────────────────────────────────

def load_seen_links_from_md(data_dir="data"):
    """
    data/ klasöründeki .md dosyalarından
    daha önce yayınlanmış linkleri çıkar.
    """
    seen = set()

    md_files = sorted(
        glob.glob(os.path.join(data_dir, "*.md")),
        reverse=True
    )

    # URL pattern: markdown linkleri [title](url) veya düz url
    url_pattern = re.compile(r'https?://[^\s\)\]"\'<>]+')

    for filepath in md_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            links = url_pattern.findall(content)
            for link in links:
                link = link.strip().rstrip(')')
                seen.add(link)
            print(f"   📂 {os.path.basename(filepath)} → {len(links)} link bulundu")
        except Exception as e:
            print(f"   ⚠️ Dosya okunamadı {filepath}: {e}")

    # JSON dosyalarından da kontrol et (varsa)
    json_files = sorted(
        [
            f for f in glob.glob(os.path.join(data_dir, "*.json"))
            if os.path.basename(f) != "weekly_news.json"
        ],
        reverse=True
    )

    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data.get('items', []):
                link = item.get('link', '').strip()
                if link:
                    seen.add(link)
            print(f"   📂 {os.path.basename(filepath)} → JSON okundu")
        except Exception as e:
            print(f"   ⚠️ JSON okunamadı {filepath}: {e}")

    print(f"   🔒 Toplam {len(seen)} link daha önce görülmüş")
    return seen

# ─────────────────────────────────────────
# HABER ÇEKME
# ─────────────────────────────────────────

def fetch_weekly_news():
    sources = load_sources()
    news_items = []

    print("📂 Önceki bültenler kontrol ediliyor...")
    seen_links = load_seen_links_from_md()
    print()

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
                    print(f"   ⏭️  Atlandı (eski): {entry.get('title','')[:60]}")
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
