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
GOOGLE_CREDENTIALS_PATH = settings.GOOGLE_CREDENTIALS_PATH
SCOPES = settings.GOOGLE_SCOPES

SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), "service_account.json")
DESIGNER_EMAIL = "hsc890125@gmail.com"


def get_service_account_credentials(access_token: str):
    try:
        creds = Credentials(token=access_token, scopes=SCOPES)
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"서비스 계쩡 자격 증명 로드 실패: {e}")
        return None


async def add_event_to_user_calendar(user_email: str, 
                                     credentials: Credentials, 
                                     event_date: datetime, 
                                     designer_name: str, 
                                     designer_introduction: str, 
                                     designer_region: str, 
                                     designer_specialist: str, 
                                     designer_shop_address: str,
                                     mode: str):

    logging.info(f"credentials ============ add_event_to_user_calendar ===========> {credentials}")

    # event_date가 문자열이라면 datetime 객체로 변환
    if isinstance(event_date, str):
        logger.info(f"Received event_date: {event_date}")
        try:
            event_date_obj = datetime.strptime(event_date, "%Y%m%d%H%M")
        except ValueError:
            raise ValueError("event_date가 올바른 형식이 아닙니다. '%Y%m%d%H%M' 형식이어야 합니다.")
    else:
        event_date_obj = event_date

    try:
        service = build("calendar", "v3", credentials=credentials)

        # DESIGNER_EMAIL은 추후 디자이너id로 eamil 조회해와서 하는걸로 수정
        event_body = {
            "summary": "블리스 헤어 상담소",

            "description": f"""\n여러분의 헤어스타일 고민을 날려버릴 블리스 헤어 상담소 입니다❤️💈💈💈\n
🩷'{designer_specialist}' 전문 디자이너 💇🏼‍♀️💆🏻‍♂️
💃🏻'{designer_name}'님(과)의 '{mode}'상담 일정입니다 💆‍♀️
{designer_name}님은요... {designer_introduction}!!


❗️'비대면'상담 주의사항❗️
    - 미리 캘린더에 생성된 Google Meet 링크를 통해 상담을 진행합니다.
    - 시간은 금 ! 상담은 정시에 시작됩니다 💜
❗️'대면'상담 주의사항❗️
    - 💈{designer_shop_address}
    - 디자이너 쌤이 있는곳 GoGo!!
    - 🧡 10분 전에 도착해주세요!
    
📍{designer_region} 
            """,
            "start": {
                "dateTime": event_date_obj.isoformat(),  # 수정: event_date_obj 사용
                "timeZone": "Asia/Seoul",
            },
            "end": {
                "dateTime": (event_date_obj + timedelta(minutes=30)).isoformat(),  # 수정: event_date_obj 사용
                "timeZone": "Asia/Seoul",
            },
            "attendees": [
                {"email": user_email},  # 예약한 유저
                {"email": DESIGNER_EMAIL},  # 디자이너
            ],
            "conferenceData": {
                "createRequest": {
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    "requestId": "unique-request-id"
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1
        ).execute()

        event_id = created_event.get("id")
        event_html_link = created_event.get("htmlLink")
        conference_data = created_event.get("conferenceData", {})
        entry_points = conference_data.get("entryPoints", [])
        meet_link = entry_points[0].get("uri") if entry_points else None

        logger.info(f"Event created: {event_html_link}")
        logger.info(f"Google Meet Link: {meet_link}")

        return event_id, event_html_link, meet_link

    except Exception as e:
        logger.error(f"캘린더에 이벤트 추가 중 오류 발생: {e}")
        return None


def update_event_with_meet_link(event_id):
    try:
        creds = get_service_account_credentials()
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().get(calendarId=DESIGNER_EMAIL, eventId=event_id).execute()

        # Google Meet 링크 자동 생성
        event['conferenceData'] = {
            'createRequest': {
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                'requestId': 'some-unique-string'
            }
        }

        updated_event = service.events().update(
            calendarId=DESIGNER_EMAIL,
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


def delete_google_calendar_event(event_id, credentials:Credentials):
    service = build('calendar', 'v3', credentials=credentials)

    try:
        # 이벤트가 존재하는지 확인
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        if event:
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            logger.info('--------------------------------구글캘린더 이벤트 삭제: %s' % event_id)
    except Exception as e:
        logger.error(f"이벤트 삭제 중 오류 발생: {e}")