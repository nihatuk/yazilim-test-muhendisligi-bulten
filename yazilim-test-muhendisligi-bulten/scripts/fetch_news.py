import feedparser
import yaml
import json
import os
from datetime import datetime, timedelta

def load_sources():
    """sources.yaml dosyasını oku"""
    with open('sources.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def is_recent(entry, days=7):
    """Haberin son 7 günde olup olmadığını kontrol et"""
    try:
        published = datetime(*entry.published_parsed[:6])
        return published > datetime.now() - timedelta(days=days)
    except:
        return True  # Tarih yoksa dahil et

def clean_text(text, max_chars=300):
    """HTML taglarını temizle ve kısalt"""
    import re
    clean = re.sub(r'<[^>]+>', '', text)  # HTML temizle
    clean = clean.replace('\n', ' ').strip()
    return clean[:max_chars] + "..." if len(clean) > max_chars else clean

def fetch_weekly_news():
    """Tüm kaynaklardan haberleri topla"""
    sources = load_sources()
    news_items = []
    
    print("🔍 Haberler toplanıyor...\n")
    
    for feed_info in sources['rss_feeds']:
        print(f"📡 {feed_info['name']} okunuyor...")
        
        try:
            feed = feedparser.parse(feed_info['url'])
            count = 0
            
            for entry in feed.entries:
                if not is_recent(entry):
                    continue
                    
                # Özet al (summary veya description)
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
                    'date': entry.get('published', datetime.now().isoformat())
                })
                count += 1
                
                if count >= 5:  # Her kaynaktan max 5 haber
                    break
                    
            print(f"   ✅ {count} haber bulundu")
            
        except Exception as e:
            print(f"   ❌ Hata: {e}")
    
    # data/ klasörüne kaydet
    os.makedirs('data', exist_ok=True)
    output_file = 'data/weekly_news.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'total': len(news_items),
            'items': news_items
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Toplam {len(news_items)} haber kaydedildi!")
    print(f"📄 Dosya: {output_file}")
    return news_items

if __name__ == "__main__":
    fetch_weekly_news()
