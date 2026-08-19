import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def clean_tcmb_events():
    service_account_info = json.loads(os.environ['GOOGLE_CREDENTIALS_JSON'])
    calendar_id = os.environ['CALENDAR_ID']
    
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    service = build('calendar', 'v3', credentials=creds)
    
    # "TCMB Kurları" arama kelimesine uyan etkinlikleri listele
    events_result = service.events().list(
        calendarId=calendar_id,
        q='TCMB Kurları',
        singleEvents=True
    ).execute()
    
    events = events_result.get('items', [])
    
    if not events:
        print("Silinecek TCMB etkinliği bulunamadı.")
        return
        
    print(f"Toplam {len(events)} adet TCMB etkinliği bulundu, siliniyor...")
    
    for event in events:
        summary = event.get('summary', '')
        event_id = event['id']
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print(f"Silindi: {summary} (ID: {event_id})")
        
    print("Temizleme tamamlandı!")

if __name__ == "__main__":
    clean_tcmb_events()
