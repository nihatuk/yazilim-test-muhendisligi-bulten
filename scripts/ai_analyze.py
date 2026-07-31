import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_news(items):
    """Her habere kısa Türkçe yorum ekle"""
    print("\n🤖 ChatGPT haberleri analiz ediyor...\n")

    analyzed = []
    for i, item in enumerate(items):
        print(f"   📝 {i+1}/{len(items)}: {item['title'][:60]}...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen kıdemli bir yazılım test mühendisisin. "
                            "Haberleri Türkçe olarak kısaca analiz ediyorsun. "
                            "2-3 cümle, sade ve profesyonel yaz."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Başlık: {item['title']}\n"
                            f"Özet: {item['summary']}\n\n"
                            "Bu haberi yazılım test mühendisleri için kısaca analiz et."
                        )
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )
            item['ai_comment'] = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️ Hata: {e}")
            item['ai_comment'] = ""

        analyzed.append(item)

    return analyzed

def generate_nihat_yorum(items):
    """Nihat Ük'ün köşe yazısını oluştur"""
    print("\n✍️  Nihat Ük'ün yorumu yazılıyor...\n")

    # Haber başlıklarını özetle
    titles = "\n".join([f"- {item['title']}" for item in items[:10]])

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen Nihat Ük'sün. Türkiye'nin önde gelen yazılım test mühendisliği "
                        "uzmanlarından birisin. Her hafta sektördeki gelişmeleri değerlendiren "
                        "bir köşe yazısı yazıyorsun. Samimi, deneyimli ve ilham verici bir "
                        "üslupla yazıyorsun. Türkçe yaz."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Bu hafta şu haberler öne çıktı:\n{titles}\n\n"
                        "Bu gelişmeleri değerlendiren, yazılım test mühendislerine "
                        "yönelik 3-4 paragraflık bir köşe yazısı yaz."
                    )
                }
            ],
            max_tokens=600,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"   ⚠️ Nihat yorumu hatası: {e}")
        return ""

def run_analysis():
    # JSON'u oku
    with open('data/weekly_news.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data['items']

    # Haberleri analiz et
    analyzed_items = analyze_news(items)

    # Nihat'ın yorumunu oluştur
    nihat_yorum = generate_nihat_yorum(analyzed_items)

    # Güncelle ve kaydet
    data['items'] = analyzed_items
    data['nihat_yorum'] = nihat_yorum

    with open('data/weekly_news.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Analiz tamamlandı ve kaydedildi!")
    return analyzed_items, nihat_yorum

if __name__ == "__main__":
    run_analysis()
