import os
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_tcmb_rates():
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
        
    root = ET.fromstring(xml_data)
    date_str = root.attrib.get('Tarih', datetime.now().strftime("%d.%m.%Y"))
    
    target_currencies = ['USD', 'EUR', 'GBP']
    rates_summary = []
    
    for currency in root.findall('Currency'):
        code = currency.attrib.get('Kod')
        if code in target_currencies:
            name = currency.find('Isim').text.strip()
            forex_buy = currency.find('ForexBuying').text or '-'
            forex_sell = currency.find('ForexSelling').text or '-'
            rates_summary.append(f"• {code} ({name})\n  Alış: {forex_buy} | Satış: {forex_sell}")
            
    return date_str, "\n\n".join(rates_summary)

def add_to_calendar(date_str, description):
    # Google kimlik bilgilerini GitHub Secrets'tan al
    service_account_info = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
    calendar_id = os.environ['CALENDAR_ID']
    
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    
    service = build('calendar', 'v3', credentials=creds)
    today_iso = datetime.now().strftime("%Y-%m-%d")
    
    event = {
        'summary': f'TCMB Kurları ({date_str})',
        'description': description,
        'start': {'date': today_iso},
        'end': {'date': today_iso},
    }
    
    result = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Etkinlik oluşturuldu: {result.get('htmlLink')}")

if __name__ == "__main__":
    tarih, ozet = get_tcmb_rates()
    add_to_calendar(tarih, ozet)
