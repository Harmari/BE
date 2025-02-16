from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
from app.core.config import settings
import logging
from google.oauth2 import service_account

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TOKEN_PATH = settings.TOKEN_PATH
TOKEN_PATH = os.path.join(os.getcwd(), "token.json")
SERVICE_ACCOUNT_PATH = os.path.join(os.getcwd(), "service_account.json")
GOOGLE_CREDENTIALS_PATH = settings.GOOGLE_CREDENTIALS_PATH
SCOPES = settings.GOOGLE_SCOPES

SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), "service_account.json")
ADMIN_CALENDAR_ID = settings.ADMIN_CALENDAR_ID

# def authenticate_google_calendar():
#     creds = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_PATH, scopes=SCOPES
#     )
#     try:
#         if os.path.exists(TOKEN_PATH):
#             creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
#             logger.info(f"--------------------------------자격 증명 파일 로드 완료")
#     except Exception as e:
#         logger.error(f"--------------------------------자격 증명 파일을 로드하는 중 오류 발생: {e}")
#         return Exception(f"자격 증명 파일을 로드하는 중 오류 발생: {e}")
#     # If there are no (valid) credentials available, let the user log in.
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             logger.info("--------------------------------자격 증명이 만료되어 새로 고침 중입니다.")
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 GOOGLE_CREDENTIALS_PATH, SCOPES)
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open(TOKEN_PATH, 'w') as token:
#             logger.info(f"--------------------------------자격 증명을 파일에 저장합니다: {TOKEN_PATH}")
#             token.write(creds.to_json())
#
#     return creds


def get_service_account_credentials():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        return creds
    except Exception as e:
        logger.error(f"서비스 계쩡 자격 증명 로드 실패: {e}")
        return None


async def add_event_to_user_calendar(user_email, event_date):
    # event_date가 문자열이라면 datetime 객체로 변환
    if isinstance(event_date, str):
        logger.info(f"Received event_date: {event_date}")
        try:
            event_date = datetime.strptime(event_date, "%Y%m%d%H%M")
        except ValueError:
            raise ValueError("event_date가 올바른 형식이 아닙니다. '%Y%m%d%H%M' 형식이어야 합니다.")

    try:

        # creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        creds = get_service_account_credentials()
        if not creds:
            logger.error("서비스 계정 인증에 실패했습니다.")
            return None

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
            # 이 부분은 사용자를 구글캘린더에 자동 초대하는 기능으로 google works 의 기업용 유료 도메인이 필요한 부분임 해당 부분은 추후 추가
            # 'attendees': [
            #     {'email': user_email},
            # ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        event = service.events().insert(calendarId=ADMIN_CALENDAR_ID, body=event).execute()
        logger.info('Event created: %s' % (event.get('htmlLink')))

        return event.get('id')  # 이벤트 아이디 반환

    except Exception as e:
        logger.error(f"캘린더에 이벤트 추가 중 오류 발생: {e}")
        return None


def update_event_with_meet_link(event_id):
    try:
        creds = get_service_account_credentials()
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().get(calendarId=ADMIN_CALENDAR_ID, eventId=event_id).execute()

        # Google Meet 링크 자동 생성
        event['conferenceData'] = {
            'createRequest': {
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                'requestId': 'some-unique-string'
            }
        }

        updated_event = service.events().update(
            calendarId=ADMIN_CALENDAR_ID,
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
    creds = get_service_account_credentials()
    service = build('calendar', 'v3', credentials=creds)

    try:
        # 이벤트가 존재하는지 확인
        event = service.events().get(calendarId=ADMIN_CALENDAR_ID, eventId=event_id).execute()
        if event:
            service.events().delete(calendarId=ADMIN_CALENDAR_ID, eventId=event_id).execute()
            logger.info('--------------------------------구글캘린더 이벤트 삭제: %s' % event_id)
    except Exception as e:
        logger.error(f"이벤트 삭제 중 오류 발생: {e}")