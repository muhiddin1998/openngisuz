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
user_state = {}  # Foydalanuvchilarning joriy holati va tanlagan kategoriyasi

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

# Asosiy menyu (Har doim chiqib turadigan tugmalar)
def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🔍 Kadastr ma'lumotlarini izlash"),
        KeyboardButton("📜 Tarixni ko'rish")
    )
    return markup

# Kategoriyalar menyusi
def get_category_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🏠 Turar joylar"),
        KeyboardButton("🏢 Noturar joylar"),
        KeyboardButton("🌾 Qishloq xo'jaligi yerlari"),
        KeyboardButton("🔙 Orqaga")
    )
    return markup

# Kadastr raqamini kiritish paytidagi orqaga qaytish tugmasi
def get_back_to_cat_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔙 Kategoriyalarga qaytish"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_state[chat_id] = None
    photo_path = "kadastr_banner.jpg"
    
    welcome_text = (
        "Assalomu alaykum! 🏛\n\n"
        "Elektron kadastr ma'lumotlar botiga xush kelibsiz.\n"
        "Ma'lumot qidirish uchun quyidagi tugmani bosing:"
    )
    
    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=welcome_text, reply_markup=get_main_keyboard())
    else:
        bot.send_message(chat_id, welcome_text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔍 Kadastr ma'lumotlarini izlash")
def show_categories(message):
    user_state[message.chat.id] = "selecting_category"
    bot.send_message(
        message.chat.id, 
        "Qaysi yo'nalish bo'yicha ma'lumot qidirmoqchisiz? Marhamat, quyidagilardan birini tanlang:", 
        reply_markup=get_category_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "🔙 Orqaga")
def go_to_main(message):
    user_state[message.chat.id] = None
    bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔙 Kategoriyalarga qaytish")
def back_to_categories(message):
    user_state[message.chat.id] = "selecting_category"
    bot.send_message(message.chat.id, "Kategoriyani tanlang:", reply_markup=get_category_keyboard())

@bot.message_handler(commands=['tarix'])
@bot.message_handler(func=lambda message: message.text == "📜 Tarixni ko'rish")
def show_history(message):
    history = load_history()
    str_user_id = str(message.chat.id)
    
    if str_user_id in history and history[str_user_id]:
        text = "📜 *Sizning qidiruvlar tarixingiz:*\n\n"
        for idx, item in enumerate(history[str_user_id], 1):
            text += f"{idx}. `{item['cadastre_number']}` ({item.get('category', '-')}) — _{item['date']}_\n"
        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=get_main_keyboard())
    else:
        bot.send_message(message.chat.id, "Sizda hali qidiruvlar tarixi mavjud emas.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text in ["🏠 Turar joylar", "🏢 Noturar joylar", "🌾 Qishloq xo'jaligi yerlari"])
def set_category(message):
    text = message.text
    chat_id = message.chat.id
    
    if "Turar joylar" in text:
        user_state[chat_id] = "turar"
        cat_name = "Turar joylar"
    elif "Noturar joylar" in text:
        user_state[chat_id] = "noturar"
        cat_name = "Noturar joylar"
    else:
        user_state[chat_id] = "agr"
        cat_name = "Qishloq xo'jaligi yerlari"
        
    bot.send_message(
        chat_id, 
        f"✅ *{cat_name}* tanlandi.\n\nEndi qidirish uchun **kadastr raqamini** kiriting (masalan: `14:07:42:03:01:0443`):", 
        parse_mode='Markdown',
        reply_markup=get_back_to_cat_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_cadastre(message):
    chat_id = message.chat.id
    current_category = user_state.get(chat_id)
    
    # Agar foydalanuvchi hech qanday qidiruv jarayonida bo'lmasa yoki shunchaki matn yozsa
    if not current_category or current_category == "selecting_category":
        bot.send_message(
            chat_id, 
            "Iltimos, ma'lumot qidirish uchun quyidagi tugmani bosing:", 
            reply_markup=get_main_keyboard()
        )
        return
        
    cadastre_number = message.text.strip()
    api_url = SERVICES[current_category]["url"]
    cat_title = SERVICES[current_category]["name"]
    
    bot.send_message(chat_id, f"🔍 {cat_title} bazasidan '{cadastre_number}' qidirilmoqda...")
    
    params = {
        'where': f"cadastral_number = '{cadastre_number}'",
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'outSR': '4326'
    }
    
    try:
        response = requests.get(api_url, params=params)
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
            
            bot.send_message(chat_id, text_result, parse_mode='Markdown', reply_markup=get_back_to_cat_keyboard())
            
            save_history(chat_id, cadastre_number, cat_title)
            
            kml_file = create_kml(feature, cadastre_number)
            if kml_file and os.path.exists(kml_file):
                with open(kml_file, 'rb') as f:
                    bot.send_document(
                        chat_id, 
                        f, 
                        caption="Xaritadagi kml fayli", 
                        reply_markup=get_back_to_cat_keyboard()
                    )
                os.remove(kml_file)
        else:
            bot.send_message(chat_id, f"[-] '{cadastre_number}' raqami bo'yicha {cat_title} bazasidan hech qanday ma'lumot topilmadi.", reply_markup=get_back_to_cat_keyboard())
            
    except Exception as e:
        bot.send_message(chat_id, f"[!] Xatolik yuz berdi: {e}", reply_markup=get_back_to_cat_keyboard())

if __name__ == '__main__':
    print("Bot ishga tushdi va ishlamoqda...")
    bot.polling(none_stop=True)