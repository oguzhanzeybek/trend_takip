// app_frontend/static/script.js

document.addEventListener('DOMContentLoaded', () => {
    const recommendationsList = document.getElementById('recommendations-list');
    const getRecommendationsBtn = document.getElementById('getRecommendationsBtn');
    const articleIdDisplay = document.getElementById('article-id-display');
    
    // Arka uç API'sinin Deta Space'teki yolu (/api/recommendations)
    const API_ENDPOINT = '/api/recommendations'; 

    getRecommendationsBtn.addEventListener('click', async () => {
        recommendationsList.innerHTML = '<li>Öneriler yükleniyor...</li>';

        // Ön yüzde gösterilen (veya bir inputtan alınan) makale ID'sini al.
        const articleId = articleIdDisplay.textContent.trim(); 
        
        try {
            // FastAPI'a istek atılıyor
            const response = await fetch(`${API_ENDPOINT}?article_id=${articleId}&count=5`);
            
            // 404 (Bulunamadı) durumunu özel olarak ele al
            if (response.status === 404) {
                recommendationsList.innerHTML = '<li>Üzgünüz, bu makale için öneri bulunamadı (404).</li>';
                return;
            }
            // Diğer HTTP hatalarını kontrol et
            if (!response.ok) {
                throw new Error(`API hatası: ${response.status}`);
            }

            const recommendations = await response.json();

            // Liste içeriğini temizle
            recommendationsList.innerHTML = '';

            if (recommendations.length === 0) {
                 recommendationsList.innerHTML = '<li>Öneri döndürüldü, ancak liste boş.</li>';
            } else {
                // Gelen önerileri listeye ekle
                recommendations.forEach(item => {
                    const li = document.createElement('li');
                    // title ve url alanları scraper'dan gelmeli
                    li.innerHTML = `<a href="${item.url}" target="_blank"><strong>${item.title}</strong></a> (Key: ${item.key})`;
                    recommendationsList.appendChild(li);
                });
            }

        } catch (error) {
            console.error('Öneri çekerken bir hata oluştu:', error);
            recommendationsList.innerHTML = `<li>Hata: Öneriler yüklenemedi. Arka uç hizmetini kontrol edin. (${error.message})</li>`;
        }
    });
});