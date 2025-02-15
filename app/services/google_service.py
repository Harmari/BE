
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

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        service = build('calendar', 'v3', credentials=creds)
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
        event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info('Event created: %s' % (event.get('htmlLink')))
    
        return event.get('id') # 이벤트 아이디 반환
    
    except Exception as e:
        logger.error(f"캘린더에 이벤트 추가 중 오류 발생: {e}")
        return None



def update_event_with_meet_link(event_id):
    try:
        creds = authenticate_google_calendar()
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Google Meet 링크 자동 생성
        event['conferenceData'] = {
            'createRequest': {
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                'requestId': 'some-unique-string'
            }
        }

        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            conferenceDataVersion=1
        ).execute()

        # Google Meet 링크 확인
        meet_link = updated_event.get('conferenceData', {}).get('entryPoints', [])[0].get('uri', '')
        logger.info('--------------------------------Google Meet Link: %s' % meet_link)
        logger.info('--------------------------------Event updated: %s' % (updated_event.get('htmlLink')))

        return meet_link
    
    except Exception as e:
        logger.error(f"Google Meet 링크 업데이트 중 오류 발생: {e}")
        return None


def delete_google_calendar_event(event_id):
    creds = authenticate_google_calendar()
    service = build('calendar', 'v3', credentials=creds)

    try:
        # 이벤트가 존재하는지 확인
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        if event:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            logger.info('--------------------------------구글캘린더 이벤트 삭제: %s' % event_id)
    except Exception as e:
        logger.error(f"이벤트 삭제 중 오류 발생: {e}")