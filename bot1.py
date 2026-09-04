import threading
import telebot
import requests
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

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

def get_category_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🏠 Turar joylar", callback_data="cat_turar"),
        InlineKeyboardButton("🏢 Noturar joylar", callback_data="cat_noturar"),
        InlineKeyboardButton("🌾 Qishloq xo'jaligi yerlari", callback_data="cat_agr"),
        InlineKeyboardButton("📜 Tarixni ko'rish", callback_data="show_history")
    )
    return markup

def get_back_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 Kategoriyalarga qaytish", callback_data="back_to_menu"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_state[chat_id] = None
    
    welcome_text = (
        "Assalomu alaykum! 🏛\n\n"
        "Elektron kadastr ma'lumotlar botiga xush kelibsiz.\n"
        "Qaysi yo'nalish bo'yicha ma'lumot qidirmoqchisiz? Marhamat, quyidagilardan birini tanlang:"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_category_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    bot.answer_callback_query(call.id)
    
    if data == "cat_turar":
        user_state[chat_id] = "turar"
        bot.edit_message_text(
            "✅ *Turar joylar* tanlandi.\n\nEndi kadastr raqamini kiriting (masalan: `14:07:42:03:01:0443`):", 
            chat_id, 
            call.message.message_id, 
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
    elif data == "cat_noturar":
        user_state[chat_id] = "noturar"
        bot.edit_message_text(
            "✅ *Noturar joylar* tanlandi.\n\nEndi kadastr raqamini kiriting (masalan: `14:07:42:03:01:0443`):", 
            chat_id, 
            call.message.message_id, 
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
    elif data == "cat_agr":
        user_state[chat_id] = "agr"
        bot.edit_message_text(
            "✅ *Qishloq xo'jaligi yerlari* tanlandi.\n\nEndi kadastr raqamini kiriting (masalan: `14:07:42:03:01:0443`):", 
            chat_id, 
            call.message.message_id, 
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
    elif data == "show_history":
        history = load_history()
        str_user_id = str(chat_id)
        
        if str_user_id in history and history[str_user_id]:
            text = "📜 *Sizning qidiruvlar tarixingiz:*\n\n"
            for idx, item in enumerate(history[str_user_id], 1):
                text += f"{idx}. `{item['cadastre_number']}` ({item.get('category', '-')}) — _{item['date']}_\n"
        else:
            text = "Sizda hali qidiruvlar tarixi mavjud emas."
            
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=get_back_keyboard())
    elif data == "back_to_menu":
        user_state[chat_id] = None
        bot.edit_message_text(
            "Qaysi yo'nalish bo'yicha ma'lumot qidirmoqchisiz? Marhamat, quyidagilardan birini tanlang:", 
            chat_id, 
            call.message.message_id, 
            reply_markup=get_category_keyboard()
        )

@bot.message_handler(func=lambda message: True)
def handle_cadastre(message):
    chat_id = message.chat.id
    current_category = user_state.get(chat_id)
    
    if not current_category:
        bot.send_message(chat_id, "Iltimos, avval /start buyrug'ini bosing yoki quyidagi menyudan foydalaning:", reply_markup=get_category_keyboard())
        return

    cadastre_number = message.text.strip()
    api_url = SERVICES[current_category]["url"]
    cat_title = SERVICES[current_category]["name"]
    
    bot.send_message(chat_id, f"🔍 {cat_title} bazasidan '{cadastre_number}' qidirilmoqda...")
    
    threading.Thread(target=process_cadastre_request, args=(chat_id, cadastre_number, api_url, cat_title)).start()

def process_cadastre_request(chat_id, cadastre_number, api_url, cat_title):
    params = {
        'where': f"cadastral_number = '{cadastre_number}'",
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'outSR': '4326'
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=15)
        data = response.json()
        
        if 'features' in data and len(data['features']) > 0:
            feature = data['features'][0]
            attr = feature.get('attributes', {})
            
            c_num = attr.get('cadastral_number', cadastre_number)
            viloyat = attr.get('region_name', '-')
            tuman = attr.get('district_name', '-')
            mahalla_nomi = attr.get('mahalla_name', '-')
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
            
            bot.send_message(chat_id, text_result, parse_mode='Markdown', reply_markup=get_category_keyboard())
            save_history(chat_id, cadastre_number, cat_title)
            
            kml_file = create_kml(feature, cadastre_number)
            if kml_file and os.path.exists(kml_file):
                with open(kml_file, 'rb') as f:
                    bot.send_document(chat_id, f, caption="Xaritadagi kml fayli", reply_markup=get_category_keyboard())
                os.remove(kml_file)
        else:
            bot.send_message(chat_id, f"[-] '{cadastre_number}' raqami bo'yicha {cat_title} bazasidan hech qanday ma'lumot topilmadi.", reply_markup=get_category_keyboard())
            
    except requests.exceptions.Timeout:
        bot.send_message(chat_id, "[!] Bazadan javob kelishi juda cho'zilib ketdi (server vaqtincha ishlamayapti). Iltimos, qaytadan urinib ko'ring.", reply_markup=get_category_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"[!] Xatolik yuz berdi: {e}", reply_markup=get_category_keyboard())

if __name__ == '__main__':
    print("Bot ishga tushdi va ishlamoqda...")
    bot.polling(none_stop=True)
