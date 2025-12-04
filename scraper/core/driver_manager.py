import undetected_chromedriver as uc
import os

def get_chrome_driver():
    """
    Tüm botlar için ortak Chrome sürücüsünü yapılandırır ve döndürür.
    Ayarlar tek bir yerden yönetilir.
    """
    options = uc.ChromeOptions()
    
    options.add_argument("--headless=new")  # Arayüzsüz mod
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    CHROME_VERSION_MAIN = 142 
    
    try:
        print(f"🔌 Driver Başlatılıyor (Versiyon: {CHROME_VERSION_MAIN})...")
        driver = uc.Chrome(options=options, version_main=CHROME_VERSION_MAIN)
        return driver
    except Exception as e:
        print(f"❌ Driver başlatma hatası (Merkezi Yönetici): {e}")
        raise e