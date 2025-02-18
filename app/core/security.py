import logging
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer
from google.auth.transport.requests import Request as GoogleRequest

from app.core.config import settings

# JWT 설정
SECRET_KEY = settings.SECRET_KEY
REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from app.db.session import get_database
db = get_database()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """JWT Access Token 생성"""
    try:
        # 토큰 만료 시간 설정
        to_encode = data.copy()

        # 만료 시간이 지정되지 않은 경우, 기본 만료 시간 설정
        expire_time = datetime.fromisoformat(settings.CURRENT_DATETIME) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

        # 토큰에 만료 시간 추가
        to_encode.update({"exp": expire_time.timestamp()})
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # 예외처리(그 외 예외)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JWT 생성 오류: {str(e)}")
    
def create_refresh_token(data: dict) -> str:
    """JWT Refresh Token 생성 (Access Token과 다른 서명 키 사용)"""
    try:
        # 토큰 만료 시간 설정
        to_encode = data.copy()

        # 만료 시간 설정
        expire_time = datetime.fromisoformat(settings.CURRENT_DATETIME) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        # 토큰에 만료 시간 추가
        to_encode.update({"exp": expire_time.timestamp()})

        return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    
    # 예외처리(그 외 예외)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error : {str(e)}")

async def verify_access_token(token: str) -> dict:
    """JWT Access Token 검증"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="access token 만료")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 access token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

def verify_refresh_token(refresh_token: str) -> dict:
    """JWT Refresh Token 검증 (Access Token과 다른 서명 키 사용)"""
    try:
        return jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="refresh token 만료")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 refresh token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error : {str(e)}")

async def get_current_user(request: Request) -> dict: 
    """현재 로그인한 사용자 확인 (JWT 검증) + Access Token 자동 갱신"""
    try:
        # 쿠키에서 Access Token 가져오기 
        access_token = request.cookies.get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="Access Token이 제공되지 않았습니다.")

        return await verify_access_token(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")
    
def set_auth_cookies(response: Response, access_token: str, refresh_token: str, email: str):
    """JWT를 httpOnly Secure 쿠키에 저장"""

    # 쿠키에 Access Token 저장
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="None",
        domain="harmari.duckdns.org",
        path="/"
    )

    # 쿠키에 Refresh Token 저장
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
        domain="harmari.duckdns.org",
        path="/"
    )

    # 쿠키에 email 저장
    response.set_cookie(
        key="email",
        value=email,
        httponly=True,
        secure=True,
        samesite="None",
        domain="harmari.duckdns.org",
        path="/"
    )

def clear_auth_cookies(response: Response): 
    """JWT 쿠키 삭제 (로그아웃 시 사용)"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


async def get_auth_user(request: Request) -> dict:
    # 쿠키에서 이메일 정보 추출 (예: "email" 키에 저장)
    user_email = request.cookies.get("email")
    if not user_email:
        logger.info("이메일 쿠키가 존재하지 않습니다.")
        raise HTTPException(status_code=401, detail="로그인 한 사용자만 사용 가능합니다.")

    # DB에서 사용자 정보 조회 (이메일 기준)
    user_record = await db["users"].find_one({"email": user_email})
    if not user_record:
        logger.info("DB에서 사용자 정보를 찾을 수 없습니다.")
        raise HTTPException(status_code=404, detail="사용자 정보를 찾을 수 없습니다.")

    # DB에서 Google OAuth2 토큰 정보 가져오기
    google_access_token = user_record.get("google_access_token")
    google_refresh_token = user_record.get("google_refresh_token")
    if not google_access_token or not google_refresh_token:
        logger.info("DB에 Google 인증 정보가 없습니다.")
        raise HTTPException(status_code=401, detail="Google 인증 정보가 없습니다.")

    # Google OAuth2 Credentials 객체 생성 (캘린더 접근 권한 포함)
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    token_uri = "https://oauth2.googleapis.com/token"
    scopes = ["openid", "email", "profile", "https://www.googleapis.com/auth/calendar"]

    credentials = Credentials(
        token=google_access_token,
        refresh_token=google_refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes
    )

    logging.info(f"credentials =======================> {credentials}")

    # 토큰 만료 시 자동 갱신
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(GoogleRequest())
            # 갱신된 토큰 정보를 DB에 업데이트
            await db["users"].update_one(
                {"email": user_email},
                {"$set": {
                    "google_access_token": credentials.token,
                    "google_refresh_token": credentials.refresh_token
                }}
            )
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            raise HTTPException(status_code=401, detail=f"토큰 갱신에 실패했습니다: {e}")

    # 반환할 사용자 정보에 Credentials 객체와 이메일 추가
    user_data = {
        "email": user_email,
        "credentials": credentials
    }
    return user_data
