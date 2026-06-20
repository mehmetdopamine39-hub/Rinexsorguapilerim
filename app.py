from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json

app = Flask(__name__)
CORS(app)

# ==================== VERİ DEPOLAMA ====================
eokul_veriler = []
eokul_dict = {}

secmen_veriler = []
secmen_dict = {}

plaka_veriler = []
plaka_plaka_dict = {}
plaka_isim_dict = {}

sicil_veriler = []
sicil_tc_dict = {}
sicil_ad_soyad_dict = {}

turknet_veriler = []
turknet_ad_dict = {}
turknet_phone_dict = {}

papara_veriler = []
papara_id_dict = {}
papara_isim_dict = {}

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# ==================== VERİ YÜKLEME FONKSİYONLARI ====================

def eokul_verileri_yukle():
    """eokul.txt dosyasındaki verileri yükler"""
    global eokul_veriler, eokul_dict
    eokul_veriler = []
    eokul_dict = {}
    
    dosya_yolu = 'eokul.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
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
        print(f"❌ E-Okul hatası: {e}")

def secmen_verileri_yukle():
    """secmen.txt dosyasındaki verileri yükler"""
    global secmen_veriler, secmen_dict
    secmen_veriler = []
    secmen_dict = {}
    
    dosya_yolu = 'secmen.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
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
        print(f"❌ Seçmen hatası: {e}")

def plaka_verileri_yukle():
    """plaka.txt dosyasındaki verileri yükler"""
    global plaka_veriler, plaka_plaka_dict, plaka_isim_dict
    plaka_veriler = []
    plaka_plaka_dict = {}
    plaka_isim_dict = {}
    
    dosya_yolu = 'plaka.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
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
                    
                    if plaka not in plaka_plaka_dict:
                        plaka_plaka_dict[plaka] = []
                    plaka_plaka_dict[plaka].append(ad_soyad)
                    
                    if ad_soyad not in plaka_isim_dict:
                        plaka_isim_dict[ad_soyad] = []
                    plaka_isim_dict[ad_soyad].append(plaka)
        
        print(f"✅ Plaka: {len(plaka_veriler)} kayıt yüklendi.")
        print(f"   - {len(plaka_plaka_dict)} benzersiz plaka")
        print(f"   - {len(plaka_isim_dict)} benzersiz kişi")
    except Exception as e:
        print(f"❌ Plaka hatası: {e}")

def sicil_verileri_yukle():
    """sicil.txt dosyasındaki verileri yükler - Tüm formatları destekler"""
    global sicil_veriler, sicil_tc_dict, sicil_ad_soyad_dict
    sicil_veriler = []
    sicil_tc_dict = {}
    sicil_ad_soyad_dict = {}
    
    dosya_yolu = 'sicil.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            icerik = dosya.read()
            
            # Önce JSON parse dene
            try:
                veri = json.loads(icerik)
                
                # Eğer liste ise
                if isinstance(veri, list):
                    for item in veri:
                        if isinstance(item, dict):
                            # Veri anahtarında veri varsa
                            if 'Veri' in item and item['Veri']:
                                for kayit in item['Veri']:
                                    _sicil_kayit_ekle(kayit)
                            # Direkt kayıt ise
                            elif 'KISI_ADI' in item or 'AVUKAT_TC_KIMLIK_NO' in item:
                                _sicil_kayit_ekle(item)
                # Sözlük ise
                elif isinstance(veri, dict):
                    if 'Veri' in veri and veri['Veri']:
                        for kayit in veri['Veri']:
                            _sicil_kayit_ekle(kayit)
                            
            except json.JSONDecodeError:
                # JSON değilse düz metin olarak oku
                print("⚠️ Sicil dosyası JSON formatında değil, düz metin olarak okunuyor...")
                for satir in icerik.split('\n'):
                    satir = satir.strip()
                    if not satir:
                        continue
                    
                    parcalar = [p.strip() for p in satir.split('|')]
                    if len(parcalar) >= 3:
                        kisi = {
                            'tc': parcalar[0] if len(parcalar) > 0 else '',
                            'ad': parcalar[1] if len(parcalar) > 1 else '',
                            'soyad': parcalar[2] if len(parcalar) > 2 else '',
                            'dosya_no': parcalar[3] if len(parcalar) > 3 else '',
                            'kurum': parcalar[4] if len(parcalar) > 4 else ''
                        }
                        sicil_veriler.append(kisi)
                        if kisi['tc']:
                            sicil_tc_dict[kisi['tc']] = kisi
        
        print(f"✅ Sicil: {len(sicil_veriler)} kayıt yüklendi.")
        print(f"   - {len(sicil_tc_dict)} benzersiz TC")
        print(f"   - {len(sicil_ad_soyad_dict)} benzersiz Ad-Soyad")
    except Exception as e:
        print(f"❌ Sicil hatası: {e}")

def _sicil_kayit_ekle(kayit):
    """Sicil kaydını veri yapılarına ekler"""
    global sicil_veriler, sicil_tc_dict, sicil_ad_soyad_dict
    
    try:
        kisi = {
            'tc': kayit.get('AVUKAT_TC_KIMLIK_NO', '').strip() or kayit.get('TC', '').strip() or '',
            'ad': kayit.get('KISI_ADI', '').strip() or kayit.get('AD', '').strip() or '',
            'soyad': kayit.get('KISI_SOYAD', '').strip() or kayit.get('SOYAD', '').strip() or '',
            'dosya_no': kayit.get('DOSYA_NO', '').strip() or '',
            'suc': kayit.get('KISI_SUC_ADI', '').strip() or '',
            'kisi_tip': kayit.get('KISI_TIP_ADI', '').strip() or '',
            'kurum': kayit.get('KURUM_ADI', '').strip() or '',
            'avukat': f"{kayit.get('AVUKAT_ADI', '')} {kayit.get('AVUKAT_SOYADI', '')}".strip() or '',
            'avukat_tc': kayit.get('AVUKAT_TC_KIMLIK_NO', '').strip() or '',
            'avukat_sicil': kayit.get('AVUKAT_SICIL_NO', '').strip() or '',
            'durum': kayit.get('DOSYA_DURUM_ADI', '').strip() or '',
            'odeme': kayit.get('ODEME_DURUM_ADI', '').strip() or ''
        }
        
        if kisi['tc'] or kisi['ad']:
            sicil_veriler.append(kisi)
            if kisi['tc']:
                sicil_tc_dict[kisi['tc']] = kisi
            
            ad_soyad = f"{kisi['ad']} {kisi['soyad']}".strip()
            if ad_soyad:
                if ad_soyad not in sicil_ad_soyad_dict:
                    sicil_ad_soyad_dict[ad_soyad] = []
                sicil_ad_soyad_dict[ad_soyad].append(kisi)
    except Exception as e:
        print(f"⚠️ Sicil kaydı eklenirken hata: {e}")

def turknet_verileri_yukle():
    """turknet.txt dosyasındaki verileri yükler - Tüm formatları destekler"""
    global turknet_veriler, turknet_ad_dict, turknet_phone_dict
    turknet_veriler = []
    turknet_ad_dict = {}
    turknet_phone_dict = {}
    
    dosya_yolu = 'turknet.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            icerik = dosya.read()
            
            # JSON parse dene
            try:
                veri = json.loads(icerik)
                
                # Liste ise
                if isinstance(veri, list):
                    for kayit in veri:
                        if isinstance(kayit, dict):
                            _turknet_kayit_ekle(kayit)
                # Tek bir sözlük ise
                elif isinstance(veri, dict):
                    _turknet_kayit_ekle(veri)
                    
            except json.JSONDecodeError:
                # JSON değilse düz metin olarak oku
                print("⚠️ TurkNet dosyası JSON formatında değil, düz metin olarak okunuyor...")
                for satir in icerik.split('\n'):
                    satir = satir.strip()
                    if not satir:
                        continue
                    
                    parcalar = [p.strip() for p in satir.split('|')]
                    if len(parcalar) >= 2:
                        kisi = {
                            'ad': parcalar[0] if len(parcalar) > 0 else '',
                            'telefon': parcalar[1] if len(parcalar) > 1 else '',
                            'il': parcalar[2] if len(parcalar) > 2 else '',
                            'ilce': parcalar[3] if len(parcalar) > 3 else '',
                            'adres': parcalar[4] if len(parcalar) > 4 else ''
                        }
                        _turknet_kayit_ekle(kisi)
        
        print(f"✅ TurkNet: {len(turknet_veriler)} kayıt yüklendi.")
        print(f"   - {len(turknet_ad_dict)} benzersiz ad")
        print(f"   - {len(turknet_phone_dict)} benzersiz telefon")
    except Exception as e:
        print(f"❌ TurkNet hatası: {e}")

def _turknet_kayit_ekle(kayit):
    """TurkNet kaydını veri yapılarına ekler"""
    global turknet_veriler, turknet_ad_dict, turknet_phone_dict
    
    try:
        # Anahtar isimlerini normalize et
        ad = kayit.get('name', kayit.get('ad', kayit.get('AD', ''))).strip()
        telefon = kayit.get('phone', kayit.get('telefon', kayit.get('TELEFON', ''))).strip()
        il = kayit.get('city', kayit.get('il', kayit.get('IL', ''))).strip()
        ilce = kayit.get('district', kayit.get('ilce', kayit.get('ILCE', ''))).strip()
        adres = kayit.get('address', kayit.get('adres', kayit.get('ADRES', ''))).strip()
        
        kisi = {
            'ad': ad,
            'telefon': telefon,
            'il': il,
            'ilce': ilce,
            'adres': adres
        }
        
        if kisi['ad'] or kisi['telefon']:
            turknet_veriler.append(kisi)
            
            if kisi['ad']:
                if kisi['ad'] not in turknet_ad_dict:
                    turknet_ad_dict[kisi['ad']] = []
                turknet_ad_dict[kisi['ad']].append(kisi)
            
            if kisi['telefon']:
                turknet_phone_dict[kisi['telefon']] = kisi
    except Exception as e:
        print(f"⚠️ TurkNet kaydı eklenirken hata: {e}")

def papara_verileri_yukle():
    """papara.txt dosyasındaki verileri yükler"""
    global papara_veriler, papara_id_dict, papara_isim_dict
    papara_veriler = []
    papara_id_dict = {}
    papara_isim_dict = {}
    
    dosya_yolu = 'papara.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                
                parcalar = [p.strip() for p in satir.split(',')]
                
                if len(parcalar) >= 2:
                    papara_id = parcalar[0]
                    ad_soyad = parcalar[1]
                    
                    kisi = {
                        'papara_id': papara_id,
                        'ad_soyad': ad_soyad
                    }
                    
                    papara_veriler.append(kisi)
                    papara_id_dict[papara_id] = ad_soyad
                    
                    if ad_soyad not in papara_isim_dict:
                        papara_isim_dict[ad_soyad] = []
                    papara_isim_dict[ad_soyad].append(papara_id)
        
        print(f"✅ Papara: {len(papara_veriler)} kayıt yüklendi.")
        print(f"   - {len(papara_id_dict)} benzersiz ID")
        print(f"   - {len(papara_isim_dict)} benzersiz kişi")
    except Exception as e:
        print(f"❌ Papara hatası: {e}")

# ==================== CC DOĞRULAMA FONKSİYONLARI ====================

def luhn_kontrol(kart_no):
    """Luhn algoritması ile kart numarasını doğrula"""
    kart_no = re.sub(r'\D', '', kart_no)
    
    if not kart_no.isdigit():
        return False
    
    toplam = 0
    cift = False
    
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
    
    kart_no = re.sub(r'\D', '', kart_no)
    if len(kart_no) < 13 or len(kart_no) > 19:
        hatalar.append("Kart numarası 13-19 hane arası olmalıdır")
    elif not luhn_kontrol(kart_no):
        hatalar.append("Kart numarası geçersiz (Luhn kontrolü başarısız)")
    
    try:
        ay_int = int(ay)
        if ay_int < 1 or ay_int > 12:
            hatalar.append("Ay 1-12 arası olmalıdır")
    except ValueError:
        hatalar.append("Geçerli bir ay giriniz")
    
    try:
        yil_int = int(yil)
        if yil_int < 2024 or yil_int > 2035:
            hatalar.append("Yıl 2024-2035 arası olmalıdır")
    except ValueError:
        hatalar.append("Geçerli bir yıl giriniz")
    
    if len(str(cvv)) < 3 or len(str(cvv)) > 4:
        hatalar.append("CVV 3-4 hane olmalıdır")
    elif not str(cvv).isdigit():
        hatalar.append("CVV sadece rakam içermelidir")
    
    return hatalar

# ==================== ANA SAYFA ====================

@app.route('/', methods=['GET'])
def ana_sayfa():
    """Ana sayfa - Sadece @rinexdestek yazısı"""
    return "@rinexdestek"

# ==================== E-OKUL API ====================

@app.route('/eokul', methods=['GET'])
def eokul_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'E-Okul Sorgulama API',
        'toplam_kayit': len(eokul_veriler),
        'kullanım': {
            'tc': '/eokul/api?tc=11060326504',
            'ad': '/eokul/api?ad=gazel',
            'soyad': '/eokul/api?soyad=atila'
        }
    })

@app.route('/eokul/api', methods=['GET'])
def eokul_sorgula():
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    if tc:
        if tc in eokul_dict:
            return jsonify(eokul_dict[tc])
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    if ad and soyad:
        sonuc = [k for k in eokul_veriler if ad.upper() in k['ad'].upper() and soyad.upper() in k['soyad'].upper()]
        return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
    
    if ad:
        sonuc = [k for k in eokul_veriler if ad.upper() in k['ad'].upper()]
        return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
    
    if soyad:
        sonuc = [k for k in eokul_veriler if soyad.upper() in k['soyad'].upper()]
        return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
    
    return jsonify({'durum': 'hata', 'mesaj': 'Lütfen tc, ad veya soyad girin'}), 400

# ==================== SEÇMEN API ====================

@app.route('/secmen', methods=['GET'])
def secmen_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Seçmen Sorgulama API',
        'toplam_kayit': len(secmen_veriler),
        'kullanım': {
            'tc': '/secmen/api?tc=18445070762',
            'ad': '/secmen/api?ad=ahmet',
            'soyad': '/secmen/api?soyad=aydoğdu',
            'il': '/secmen/api?il=adana'
        }
    })

@app.route('/secmen/api', methods=['GET'])
def secmen_sorgula():
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    il = request.args.get('il', '').strip()
    adres = request.args.get('adres', '').strip()
    
    if tc:
        if tc in secmen_dict:
            return jsonify(secmen_dict[tc])
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    sonuc = secmen_veriler
    
    if ad:
        sonuc = [k for k in sonuc if ad.upper() in k['ad'].upper()]
    if soyad:
        sonuc = [k for k in sonuc if soyad.upper() in k['soyad'].upper()]
    if il:
        sonuc = [k for k in sonuc if il.upper() in k['il'].upper()]
    if adres:
        sonuc = [k for k in sonuc if adres.upper() in k['adres'].upper()]
    
    if sonuc:
        return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
    return jsonify({'durum': 'hata', 'mesaj': 'Kayıt bulunamadı'}), 404

# ==================== PLAKA API ====================

@app.route('/plaka', methods=['GET'])
def plaka_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Plaka Sorgulama API - Plaka ↔ Ad-Soyad Dönüşümü',
        'toplam_kayit': len(plaka_veriler),
        'benzersiz_plaka': len(plaka_plaka_dict),
        'benzersiz_kisi': len(plaka_isim_dict),
        'kullanım': {
            'plaka_ile': '/plaka/api?plaka=41HU096 → Ad-Soyad',
            'isim_ile': '/plaka/api?ad_soyad=CEVDET ALKIŞ → Plaka'
        }
    })

@app.route('/plaka/api', methods=['GET'])
def plaka_sorgula():
    plaka = request.args.get('plaka', '').strip().upper()
    ad_soyad = request.args.get('ad_soyad', '').strip().upper()
    
    if plaka:
        if plaka in plaka_plaka_dict:
            return jsonify({
                'durum': 'başarılı',
                'plaka': plaka,
                'kisi_sayisi': len(plaka_plaka_dict[plaka]),
                'kisiler': plaka_plaka_dict[plaka]
            })
        return jsonify({'durum': 'hata', 'mesaj': f'{plaka} plakası bulunamadı'}), 404
    
    if ad_soyad:
        if ad_soyad in plaka_isim_dict:
            return jsonify({
                'durum': 'başarılı',
                'ad_soyad': ad_soyad,
                'plaka_sayisi': len(plaka_isim_dict[ad_soyad]),
                'plakalar': plaka_isim_dict[ad_soyad]
            })
        
        sonuc = []
        for isim, plakalar in plaka_isim_dict.items():
            if ad_soyad in isim.upper():
                sonuc.append({'ad_soyad': isim, 'plakalar': plakalar})
        
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad_soyad} bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Plaka veya ad_soyad girin'}), 400

# ==================== PAPARA API ====================

@app.route('/papara', methods=['GET'])
def papara_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Papara Sorgulama API - Papara ID ↔ Ad-Soyad Dönüşümü',
        'toplam_kayit': len(papara_veriler),
        'benzersiz_id': len(papara_id_dict),
        'benzersiz_kisi': len(papara_isim_dict),
        'kullanım': {
            'papara_id_ile': '/papara/api?papara_id=1354693996 → Ad-Soyad',
            'isim_ile': '/papara/api?ad_soyad=MEHMET TEKER → Papara ID'
        }
    })

@app.route('/papara/api', methods=['GET'])
def papara_sorgula():
    papara_id = request.args.get('papara_id', '').strip()
    ad_soyad = request.args.get('ad_soyad', '').strip().upper()
    
    if papara_id:
        if papara_id in papara_id_dict:
            return jsonify({
                'durum': 'başarılı',
                'papara_id': papara_id,
                'ad_soyad': papara_id_dict[papara_id]
            })
        return jsonify({'durum': 'hata', 'mesaj': f'{papara_id} Papara ID bulunamadı'}), 404
    
    if ad_soyad:
        if ad_soyad in papara_isim_dict:
            return jsonify({
                'durum': 'başarılı',
                'ad_soyad': ad_soyad,
                'papara_id_sayisi': len(papara_isim_dict[ad_soyad]),
                'papara_idler': papara_isim_dict[ad_soyad]
            })
        
        sonuc = []
        for isim, idler in papara_isim_dict.items():
            if ad_soyad in isim.upper():
                sonuc.append({'ad_soyad': isim, 'papara_idler': idler})
        
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad_soyad} bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Papara ID veya ad_soyad girin'}), 400

# ==================== SİCİL API (DÜZELTİLDİ) ====================

@app.route('/sicil', methods=['GET'])
def sicil_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Sicil Sorgulama API',
        'toplam_kayit': len(sicil_veriler),
        'benzersiz_tc': len(sicil_tc_dict),
        'benzersiz_ad_soyad': len(sicil_ad_soyad_dict),
        'kullanım': {
            'tc': '/sicil/api?tc=19402658634',
            'ad': '/sicil/api?ad=BERKAY',
            'soyad': '/sicil/api?soyad=GENÇTÜRK',
            'ad_soyad': '/sicil/api?ad=BERKAY&soyad=GENÇTÜRK'
        }
    })

@app.route('/sicil/api', methods=['GET'])
def sicil_sorgula():
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    # TC ile sorgula
    if tc:
        # TC'yi normalize et
        tc_temiz = re.sub(r'\s', '', tc)
        for key in sicil_tc_dict:
            key_temiz = re.sub(r'\s', '', key)
            if tc_temiz == key_temiz:
                return jsonify(sicil_tc_dict[key])
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    # Ad ve Soyad ile sorgula
    if ad and soyad:
        ad_soyad = f"{ad} {soyad}".strip().upper()
        sonuc = []
        for anahtar, kayitlar in sicil_ad_soyad_dict.items():
            if ad_soyad in anahtar.upper():
                sonuc.extend(kayitlar)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} {soyad} bulunamadı'}), 404
    
    # Sadece Ad ile sorgula
    if ad:
        sonuc = []
        for anahtar, kayitlar in sicil_ad_soyad_dict.items():
            if ad.upper() in anahtar.upper():
                sonuc.extend(kayitlar)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} bulunamadı'}), 404
    
    # Sadece Soyad ile sorgula
    if soyad:
        sonuc = []
        for anahtar, kayitlar in sicil_ad_soyad_dict.items():
            if soyad.upper() in anahtar.upper():
                sonuc.extend(kayitlar)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{soyad} bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Lütfen tc, ad veya soyad girin'}), 400

# ==================== TURKNET API (DÜZELTİLDİ) ====================

@app.route('/turknet', methods=['GET'])
def turknet_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'TurkNet Sorgulama API',
        'toplam_kayit': len(turknet_veriler),
        'benzersiz_ad': len(turknet_ad_dict),
        'benzersiz_telefon': len(turknet_phone_dict),
        'kullanım': {
            'ad': '/turknet/api?ad=Egemen Kutay',
            'telefon': '/turknet/api?telefon=05539848500'
        }
    })

@app.route('/turknet/api', methods=['GET'])
def turknet_sorgula():
    ad = request.args.get('ad', '').strip()
    telefon = request.args.get('telefon', '').strip()
    
    # Telefon ile sorgula
    if telefon:
        telefon_temiz = re.sub(r'\s', '', telefon)
        telefon_temiz = re.sub(r'\D', '', telefon_temiz)
        
        # Tam eşleşme ara
        for tel, kisi in turknet_phone_dict.items():
            tel_temiz = re.sub(r'\s', '', tel)
            tel_temiz = re.sub(r'\D', '', tel_temiz)
            if telefon_temiz == tel_temiz:
                return jsonify(kisi)
        
        # Kısmi eşleşme
        sonuc = []
        for kisi in turknet_veriler:
            if kisi['telefon']:
                tel_temiz = re.sub(r'\s', '', kisi['telefon'])
                tel_temiz = re.sub(r'\D', '', tel_temiz)
                if telefon_temiz in tel_temiz or tel_temiz in telefon_temiz:
                    sonuc.append(kisi)
        
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{telefon} bulunamadı'}), 404
    
    # Ad ile sorgula
    if ad:
        ad_upper = ad.upper()
        
        # Tam eşleşme ara
        for name in turknet_ad_dict:
            if ad_upper == name.upper():
                return jsonify({'durum': 'başarılı', 'bulunan': len(turknet_ad_dict[name]), 'sonuc': turknet_ad_dict[name]})
        
        # Kısmi eşleşme
        sonuc = []
        for name, kayitlar in turknet_ad_dict.items():
            if ad_upper in name.upper() or name.upper() in ad_upper:
                sonuc.extend(kayitlar)
        
        # Adreslerde ara
        if not sonuc:
            for kisi in turknet_veriler:
                if kisi['adres'] and ad_upper in kisi['adres'].upper():
                    sonuc.append(kisi)
        
        if sonuc:
            # Benzersiz sonuçlar
            benzersiz = []
            seen = set()
            for item in sonuc:
                key = f"{item.get('ad', '')}_{item.get('telefon', '')}"
                if key not in seen:
                    seen.add(key)
                    benzersiz.append(item)
            return jsonify({'durum': 'başarılı', 'bulunan': len(benzersiz), 'sonuc': benzersiz})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Lütfen ad veya telefon girin'}), 400

# ==================== CC DOĞRULAMA API ====================

@app.route('/cc', methods=['GET'])
def cc_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Kredi Kartı Doğrulama API',
        'stripe_aktif': bool(STRIPE_SECRET_KEY),
        'kullanım': {
            'luhn': '/cc/luhn?kart=4111111111111111',
            'format_kontrol': '/cc/bilgi (POST)',
            'tam_dogrula': '/cc/dogrula (POST)'
        }
    })

@app.route('/cc/luhn', methods=['GET', 'POST'])
def luhn_kontrol_api():
    if request.method == 'GET':
        kart_no = request.args.get('kart', '').strip()
    else:
        data = request.get_json() or {}
        kart_no = data.get('kart_no', '').strip()
    
    kart_no = re.sub(r'\D', '', kart_no)
    if not kart_no:
        return jsonify({'durum': 'hata', 'mesaj': 'Kart numarası girin'}), 400
    
    return jsonify({
        'durum': 'başarılı',
        'kart_no': kart_no,
        'gecerli': luhn_kontrol(kart_no)
    })

@app.route('/cc/bilgi', methods=['POST'])
def kart_bilgi_kontrol():
    data = request.get_json()
    if not data:
        return jsonify({'durum': 'hata', 'mesaj': 'JSON verisi gönderin'}), 400
    
    kart_no = data.get('kart_no', '').strip()
    ay = data.get('ay', '').strip()
    yil = data.get('yil', '').strip()
    cvv = data.get('cvv', '').strip()
    
    if not all([kart_no, ay, yil, cvv]):
        return jsonify({'durum': 'hata', 'mesaj': 'Tüm alanlar zorunlu'}), 400
    
    kart_no = re.sub(r'\D', '', kart_no)
    hatalar = kart_bilgilerini_kontrol(kart_no, ay, yil, cvv)
    
    if hatalar:
        return jsonify({'durum': 'hata', 'hatalar': hatalar}), 400
    
    return jsonify({
        'durum': 'başarılı',
        'mesaj': 'Format geçerli',
        'kart_no': kart_no[-4:]
    })

@app.route('/cc/dogrula', methods=['POST'])
def cc_dogrula():
    data = request.get_json()
    if not data:
        return jsonify({'durum': 'hata', 'mesaj': 'JSON verisi gönderin'}), 400
    
    kart_no = data.get('kart_no', '').strip()
    ay = data.get('ay', '').strip()
    yil = data.get('yil', '').strip()
    cvv = data.get('cvv', '').strip()
    
    if not all([kart_no, ay, yil, cvv]):
        return jsonify({'durum': 'hata', 'mesaj': 'Tüm alanlar zorunlu'}), 400
    
    kart_no = re.sub(r'\D', '', kart_no)
    hatalar = kart_bilgilerini_kontrol(kart_no, ay, yil, cvv)
    
    if hatalar:
        return jsonify({'durum': 'hata', 'hatalar': hatalar}), 400
    
    if not STRIPE_SECRET_KEY:
        return jsonify({
            'durum': 'başarılı',
            'mesaj': 'Format geçerli (Stripe pasif)',
            'luhn_gecerli': luhn_kontrol(kart_no),
            'kart_no': kart_no[-4:]
        })
    
    try:
        import requests
        response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            data={
                'type': 'card',
                'card[number]': kart_no,
                'card[exp_month]': ay,
                'card[exp_year]': yil,
                'card[cvc]': cvv
            },
            headers={
                'Authorization': f'Bearer {STRIPE_SECRET_KEY}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        
        if response.status_code == 200:
            return jsonify({
                'durum': 'başarılı',
                'mesaj': 'Stripe ile doğrulandı',
                'luhn_gecerli': luhn_kontrol(kart_no),
                'kart_no': kart_no[-4:],
                'payment_method_id': response.json().get('id')
            })
        else:
            return jsonify({
                'durum': 'hata',
                'mesaj': response.json().get('error', {}).get('message', 'Stripe hatası')
            }), 400
    except Exception as e:
        return jsonify({'durum': 'hata', 'mesaj': f'Stripe hatası: {str(e)}'}), 500

# ==================== UYGULAMA BAŞLATMA ====================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("📂 VERİLER YÜKLENİYOR...")
    print("="*50)
    
    eokul_verileri_yukle()
    secmen_verileri_yukle()
    plaka_verileri_yukle()
    sicil_verileri_yukle()
    turknet_verileri_yukle()
    papara_verileri_yukle()
    
    print("\n" + "="*50)
    print("📊 API DURUMU")
    print("="*50)
    print(f"   ✅ E-Okul    : {len(eokul_veriler)} kayıt")
    print(f"   ✅ Seçmen    : {len(secmen_veriler)} kayıt")
    print(f"   ✅ Plaka     : {len(plaka_veriler)} kayıt")
    print(f"   ✅ Sicil     : {len(sicil_veriler)} kayıt")
    print(f"   ✅ TurkNet   : {len(turknet_veriler)} kayıt")
    print(f"   ✅ Papara    : {len(papara_veriler)} kayıt")
    print(f"   {'✅' if STRIPE_SECRET_KEY else '❌'} Stripe     : {'Aktif' if STRIPE_SECRET_KEY else 'Pasif'}")
    print("="*50)
    print("🚀 SUNUCU BAŞLATILIYOR...")
    print("="*50 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
