import threading
import telebot
import requests
import json
import os
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8797770726:AAGHJvpFtm2_x5CD6bvLWfmregFRvvD-OPU"
bot = telebot.TeleBot(TOKEN)

try:
    bot.remove_webhook()
except:
    pass

HISTORY_FILE = "history.json"
user_state = {}  

SERVICES = {
    "turar": {
        "name": "🏠 Turar joylar",
        "url": "https://db.ngis.uz/db/rest/services/UZKAD/TURAR_UZKAD_DB16/MapServer/0/query"
    },
    "noturar": {
        "name": "🏢 Noturar joylar",
        "url": "https://db.ngis.uz/db/rest/services/UZKAD/NOTURAR_UZKAD_DB16/MapServer/0/query"
    },
    "agr": {
        "name": "🌾 Qishloq xo'jaligi yerlari",
        "url": "https://db.ngis.uz/db/rest/services/UZKAD/AGR_ONLY_UZKAD_DB16/MapServer/0/query"
    }
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_history(user_id, cadastre_number, category):
    history = load_history()
    str_user_id = str(user_id)
    if str_user_id not in history:
        history[str_user_id] = []
        
    entry = {
        "cadastre_number": cadastre_number,
        "category": category,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    history[str_user_id].append(entry)
        
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def create_kml(feature, cadastre_number):
    geometry = feature.get('geometry', {})
    rings = geometry.get('rings', [])
    
    if not rings:
        return None
        
    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Kadastr: {cadastre_number}</name>
    <Placemark>
      <name>{cadastre_number}</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
"""
    for ring in rings:
        for coord in ring:
            kml_content += f"              {coord[0]},{coord[1]},0\n"
            
    kml_content += """            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""
    filename = f"cadastre_{cadastre_number.replace(':', '_')}.kml"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(kml_content)
    return filename

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🔍 Qidirish"),
        KeyboardButton("📜 Tarix")
    )
    return markup

def get_categories_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🏠 Turar joylar"),
        KeyboardButton("🏢 Noturar joylar"),
        KeyboardButton("🌾 Qishloq xo'jaligi yerlari"),
        KeyboardButton("🔙 Orqaga qaytish")
    )
    return markup

def get_input_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🔙 Kategoriyalarga qaytish"),
        KeyboardButton("🔄 Qaytadan boshlash")
    )
    return markup

def get_result_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🔄 Qaytadan boshlash"),
        KeyboardButton("📜 Tarix")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_state[chat_id] = None
    welcome_text = (
        "Assalomu alaykum! 🏛\n\n"
        "Elektron kadastr ma'lumotlar botiga xush kelibsiz.\n"
        "Kerakli bo'limni tanlang:"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔄 Qaytadan boshlash")
def restart_bot(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == "🔍 Qidirish")
def start_search(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Bo'limni tanlang:", reply_markup=get_categories_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔙 Orqaga qaytish")
def go_back_main(message):
    chat_id = message.chat.id
    user_state[chat_id] = None
    bot.send_message(chat_id, "Asosiy menyu:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔙 Kategoriyalarga qaytish")
def go_back_categories(message):
    chat_id = message.chat.id
    user_state[chat_id] = None
    bot.send_message(chat_id, "Kategoriyani tanlang:", reply_markup=get_categories_keyboard())

@bot.message_handler(func=lambda message: message.text == "📜 Tarix")
def show_history(message):
    chat_id = message.chat.id
    history = load_history()
    str_user_id = str(chat_id)
    
    if str_user_id in history and history[str_user_id]:
        text = "📜 *Sizning qidiruvlar tarixingiz:*\n\n"
        for idx, item in enumerate(history[str_user_id], 1):
            text += f"{idx}. `{item['cadastre_number']}` ({item.get('category', '-')}) — _{item['date']}_\n"
    else:
        text = "Sizda hali qidiruvlar tarixi mavjud emas."
        
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=get_result_keyboard())

@bot.message_handler(func=lambda message: message.text in ["🏠 Turar joylar", "🏢 Noturar joylar", "🌾 Qishloq xo'jaligi yerlari"])
def set_category(message):
    chat_id = message.chat.id
    text = message.text
    
    if "Turar" in text:
        user_state[chat_id] = "turar"
        cat_name = "🏠 Turar joylar"
    elif "Noturar" in text:
        user_state[chat_id] = "noturar"
        cat_name = "🏢 Noturar joylar"
    else:
        user_state[chat_id] = "agr"
        cat_name = "🌾 Qishloq xo'jaligi yerlari"
        
    bot.send_message(
        chat_id, 
        f"✅ *{cat_name}* tanlandi.\n\nEndi ushbu bo'limga tegishli kadastr raqamini kiriting (masalan: `14:07:42:03:01:0443`):", 
        parse_mode='Markdown',
        reply_markup=get_input_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_cadastre(message):
    chat_id = message.chat.id
    cadastre_number = message.text.strip()
    
    current_category = user_state.get(chat_id)
    
    if not current_category:
        bot.send_message(chat_id, "⚠️ Iltimos, avval '🔍 Qidirish' tugmasini bosing:", reply_markup=get_main_keyboard())
        return

    api_url = SERVICES[current_category]["url"]
    cat_title = SERVICES[current_category]["name"]
    
    bot.send_message(chat_id, f"🔍 {cat_title} bazasidan '{cadastre_number}' qidirilmoqda...", reply_markup=get_input_keyboard())
    
    threading.Thread(target=process_cadastre_request, args=(chat_id, cadastre_number, api_url, cat_title)).start()

def process_cadastre_request(chat_id, cadastre_number, api_url, cat_title):
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://db.ngis.uz/'
    }
    
    # Server qotib qolmasligi uchun aniq tenglik (=) sharti ishlatiladi
    params = {
        'where': f"cadastral_number = '{cadastre_number}' OR kadastr = '{cadastre_number}' OR cad_num = '{cadastre_number}'",
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'outSR': '4326',
        'resultRecordCount': 1
    }
    
    try:
        response = session.get(api_url, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            bot.send_message(chat_id, f"[!] Server xato kod qaytardi: HTTP {response.status_code}", reply_markup=get_result_keyboard())
            return
            
        data = response.json()
        
        if 'error' in data:
            err_msg = data['error'].get('message', 'ArcGIS xatosi')
            bot.send_message(chat_id, f"[!] Server xabari: {err_msg}", reply_markup=get_result_keyboard())
            return
        
        if 'features' in data and len(data['features']) > 0:
            feature = data['features'][0]
            attr = feature.get('attributes', {})
            
            c_num = attr.get('cadastral_number', attr.get('kadastr', cadastre_number))
            viloyat = attr.get('region_name', attr.get('viloyat', '-'))
            tuman = attr.get('district_name', attr.get('tuman', '-'))
            mahalla_nomi = attr.get('mahalla_name', attr.get('mahalla', '-'))
            mahalla_kodi = attr.get('mahalla_code', '-')
            maqsadi = attr.get('land_fund_type_description', attr.get('purpose_description', 'Aniqlanmagan'))
            
            text_result = (
                f"📋 *KADASTR MA'LUMOTLARI* ({cat_title})\n"
                "──────────────────────────────\n"
                f"🏷 *Kadastr raqami:* `{c_num}`\n"
                f"🗺 *Viloyat:* {viloyat}\n"
                f"🏛 *Tuman:* {tuman}\n"
                f"🏘 *Mahalla:* {mahalla_nomi}\n"
                f"🔑 *Mahalla kodi:* `{mahalla_kodi}`\n"
                f"🎯 *Maqsadi:* {maqsadi}\n"
                "──────────────────────────────"
            )
            
            bot.send_message(chat_id, text_result, parse_mode='Markdown', reply_markup=get_result_keyboard())
            save_history(chat_id, cadastre_number, cat_title)
            
            kml_file = create_kml(feature, cadastre_number)
            if kml_file and os.path.exists(kml_file):
                with open(kml_file, 'rb') as f:
                    bot.send_document(chat_id, f, caption="Xaritadagi kml fayli", reply_markup=get_result_keyboard())
                os.remove(kml_file)
        else:
            bot.send_message(chat_id, f"[-] '{cadastre_number}' raqami bo'yicha {cat_title} bazasidan ma'lumot topilmadi.", reply_markup=get_result_keyboard())
            
    except requests.exceptions.Timeout:
        bot.send_message(chat_id, "[!] Server javob berish vaqtini uzaytirdi. Baza vaqtincha band.", reply_markup=get_result_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"[!] Xatolik yuz berdi: {e}", reply_markup=get_result_keyboard())

if __name__ == '__main__':
    print("Bot ishga tushdi va ishlamoqda...")
    bot.polling(none_stop=True)
