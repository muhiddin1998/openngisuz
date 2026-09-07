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
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'uz,en-US;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://open.ngis.uz/',
        'Origin': 'https://open.ngis.uz'
    }
    
    # ArcGIS serveri uchun qidiruv sharti (barcha mumkin bo'lgan ustun nomlarini qamrab olamiz)
    where_query = f"CADASTRAL_NUMBER='{cadastre_number}' OR KADASTR='{cadastre_number}' OR CAD_NUM='{cadastre_number}' OR NUMBER='{cadastre_number}'"
    
    params = {
        'where': where_query,
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'outSR': '4326',
        'resultRecordCount': 5
    }
    
    try:
        session = requests.Session()
        # Avval asosiy sahifaga cookie olish uchun head/get so'rov yuboramiz
        session.get('https://open.ngis.uz/', headers=headers, timeout=15)
        
        # Asosiy ArcGIS mapserver query so'rovi
        response = session.get(api_url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            bot.send_message(chat_id, f"[!] Server xato kod qaytardi: HTTP {response.status_code}", reply_markup=get_result_keyboard())
            return
            
        data = response.json()
        
        if 'error' in data:
            bot.send_message(chat_id, f"[!] Server xabari: {data['error'].get('message', 'Xatolik')}", reply_markup=get_result_keyboard())
            return
            
        if 'features' in data and len(data['features']) > 0:
            feature = data['features'][0]
            attr = feature.get('attributes', {})
            
            c_num = attr.get('CADASTRAL_NUMBER', attr.get('KADASTR', attr.get('CAD_NUM', cadastre_number)))
            viloyat = attr.get('region_name', attr.get('viloyat', attr.get('REGION', '-')))
            tuman = attr.get('district_name', attr.get('tuman', attr.get('DISTRICT', '-')))
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
        bot.send_message(chat_id, "[!] Server javob berish vaqtini uzaytirdi. Baza band yoki himoya tizimi so'rovni ushlab qoldi.", reply_markup=get_result_keyboard())
    except Exception as e:
        bot.send_message(chat_id, "[!] Xatolik yuz berdi. Keyinroq urinib ko'ring.", reply_markup=get_result_keyboard())
