
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If modifying these SCOPES, delete the file token.json.
TOKEN_PATH = '../token.json'
SCOPES = settings.GOOGLE_SCOPES
GOOGLE_CREDENTIALS_PATH = settings.GOOGLE_CREDENTIALS_PATH


def authenticate_google_calendar():
    creds = None
    # token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds


async def add_event_to_user_calendar(user_email, event_date):
    # event_date가 문자열이라면 datetime 객체로 변환
    if isinstance(event_date, str):
        logger.info(f"Received event_date: {event_date}")
        try:
            event_date = datetime.strptime(event_date, "%Y%m%d%H%M")
        except ValueError:
            raise ValueError("event_date가 올바른 형식이 아닙니다. '%Y%m%d%H%M' 형식이어야 합니다.")

    # Load user's credentials
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # Build the calendar service
    service = build('calendar', 'v3', credentials=creds)

    # Create the event
    event = {
        'summary': '블리스 헤어 상담소',
        'description': '블리스 헤어 상담소 예약 이벤트',
        'start': {
            'dateTime': event_date.isoformat(),
            'timeZone': 'Asia/Seoul',
        },
        'end': {
            'dateTime': (event_date + timedelta(hours=1)).isoformat(),
            'timeZone': 'Asia/Seoul',
        },
        'attendees': [
            {'email': user_email},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    # Insert the event into the user's calendar
    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    return event.get('id')  # 이벤트 ID 반환



def update_event_with_meet_link(event_id, google_meet_link):
    creds = authenticate_google_calendar()
    service = build('calendar', 'v3', credentials=creds)

    event = service.events().get(calendarId='primary', eventId=event_id).execute()
    event['location'] = google_meet_link

    updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
    print('Event updated: %s' % (updated_event.get('htmlLink')))