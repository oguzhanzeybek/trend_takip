import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
print(f"🔑 API Key Okundu mu?: {'EVET' if api_key else 'HAYIR'}")

client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

MODEL_NAME = "openai/gpt-4o-mini"

print(f"⏳ {MODEL_NAME} modeline bağlanılıyor...")

try:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": "Merhaba, test mesajı."}
        ],
    )
    print("✅ BAŞARILI! Cevap:")
    print(response.choices[0].message.content)

except Exception as e:
    print("\n❌ HATA OLUŞTU!")
    print(f"Hata Detayı: {e}")