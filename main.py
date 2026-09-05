def process_cadastre_request(chat_id, cadastre_number, api_url, cat_title):
    session = requests.Session()
    
    # Brauzer ekanligini To'liq ko'rsatuvchi Sarlavhalar
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'uz,en-US;q=0.9,en;q=0.8,ru;q=0.7',
        'Connection': 'keep-alive',
        'Referer': 'https://db.ngis.uz/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    params = {
        'where': f"cadastral_number = '{cadastre_number}' OR kadastr = '{cadastre_number}' OR cad_num = '{cadastre_number}'",
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'outSR': '4326',
        'resultRecordCount': 1
    }
    
    try:
        # Avval asosiy sahifaga GET so'rov yuborib Cookie olib qolamiz (Himoyadan o'tish uchun)
        session.get('https://db.ngis.uz/', headers=headers, timeout=10)
        
        # Endi API ga real so'rov yuboramiz
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
        bot.send_message(chat_id, "[!] Server javob berish vaqtini uzaytirdi. Baza vaqtincha band yoki so'rovni rad etdi.", reply_markup=get_result_keyboard())
    except Exception as e:
        bot.send_message(chat_id, f"[!] Xatolik yuz berdi: {e}", reply_markup=get_result_keyboard())
