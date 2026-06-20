from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Verileri saklayacağımız liste
veriler = []
veri_dict = {}  # TC'ye göre hızlı erişim için sözlük

def verileri_yukle():
    """eokul.txt dosyasındaki verileri yükler"""
    global veriler, veri_dict
    veriler = []
    veri_dict = {}
    
    dosya_yolu = 'eokul.txt'
    if not os.path.exists(dosya_yolu):
        print(f"Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                
                # Veriyi | karakterine göre ayır
                parcalar = [p.strip() for p in satir.split('|')]
                
                if len(parcalar) >= 5:
                    kisi = {
                        'tc': parcalar[0],
                        'ad': parcalar[1],
                        'soyad': parcalar[2],
                        'dogum': parcalar[3],
                        'universite': parcalar[4]
                    }
                    veriler.append(kisi)
                    veri_dict[parcalar[0]] = kisi  # TC'ye göre indeksle
        
        print(f"✅ {len(veriler)} kayıt yüklendi.")
        
    except Exception as e:
        print(f"❌ Dosya okunurken hata: {e}")

@app.route('/', methods=['GET'])
def ana_sayfa():
    """Ana sayfa - API bilgileri"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'E-Okul Sorgulama API',
        'versiyon': '2.0',
        'toplam_kayit': len(veriler),
        'ornek_kullanim': '/api?tc=11060326504',
        'endpointler': {
            '/api': 'TC ile sorgula (örn: /api?tc=11060326504)',
            '/api?tc=TC_NO': 'TC ile detaylı sorgu',
            '/api?ad=AD': 'Ad ile ara (kısmi eşleşme)',
            '/api?soyad=SOYAD': 'Soyad ile ara (kısmi eşleşme)',
            '/api?ad=AD&soyad=SOYAD': 'Ad ve soyad ile ara',
            '/tumveriler': 'Tüm verileri listele (dikkat: çok fazla veri!)'
        }
    })

@app.route('/api', methods=['GET'])
def api_sorgula():
    """Ana sorgu endpoint'i - TC, ad veya soyad ile ara"""
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    # TC ile sorgu (tam eşleşme - en hızlı)
    if tc:
        if tc in veri_dict:
            return jsonify(veri_dict[tc])
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': f'{tc} TC numarası bulunamadı',
                'sonuc': None
            }), 404
    
    # Ad ve soyad ile sorgu
    if ad and soyad:
        sonuc = [
            kisi for kisi in veriler 
            if ad.upper() in kisi['ad'].upper() 
            and soyad.upper() in kisi['soyad'].upper()
        ]
        return jsonify({
            'durum': 'başarılı',
            'bulunan': len(sonuc),
            'sonuc': sonuc
        })
    
    # Sadece ad ile sorgu
    if ad:
        sonuc = [
            kisi for kisi in veriler 
            if ad.upper() in kisi['ad'].upper()
        ]
        return jsonify({
            'durum': 'başarılı',
            'bulunan': len(sonuc),
            'sonuc': sonuc
        })
    
    # Sadece soyad ile sorgu
    if soyad:
        sonuc = [
            kisi for kisi in veriler 
            if soyad.upper() in kisi['soyad'].upper()
        ]
        return jsonify({
            'durum': 'başarılı',
            'bulunan': len(sonuc),
            'sonuc': sonuc
        })
    
    # Hiç parametre yoksa
    return jsonify({
        'durum': 'hata',
        'mesaj': 'Lütfen tc, ad veya soyad parametresi girin',
        'ornek': '/api?tc=11060326504',
        'kullanım': {
            'tc': 'TC ile sorgula: /api?tc=12345678901',
            'ad': 'Ad ile sorgula: /api?ad=gazel',
            'soyad': 'Soyad ile sorgula: /api?soyad=atila',
            'ad_soyad': 'Ad ve soyad ile sorgula: /api?ad=gazel&soyad=atila'
        }
    }), 400

@app.route('/tumveriler', methods=['GET'])
def tum_veriler():
    """Tüm verileri listele"""
    return jsonify({
        'durum': 'başarılı',
        'toplam': len(veriler),
        'veriler': veriler
    })

@app.route('/ara/<tc>', methods=['GET'])
def tc_ile_ara(tc):
    """TC ile ara (URL path üzerinden)"""
    tc = tc.strip()
    
    if tc in veri_dict:
        return jsonify(veri_dict[tc])
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{tc} TC numarası bulunamadı'
        }), 404

# Uygulama başladığında verileri yükle
verileri_yukle()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
