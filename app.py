from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Verileri saklayacağımız listeler
eokul_veriler = []
eokul_dict = {}  # TC'ye göre hızlı erişim için

secmen_veriler = []
secmen_dict = {}  # TC'ye göre hızlı erişim için

def eokul_verileri_yukle():
    """eokul.txt dosyasındaki verileri yükler"""
    global eokul_veriler, eokul_dict
    eokul_veriler = []
    eokul_dict = {}
    
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
                
                parcalar = [p.strip() for p in satir.split('|')]
                
                if len(parcalar) >= 5:
                    kisi = {
                        'tc': parcalar[0],
                        'ad': parcalar[1],
                        'soyad': parcalar[2],
                        'dogum': parcalar[3],
                        'universite': parcalar[4]
                    }
                    eokul_veriler.append(kisi)
                    eokul_dict[parcalar[0]] = kisi
        
        print(f"✅ E-Okul: {len(eokul_veriler)} kayıt yüklendi.")
        
    except Exception as e:
        print(f"❌ E-Okul dosyası okunurken hata: {e}")

def secmen_verileri_yukle():
    """secmen.txt dosyasındaki verileri yükler"""
    global secmen_veriler, secmen_dict
    secmen_veriler = []
    secmen_dict = {}
    
    dosya_yolu = 'secmen.txt'
    if not os.path.exists(dosya_yolu):
        print(f"Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                
                parcalar = [p.strip() for p in satir.split('|')]
                
                if len(parcalar) >= 5:
                    kisi = {
                        'tc': parcalar[0],
                        'ad': parcalar[1],
                        'soyad': parcalar[2],
                        'il': parcalar[3],
                        'adres': parcalar[4]
                    }
                    secmen_veriler.append(kisi)
                    secmen_dict[parcalar[0]] = kisi
        
        print(f"✅ Seçmen: {len(secmen_veriler)} kayıt yüklendi.")
        
    except Exception as e:
        print(f"❌ Seçmen dosyası okunurken hata: {e}")

@app.route('/', methods=['GET'])
def ana_sayfa():
    """Ana sayfa - API bilgileri"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'E-Okul & Seçmen Sorgulama API',
        'versiyon': '3.0',
        'veri_kaynaklari': {
            'eokul': {
                'toplam': len(eokul_veriler),
                'ornek': '/eokul/api?tc=11060326504'
            },
            'secmen': {
                'toplam': len(secmen_veriler),
                'ornek': '/secmen/api?tc=18445070762'
            }
        },
        'endpointler': {
            'E-Okul': {
                '/eokul': 'E-Okul ana sayfası',
                '/eokul/api': 'E-Okul sorgula (tc, ad, soyad)',
                '/eokul/ara/<tc>': 'E-Okul TC ile ara (path)'
            },
            'Seçmen': {
                '/secmen': 'Seçmen ana sayfası',
                '/secmen/api': 'Seçmen sorgula (tc, ad, soyad)',
                '/secmen/ara/<tc>': 'Seçmen TC ile ara (path)'
            }
        }
    })

# ==================== E-OKUL API'leri ====================

@app.route('/eokul', methods=['GET'])
def eokul_ana():
    """E-Okul API ana sayfası"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'E-Okul Sorgulama API',
        'toplam_kayit': len(eokul_veriler),
        'ornek_kullanim': '/eokul/api?tc=11060326504',
        'kullanım': {
            'tc': '/eokul/api?tc=12345678901',
            'ad': '/eokul/api?ad=gazel',
            'soyad': '/eokul/api?soyad=atila',
            'ad_soyad': '/eokul/api?ad=gazel&soyad=atila'
        }
    })

@app.route('/eokul/api', methods=['GET'])
def eokul_sorgula():
    """E-Okul sorgulama endpoint'i"""
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    # TC ile sorgu (tam eşleşme)
    if tc:
        if tc in eokul_dict:
            return jsonify(eokul_dict[tc])
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': f'{tc} TC numarası bulunamadı',
                'sonuc': None
            }), 404
    
    # Ad ve soyad ile sorgu
    if ad and soyad:
        sonuc = [
            kisi for kisi in eokul_veriler 
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
            kisi for kisi in eokul_veriler 
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
            kisi for kisi in eokul_veriler 
            if soyad.upper() in kisi['soyad'].upper()
        ]
        return jsonify({
            'durum': 'başarılı',
            'bulunan': len(sonuc),
            'sonuc': sonuc
        })
    
    return jsonify({
        'durum': 'hata',
        'mesaj': 'Lütfen tc, ad veya soyad parametresi girin',
        'kullanım': '/eokul/api?tc=11060326504'
    }), 400

@app.route('/eokul/ara/<tc>', methods=['GET'])
def eokul_tc_ara(tc):
    """E-Okul TC ile ara (path üzerinden)"""
    tc = tc.strip()
    
    if tc in eokul_dict:
        return jsonify(eokul_dict[tc])
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{tc} TC numarası bulunamadı'
        }), 404

# ==================== SEÇMEN API'leri ====================

@app.route('/secmen', methods=['GET'])
def secmen_ana():
    """Seçmen API ana sayfası"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'Seçmen Sorgulama API',
        'toplam_kayit': len(secmen_veriler),
        'ornek_kullanim': '/secmen/api?tc=18445070762',
        'kullanım': {
            'tc': '/secmen/api?tc=12345678901',
            'ad': '/secmen/api?ad=ahmet',
            'soyad': '/secmen/api?soyad=aydoğdu',
            'ad_soyad': '/secmen/api?ad=ahmet&soyad=aydoğdu',
            'il': '/secmen/api?il=adana',
            'adres': '/secmen/api?adres=akdere'
        }
    })

@app.route('/secmen/api', methods=['GET'])
def secmen_sorgula():
    """Seçmen sorgulama endpoint'i"""
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    il = request.args.get('il', '').strip()
    adres = request.args.get('adres', '').strip()
    
    # TC ile sorgu (tam eşleşme)
    if tc:
        if tc in secmen_dict:
            return jsonify(secmen_dict[tc])
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': f'{tc} TC numarası bulunamadı',
                'sonuc': None
            }), 404
    
    sonuc = secmen_veriler
    
    # Ad ile filtrele
    if ad:
        ad_upper = ad.upper()
        sonuc = [kisi for kisi in sonuc if ad_upper in kisi['ad'].upper()]
    
    # Soyad ile filtrele
    if soyad:
        soyad_upper = soyad.upper()
        sonuc = [kisi for kisi in sonuc if soyad_upper in kisi['soyad'].upper()]
    
    # İl ile filtrele
    if il:
        il_upper = il.upper()
        sonuc = [kisi for kisi in sonuc if il_upper in kisi['il'].upper()]
    
    # Adres ile filtrele (kısmi eşleşme)
    if adres:
        adres_upper = adres.upper()
        sonuc = [kisi for kisi in sonuc if adres_upper in kisi['adres'].upper()]
    
    if sonuc:
        return jsonify({
            'durum': 'başarılı',
            'bulunan': len(sonuc),
            'sonuc': sonuc
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kriterlere uygun kayıt bulunamadı',
            'sonuc': []
        }), 404

@app.route('/secmen/ara/<tc>', methods=['GET'])
def secmen_tc_ara(tc):
    """Seçmen TC ile ara (path üzerinden)"""
    tc = tc.strip()
    
    if tc in secmen_dict:
        return jsonify(secmen_dict[tc])
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{tc} TC numarası bulunamadı'
        }), 404

# ==================== UYGULAMA BAŞLATMA ====================

if __name__ == '__main__':
    # Verileri yükle
    eokul_verileri_yukle()
    secmen_verileri_yukle()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
