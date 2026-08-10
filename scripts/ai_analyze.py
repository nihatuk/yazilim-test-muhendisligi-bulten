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
        lang_note = "Haber İngilizce olsa da yorumu Türkçe yaz." if item.get('lang')
