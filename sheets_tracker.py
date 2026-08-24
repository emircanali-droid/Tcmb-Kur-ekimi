import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.request
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_next_business_day(current_date):
    weekday = current_date.weekday()
    if weekday == 4:  # Cuma -> Pazartesi
        return current_date + timedelta(days=3)
    elif weekday == 5:  # Cumartesi -> Pazartesi
        return current_date + timedelta(days=2)
    else:
        return current_date + timedelta(days=1)

def get_tcmb_rates():
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
        
    root = ET.fromstring(xml_data)
    bulten_tarihi = root.attrib.get('Tarih', datetime.now().strftime("%d.%m.%Y"))
    
    today = datetime.now()
    gecerlilik_tarihi = get_next_business_day(today).strftime("%d.%m.%Y")
    
    target_currencies = ['USD', 'EUR', 'GBP']
    rates_rows = []
    
    for currency in root.findall('Currency'):
        code = currency.attrib.get('Kod')
        if code in target_currencies:
            forex_buy = currency.find('ForexBuying').text or ''
            forex_sell = currency.find('ForexSelling').text or ''
            banknote_buy = currency.find('BanknoteBuying').text or ''
            banknote_sell = currency.find('BanknoteSelling').text or ''
            
            # Sayısal değerlerdeki noktayı Excel/Sheets formatına uygun dönüştürme opsiyonu
            # Sheets yerel ayarınıza göre nokta veya virgül otomatik algılanır
            rates_rows.append([
                bulten_tarihi,
                gecerlilik_tarihi,
                code,
                forex_buy,
                forex_sell,
                banknote_buy,
                banknote_sell,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
            
    return rates_rows

def sync_to_google_sheets(rows):
    service_account_info = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
    spreadsheet_id = os.environ['SPREADSHEET_ID']
    
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    # 1. Mevcut verileri oku (Başlık var mı ve mükerrer kayıt kontrolü)
    result = sheet.values().get(
        spreadsheetId=spreadsheet_id,
        range="Sayfa1!A:H"
    ).execute()
    
    existing_values = result.get('values', [])
    
    # Başlık satırı yoksa önce başlıkları ekle
    headers = [
        "Bülten Tarihi", "Geçerlilik Tarihi", "Döviz Kodu",
        "Döviz Alış", "Döviz Satış", "Efektif Alış", "Efektif Satış", "Kayıt Zamanı"
    ]
    
    if not existing_values:
        sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range="Sayfa1!A1",
            valueInputOption="USER_ENTERED",
            body={"values": [headers]}
        ).execute()
        existing_values = [headers]
    
    # Mükerrer kontrolü (Bülten Tarihi + Döviz Kodu)
    existing_keys = set()
    for row in existing_values[1:]:
        if len(row) >= 3:
            existing_keys.add((row[0], row[2]))
            
    new_rows_to_add = []
    for r in rows:
        key = (r[0], r[2])
        if key not in existing_keys:
            new_rows_to_add.append(r)
            
    if new_rows_to_add:
        sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range="Sayfa1!A:H",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": new_rows_to_add}
        ).execute()
        print(f"{len(new_rows_to_add)} yeni satır Google Sheets'e başarıyla eklendi.")
    else:
        print("Bu bülten tarihine ait kurlar zaten tabloda mevcut, mükerrer eklenmedi.")

if __name__ == "__main__":
    rates = get_tcmb_rates()
    sync_to_google_sheets(rates)
