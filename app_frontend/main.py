# app_frontend/main.py

from flask import Flask, render_template

# Flask uygulamasını başlat
app = Flask(__name__)

# Ana sayfa rotası
@app.route('/')
def index():
    # templates/index.html dosyasını render et
    # Bu sayfa, JS ile arka uç API'nizi çağıracaktır.
    return render_template('index.html')

# Flask'ın Deta Space'te çalışması için bu kısım gerekli değildir,
# ancak lokal test için korunabilir.
if __name__ == '__main__':
    app.run(debug=True)