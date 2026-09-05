import telebot
import requests
import json
import os
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8797770726:AAGHJvpFtm2_x5CD6bvLWfmregFRvvD-OPU"
bot = telebot.TeleBot(TOKEN)

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
    bot.send_message(chat_id, "Kategoriyani tanlang:", reply_markup=
