import os
import subprocess
import telebot
import signal
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Quản lý trạng thái quét
scan_process = None
found_ips = []
current_config = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🎮 <b>BẢNG ĐIỀU KHIỂN MASSCAN</b>\n\n"
        "/scan - Thiết lập cấu hình và bắt đầu quét\n"
        "/stop - Dừng quét ngay lập tức\n"
        "/status - Kiểm tra trạng thái hiện tại\n"
        "/list - In danh sách IP tìm thấy\n"
        "/clear - Xóa danh sách IP cũ"
    )
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['scan'])
def ask_config(message):
    msg = bot.send_message(message.chat.id, "1️⃣ Nhập IP/Dải IP (VD: 1.2.3.4 hoặc 1.2.3.0/24):")
    bot.register_next_step_handler(msg, step_port)

def step_port(message):
    current_config['ip'] = message.text
    msg = bot.send_message(message.chat.id, "2️⃣ Nhập Port (VD: 3389):")
    bot.register_next_step_handler(msg, step_rate)

def step_rate(message):
    current_config['port'] = message.text
    msg = bot.send_message(message.chat.id, "3️⃣ Nhập Rate (Tốc độ, VD: 5000):")
    bot.register_next_step_handler(msg, execute_scan)

def execute_scan(message):
    global scan_process, found_ips
    rate = message.text
    ip = current_config['ip']
    port = current_config['port']
    
    if scan_process and scan_process.poll() is None:
        bot.reply_to(message, "⚠️ Một tiến trình quét đang chạy. Hãy gõ /stop trước!")
        return

    bot.send_message(message.chat.id, f"🚀 <b>Bắt đầu quét...</b>\nIP: {ip}\nPort: {port}\nRate: {rate}", parse_mode="HTML")
    
    cmd = f"masscan {ip} -p{port} --rate {rate} --wait 0 -oL -"
    
    try:
        scan_process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, text=True, preexec_fn=os.setsid)
        
        for line in scan_process.stdout:
            if "open" in line:
                parts = line.split()
                ip_res = parts[3]
                found_ips.append(f"{ip_res}:{port}")
                bot.send_message(message.chat.id, f"✅ Found: <code>{ip_res}:{port}</code>", parse_mode="HTML")
        
        scan_process.wait()
        bot.send_message(message.chat.id, "🏁 Quét hoàn tất!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Lỗi: {str(e)}")

@bot.message_handler(commands=['stop'])
def stop_scan(message):
    global scan_process
    if scan_process and scan_process.poll() is None:
        os.killpg(os.getpgid(scan_process.pid), signal.SIGTERM)
        bot.reply_to(message, "🛑 Đã dừng tiến trình quét.")
    else:
        bot.reply_to(message, "Hiện không có tiến trình nào đang chạy.")

@bot.message_handler(commands=['list'])
def list_ips(message):
    if not found_ips:
        bot.reply_to(message, "Danh sách trống.")
        return
    
    report = "📋 <b>DANH SÁCH IP MỞ CỔNG:</b>\n\n" + "\n".join(found_ips)
    if len(report) > 4096: # Giới hạn tin nhắn Telegram
        with open("results.txt", "w") as f:
            f.write("\n".join(found_ips))
        bot.send_document(message.chat.id, open("results.txt", "rb"))
    else:
        bot.send_message(message.chat.id, report, parse_mode="HTML")

@bot.message_handler(commands=['clear'])
def clear_list(message):
    global found_ips
    found_ips = []
    bot.reply_to(message, "🗑 Đã xóa danh sách IP đã tìm thấy.")

bot.polling()
