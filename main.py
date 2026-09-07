headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'uz,en-US;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://db.ngis.uz/'
    }
    
    # ArcGIS bazalarida ustun nomlari ko'pincha katta harflarda bo'ladi
    params = {
        'where': f"CADASTRAL_NUMBER = '{cadastre_number}' OR KADASTR = '{cadastre_number}' OR CAD_NUM = '{cadastre_number}'",
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true',
        'outSR': '4326',
        'resultRecordCount': 1
    }
    
    try:
        session = requests.Session()
        # Avval asosiy saytga kirib cookie olamiz
        session.get('https://db.ngis.uz/', headers=headers, timeout=10)
        
        # Keyin aniq qidiruvni bajaramiz (vaqtni 25 sekundga oshiramiz)
        response = session.get(api_url, params=params, headers=headers, timeout=25)
