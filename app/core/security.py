from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# JWT 설정
SECRET_KEY = settings.SECRET_KEY
REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# OAuth2 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def verify_access_token(token: str) -> dict:
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

        return verify_access_token(access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")
    
def set_auth_cookies(response: Response, access_token: str, refresh_token: str): 
    """JWT를 httpOnly Secure 쿠키에 저장"""
    # 쿠키에 Access Token 저장
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="None",
    )

    # 쿠키에 Refresh Token 저장
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="None",
    )

def clear_auth_cookies(response: Response): 
    """JWT 쿠키 삭제 (로그아웃 시 사용)"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")