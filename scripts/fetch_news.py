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
            feed = feedparser.parse(feed_info
