import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.request
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_next_business_day(current_date):
    weekday = current_date.weekday()  # 0: Pzt, 4: Cuma, 5: Cmt, 6: Paz
    
    if weekday == 4:  # Cuma 15:30 sonrası -> Pazartesi
        return current_date + timedelta(days=3)
    elif weekday == 5:  # Cumartesi
        return current_date + timedelta(days=2)
    else:  # Pzt, Sal, Çar, Per, Paz
        return current_date + timedelta(days=1)

def get_tcmb_rates():
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
        
    root = ET.fromstring(xml_data)
    bulten_tarihi = root.attrib.get('Tarih', datetime.now().strftime("%d.%m.%Y"))
    
    target_currencies = ['USD', 'EUR', 'GBP']
    rates_summary = []
    
    for currency in root.findall('Currency'):
        code = currency.attrib.get('Kod')
        if code in target_currencies:
            name = currency.find('Isim').text.strip()
            forex_buy = currency.find('ForexBuying').text or '-'
            forex_sell = currency.find('ForexSelling').text or '-'
            rates_summary.append(f"• {code} ({name})\n  Alış: {forex_buy} | Satış: {forex_sell}")
            
    rates_text = f"Bülten Tarihi: {bulten_tarihi}\n\n" + "\n\n".join(rates_summary)
    return bulten_tarihi, rates_text

def add_to_calendar(bulten_tarihi, description):
    service_account_info = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
    calendar_id = os.environ['CALENDAR_ID']
    
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    
    service = build('calendar', 'v3', credentials=creds)
    
    today = datetime.now()
    target_date = get_next_business_day(today)
    target_date_iso = target_date.strftime("%Y-%m-%d")
    target_date_str = target_date.strftime("%d.%m.%Y")
    
    event = {
        'summary': f'TCMB Kurları ({target_date_str})',
        'description': f"Bu kurlar {target_date_str} tarihi için geçerlidir.\n\n{description}",
        'start': {'date': target_date_iso},
        'end': {'date': target_date_iso},
    }
    
    result = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Etkinlik {target_date_str} tarihine oluşturuldu: {result.get('htmlLink')}")

if __name__ == "__main__":
    bulten_tarihi, ozet = get_tcmb_rates()
    add_to_calendar(bulten_tarihi, ozet)
