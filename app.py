from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import requests
import json

app = Flask(__name__)
CORS(app)

# Verileri saklayacağımız listeler
eokul_veriler = []
eokul_dict = {}

secmen_veriler = []
secmen_dict = {}

plaka_veriler = []
plaka_dict = {}
isim_dict = {}

# Stripe API bilgileri (GERÇEK API anahtarlarınızı buraya ekleyin)
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')  # Render'dan alınacak
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')

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

def plaka_verileri_yukle():
    """plaka.txt dosyasındaki verileri yükler"""
    global plaka_veriler, plaka_dict, isim_dict
    plaka_veriler = []
    plaka_dict = {}
    isim_dict = {}
    
    dosya_yolu = 'plaka.txt'
    if not os.path.exists(dosya_yolu):
        print(f"Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                
                parcalar = satir.split()
                if len(parcalar) >= 2:
                    plaka = parcalar[-1]
                    ad_soyad = ' '.join(parcalar[:-1])
                    ad_soyad = ' '.join(ad_soyad.split())
                    
                    kisi = {
                        'ad_soyad': ad_soyad,
                        'plaka': plaka
                    }
                    
                    plaka_veriler.append(kisi)
                    
                    if plaka not in plaka_dict:
                        plaka_dict[plaka] = []
                    plaka_dict[plaka].append(ad_soyad)
                    
                    if ad_soyad not in isim_dict:
                        isim_dict[ad_soyad] = []
                    isim_dict[ad_soyad].append(plaka)
        
        print(f"✅ Plaka: {len(plaka_veriler)} kayıt yüklendi.")
        print(f"   - {len(plaka_dict)} benzersiz plaka")
        print(f"   - {len(isim_dict)} benzersiz kişi")
        
    except Exception as e:
        print(f"❌ Plaka dosyası okunurken hata: {e}")

# ==================== CC DOĞRULAMA FONKSİYONLARI ====================

def luhn_kontrol(kart_no):
    """Luhn algoritması ile kart numarasını doğrula"""
    kart_no = re.sub(r'\D', '', kart_no)  # Sadece rakamları al
    
    if not kart_no.isdigit():
        return False
    
    toplam = 0
    cift = False
    
    # Sağdan sola doğru kontrol et
    for rakam in reversed(kart_no):
        rakam = int(rakam)
        if cift:
            rakam *= 2
            if rakam > 9:
                rakam -= 9
        toplam += rakam
        cift = not cift
    
    return toplam % 10 == 0

def kart_bilgilerini_kontrol(kart_no, ay, yil, cvv):
    """Kart bilgilerinin geçerliliğini kontrol et"""
    hatalar = []
    
    # Kart numarası kontrolü
    kart_no = re.sub(r'\D', '', kart_no)
    if len(kart_no) < 13 or len(kart_no) > 19:
        hatalar.append("Kart numarası 13-19 hane arası olmalıdır")
    elif not luhn_kontrol(kart_no):
        hatalar.append("Kart numarası geçersiz (Luhn kontrolü başarısız)")
    
    # Ay kontrolü
    try:
        ay_int = int(ay)
        if ay_int < 1 or ay_int > 12:
            hatalar.append("Ay 1-12 arası olmalıdır")
    except ValueError:
        hatalar.append("Geçerli bir ay giriniz")
    
    # Yıl kontrolü
    try:
        yil_int = int(yil)
        if yil_int < 2024 or yil_int > 2035:
            hatalar.append("Yıl 2024-2035 arası olmalıdır")
    except ValueError:
        hatalar.append("Geçerli bir yıl giriniz")
    
    # CVV kontrolü
    if len(str(cvv)) < 3 or len(str(cvv)) > 4:
        hatalar.append("CVV 3-4 hane olmalıdır")
    elif not str(cvv).isdigit():
        hatalar.append("CVV sadece rakam içermelidir")
    
    return hatalar

def stripe_ile_dogrula(kart_no, ay, yil, cvv):
    """Stripe API ile kart doğrulama (GERÇEK)"""
    if not STRIPE_SECRET_KEY:
        return {
            'durum': 'hata',
            'mesaj': 'Stripe API anahtarı ayarlanmamış. Lütfen STRIPE_SECRET_KEY değişkenini ayarlayın.',
            'stripe_kullanilamiyor': True
        }
    
    try:
        # Stripe Payment Method oluştur
        url = 'https://api.stripe.com/v1/payment_methods'
        
        # Kart bilgilerini hazırla
        data = {
            'type': 'card',
            'card[number]': kart_no.replace(' ', '').replace('-', ''),
            'card[exp_month]': ay,
            'card[exp_year]': yil,
            'card[cvc]': cvv
        }
        
        headers = {
            'Authorization': f'Bearer {STRIPE_SECRET_KEY}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(url, data=data, headers=headers)
        
        if response.status_code == 200:
            return {
                'durum': 'başarılı',
                'stripe_kontrol': True,
                'mesaj': 'Kart bilgileri Stripe tarafından doğrulandı',
                'payment_method_id': response.json().get('id')
            }
        else:
            hata = response.json()
            return {
                'durum': 'hata',
                'stripe_kontrol': False,
                'mesaj': f'Stripe hatası: {hata.get("error", {}).get("message", "Bilinmeyen hata")}',
                'stripe_kullanilamiyor': False
            }
            
    except Exception as e:
        return {
            'durum': 'hata',
            'stripe_kontrol': False,
            'mesaj': f'Stripe bağlantı hatası: {str(e)}',
            'stripe_kullanilamiyor': False
        }

@app.route('/', methods=['GET'])
def ana_sayfa():
    """Ana sayfa - API bilgileri"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'E-Okul & Seçmen & Plaka & CC Sorgulama API',
        'versiyon': '5.0',
        'veri_kaynaklari': {
            'eokul': {
                'toplam': len(eokul_veriler),
                'ornek': '/eokul/api?tc=11060326504'
            },
            'secmen': {
                'toplam': len(secmen_veriler),
                'ornek': '/secmen/api?tc=18445070762'
            },
            'plaka': {
                'toplam': len(plaka_veriler),
                'benzersiz_plaka': len(plaka_dict),
                'benzersiz_kisi': len(isim_dict),
                'ornek': '/plaka/api?plaka=41HU096'
            },
            'cc_dogrulama': {
                'stripe_aktif': bool(STRIPE_SECRET_KEY),
                'ornek': '/cc/dogrula'
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
                '/secmen/api': 'Seçmen sorgula (tc, ad, soyad, il, adres)',
                '/secmen/ara/<tc>': 'Seçmen TC ile ara (path)'
            },
            'Plaka': {
                '/plaka': 'Plaka ana sayfası',
                '/plaka/api': 'Plaka sorgula (plaka veya ad_soyad)',
                '/plaka/plaka/<plaka>': 'Plakaya göre ara (path)',
                '/plaka/isim/<ad_soyad>': 'İsme göre ara (path)'
            },
            'CC Doğrulama': {
                '/cc/dogrula': 'Kart doğrulama (POST)',
                '/cc/luhn': 'Sadece Luhn kontrolü (GET/POST)',
                '/cc/bilgi': 'Kart bilgilerini format kontrolü (POST)'
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
    
    if tc:
        if tc in eokul_dict:
            return jsonify(eokul_dict[tc])
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': f'{tc} TC numarası bulunamadı',
                'sonuc': None
            }), 404
    
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
    
    if ad:
        ad_upper = ad.upper()
        sonuc = [kisi for kisi in sonuc if ad_upper in kisi['ad'].upper()]
    
    if soyad:
        soyad_upper = soyad.upper()
        sonuc = [kisi for kisi in sonuc if soyad_upper in kisi['soyad'].upper()]
    
    if il:
        il_upper = il.upper()
        sonuc = [kisi for kisi in sonuc if il_upper in kisi['il'].upper()]
    
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

# ==================== PLAKA API'leri ====================

@app.route('/plaka', methods=['GET'])
def plaka_ana():
    """Plaka API ana sayfası"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'Plaka Sorgulama API',
        'toplam_kayit': len(plaka_veriler),
        'benzersiz_plaka': len(plaka_dict),
        'benzersiz_kisi': len(isim_dict),
        'ornek_kullanim': '/plaka/api?plaka=41HU096',
        'kullanım': {
            'plaka_ile': '/plaka/api?plaka=41HU096',
            'isim_ile': '/plaka/api?ad_soyad=CEVDET ALKIŞ',
            'path_plaka': '/plaka/plaka/41HU096',
            'path_isim': '/plaka/isim/CEVDET ALKIŞ'
        }
    })

@app.route('/plaka/api', methods=['GET'])
def plaka_sorgula():
    """Plaka sorgulama endpoint'i"""
    plaka = request.args.get('plaka', '').strip().upper()
    ad_soyad = request.args.get('ad_soyad', '').strip().upper()
    
    if plaka:
        if plaka in plaka_dict:
            kisiler = plaka_dict[plaka]
            return jsonify({
                'durum': 'başarılı',
                'plaka': plaka,
                'kisi_sayisi': len(kisiler),
                'kisiler': kisiler
            })
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': f'{plaka} plakası bulunamadı',
                'sonuc': None
            }), 404
    
    if ad_soyad:
        bulunan = []
        for kayit in plaka_veriler:
            if ad_soyad in kayit['ad_soyad'].upper():
                bulunan.append(kayit)
        
        if bulunan:
            plakalar = list(set([k['plaka'] for k in bulunan]))
            return jsonify({
                'durum': 'başarılı',
                'ad_soyad': ad_soyad,
                'plaka_sayisi': len(plakalar),
                'plakalar': plakalar,
                'detaylar': bulunan
            })
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': f'{ad_soyad} ismi bulunamadı',
                'sonuc': None
            }), 404
    
    return jsonify({
        'durum': 'hata',
        'mesaj': 'Lütfen plaka veya ad_soyad parametresi girin',
        'kullanım': '/plaka/api?plaka=41HU096 veya /plaka/api?ad_soyad=CEVDET ALKIŞ'
    }), 400

@app.route('/plaka/plaka/<plaka>', methods=['GET'])
def plaka_ile_ara(plaka):
    """Plakaya göre ara (path üzerinden)"""
    plaka = plaka.strip().upper()
    
    if plaka in plaka_dict:
        return jsonify({
            'durum': 'başarılı',
            'plaka': plaka,
            'kisiler': plaka_dict[plaka]
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{plaka} plakası bulunamadı'
        }), 404

@app.route('/plaka/isim/<ad_soyad>', methods=['GET'])
def isim_ile_ara(ad_soyad):
    """İsme göre ara (path üzerinden)"""
    ad_soyad = ad_soyad.strip().upper()
    
    bulunan = []
    for kayit in plaka_veriler:
        if ad_soyad in kayit['ad_soyad'].upper():
            bulunan.append(kayit)
    
    if bulunan:
        return jsonify({
            'durum': 'başarılı',
            'ad_soyad': ad_soyad,
            'bulunan': len(bulunan),
            'sonuc': bulunan
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{ad_soyad} ismi bulunamadı'
        }), 404

# ==================== CC DOĞRULAMA API'leri ====================

@app.route('/cc', methods=['GET'])
def cc_ana():
    """CC API ana sayfası"""
    return jsonify({
        'durum': 'başarılı',
        'api': 'Kredi Kartı Doğrulama API',
        'stripe_aktif': bool(STRIPE_SECRET_KEY),
        'kullanım': {
            'luhn_kontrol': '/cc/luhn?kart=1234567890123456',
            'detayli_dogrula': '/cc/dogrula (POST)',
            'format_kontrol': '/cc/bilgi (POST)'
        },
        'ornek_post': {
            'kart_no': '1234567890123456',
            'ay': '12',
            'yil': '2029',
            'cvv': '123'
        }
    })

@app.route('/cc/luhn', methods=['GET', 'POST'])
def luhn_kontrol_api():
    """Sadece Luhn algoritması ile kart numarası kontrolü"""
    if request.method == 'GET':
        kart_no = request.args.get('kart', '').strip()
    else:
        data = request.get_json() or {}
        kart_no = data.get('kart_no', '').strip()
    
    kart_no = re.sub(r'\D', '', kart_no)
    
    if not kart_no:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kart numarası giriniz',
            'kullanım': '/cc/luhn?kart=1234567890123456'
        }), 400
    
    sonuc = luhn_kontrol(kart_no)
    
    return jsonify({
        'durum': 'başarılı',
        'kart_no': kart_no,
        'gecerli': sonuc,
        'mesaj': 'Kart numarası geçerli' if sonuc else 'Kart numarası geçersiz'
    })

@app.route('/cc/bilgi', methods=['POST'])
def kart_bilgi_kontrol():
    """Kart bilgilerinin format kontrolü (Luhn + tarih + CVV)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'JSON verisi gönderiniz',
            'ornek': {
                'kart_no': '1234567890123456',
                'ay': '12',
                'yil': '2029',
                'cvv': '123'
            }
        }), 400
    
    kart_no = data.get('kart_no', '').strip()
    ay = data.get('ay', '').strip()
    yil = data.get('yil', '').strip()
    cvv = data.get('cvv', '').strip()
    
    if not all([kart_no, ay, yil, cvv]):
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kart_no, ay, yil ve cvv alanları zorunludur'
        }), 400
    
    # Temizle
    kart_no = re.sub(r'\D', '', kart_no)
    
    # Format kontrolü
    hatalar = kart_bilgilerini_kontrol(kart_no, ay, yil, cvv)
    
    if hatalar:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kart bilgileri geçersiz',
            'hatalar': hatalar,
            'gecerli': False
        }), 400
    else:
        return jsonify({
            'durum': 'başarılı',
            'mesaj': 'Kart bilgileri format olarak geçerli',
            'gecerli': True,
            'kart_no': kart_no,
            'ay': ay,
            'yil': yil,
            'cvv': cvv
        })

@app.route('/cc/dogrula', methods=['POST'])
def cc_dogrula():
    """Tam kart doğrulama (Luhn + Stripe)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'JSON verisi gönderiniz',
            'ornek': {
                'kart_no': '1234567890123456',
                'ay': '12',
                'yil': '2029',
                'cvv': '123'
            }
        }), 400
    
    kart_no = data.get('kart_no', '').strip()
    ay = data.get('ay', '').strip()
    yil = data.get('yil', '').strip()
    cvv = data.get('cvv', '').strip()
    
    if not all([kart_no, ay, yil, cvv]):
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kart_no, ay, yil ve cvv alanları zorunludur'
        }), 400
    
    # Temizle
    kart_no = re.sub(r'\D', '', kart_no)
    
    # Önce format kontrolü
    format_hatalar = kart_bilgilerini_kontrol(kart_no, ay, yil, cvv)
    
    if format_hatalar:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kart bilgileri format olarak geçersiz',
            'format_gecerli': False,
            'hatalar': format_hatalar,
            'stripe_kontrol': False
        }), 400
    
    # Stripe ile doğrula (eğer API anahtarı varsa)
    stripe_sonuc = stripe_ile_dogrula(kart_no, ay, yil, cvv)
    
    if stripe_sonuc.get('stripe_kullanilamiyor'):
        # Stripe yoksa sadece Luhn ile doğrula
        return jsonify({
            'durum': 'başarılı',
            'mesaj': 'Kart bilgileri format olarak geçerli (Stripe aktif değil)',
            'format_gecerli': True,
            'stripe_kontrol': False,
            'luhn_gecerli': luhn_kontrol(kart_no),
            'kart_no': kart_no[-4:],  # Son 4 hane
            'ay': ay,
            'yil': yil,
            'stripe_not': stripe_sonuc.get('mesaj', 'Stripe API anahtarı ayarlanmamış')
        })
    
    # Stripe sonucunu döndür
    return jsonify({
        'durum': stripe_sonuc.get('durum'),
        'format_gecerli': True,
        'stripe_kontrol': True,
        'luhn_gecerli': luhn_kontrol(kart_no),
        'mesaj': stripe_sonuc.get('mesaj'),
        'kart_no': kart_no[-4:],  # Sadece son 4 hane
        'ay': ay,
        'yil': yil,
        'payment_method_id': stripe_sonuc.get('payment_method_id')
    })

# ==================== UYGULAMA BAŞLATMA ====================

if __name__ == '__main__':
    # Verileri yükle
    eokul_verileri_yukle()
    secmen_verileri_yukle()
    plaka_verileri_yukle()
    
    print(f"\n📊 API Durumu:")
    print(f"   - Stripe API: {'✅ Aktif' if STRIPE_SECRET_KEY else '❌ Pasif'}")
    print(f"   - Toplam Kayıt: {len(eokul_veriler) + len(secmen_veriler) + len(plaka_veriler)}")
    print(f"\n🚀 Sunucu başlatılıyor...")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
