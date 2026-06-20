from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Tüm domainlere izin ver

# Verileri saklayacağımız liste
veriler = []

def verileri_yukle():
    """eokul.txt dosyasındaki verileri yükler"""
    global veriler
    veriler = []
    
    # Dosya yolunu kontrol et
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
                    veriler.append({
                        'tc': parcalar[0],
                        'ad': parcalar[1],
                        'soyad': parcalar[2],
                        'dogum': parcalar[3],
                        'universite': parcalar[4]
                    })
        
        print(f"✅ {len(veriler)} kayıt yüklendi.")
        
    except Exception as e:
        print(f"❌ Dosya okunurken hata: {e}")

@app.route('/', methods=['GET'])
def ana_sayfa():
    """Ana sayfa - API bilgileri"""
    return jsonify({
        'api': 'E-Okul Sorgulama API',
        'version': '1.0',
        'endpoints': {
            '/': 'Bu bilgi sayfası',
            '/sorgula': 'Tüm verileri listele',
            '/ara/tc/<tc>': 'TC ile ara (örn: /ara/tc/11060326504)',
            '/ara/ad/<ad>': 'Ad ile ara (örn: /ara/ad/gazel)',
            '/ara/soyad/<soyad>': 'Soyad ile ara (örn: /ara/soyad/atila)',
            '/ara/ad-soyad/<ad>/<soyad>': 'Ad ve soyad ile ara (örn: /ara/ad-soyad/gazel/atila)',
        },
        'toplam_kayit': len(veriler)
    })

@app.route('/sorgula', methods=['GET'])
def tum_veriler():
    """Tüm verileri listele"""
    return jsonify({
        'success': True,
        'count': len(veriler),
        'data': veriler
    })

@app.route('/ara/tc/<tc>', methods=['GET'])
def tc_ile_ara(tc):
    """TC numarasına göre ara"""
    # TC'yi temizle
    tc = tc.strip()
    
    # Eşleşen kayıtları bul
    sonuc = [kisi for kisi in veriler if kisi['tc'] == tc]
    
    if sonuc:
        return jsonify({
            'success': True,
            'found': True,
            'count': len(sonuc),
            'data': sonuc[0]  # TC unique olduğu için ilkini döndür
        })
    else:
        return jsonify({
            'success': True,
            'found': False,
            'message': f'TC {tc} bulunamadı',
            'data': None
        })

@app.route('/ara/ad/<ad>', methods=['GET'])
def ad_ile_ara(ad):
    """Ad'a göre ara (kısmi eşleşme)"""
    ad = ad.strip().upper()
    
    # Ad'ı içeren kayıtları bul (büyük/küçük harf duyarsız)
    sonuc = [
        kisi for kisi in veriler 
        if ad in kisi['ad'].upper()
    ]
    
    return jsonify({
        'success': True,
        'found': len(sonuc) > 0,
        'count': len(sonuc),
        'data': sonuc
    })

@app.route('/ara/soyad/<soyad>', methods=['GET'])
def soyad_ile_ara(soyad):
    """Soyad'a göre ara (kısmi eşleşme)"""
    soyad = soyad.strip().upper()
    
    # Soyad'ı içeren kayıtları bul (büyük/küçük harf duyarsız)
    sonuc = [
        kisi for kisi in veriler 
        if soyad in kisi['soyad'].upper()
    ]
    
    return jsonify({
        'success': True,
        'found': len(sonuc) > 0,
        'count': len(sonuc),
        'data': sonuc
    })

@app.route('/ara/ad-soyad/<ad>/<soyad>', methods=['GET'])
def ad_soyad_ile_ara(ad, soyad):
    """Ad ve soyad ile ara (kısmi eşleşme)"""
    ad = ad.strip().upper()
    soyad = soyad.strip().upper()
    
    # Ad ve soyad'ı içeren kayıtları bul
    sonuc = [
        kisi for kisi in veriler 
        if ad in kisi['ad'].upper() and soyad in kisi['soyad'].upper()
    ]
    
    return jsonify({
        'success': True,
        'found': len(sonuc) > 0,
        'count': len(sonuc),
        'data': sonuc
    })

@app.route('/ara/query', methods=['GET'])
def query_ile_ara():
    """Sorgu parametreleri ile ara (örn: /ara/query?tc=123&ad=gazel)"""
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    sonuc = veriler
    
    # TC ile filtrele
    if tc:
        sonuc = [kisi for kisi in sonuc if kisi['tc'] == tc]
    
    # Ad ile filtrele
    if ad:
        ad_upper = ad.upper()
        sonuc = [kisi for kisi in sonuc if ad_upper in kisi['ad'].upper()]
    
    # Soyad ile filtrele
    if soyad:
        soyad_upper = soyad.upper()
        sonuc = [kisi for kisi in sonuc if soyad_upper in kisi['soyad'].upper()]
    
    return jsonify({
        'success': True,
        'found': len(sonuc) > 0,
        'count': len(sonuc),
        'data': sonuc
    })

# Uygulama başladığında verileri yükle
verileri_yukle()

if __name__ == '__main__':
    # Render'da çalıştırmak için
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
