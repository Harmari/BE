from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import Depends, HTTPException
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
        # 토큰 디코딩
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return payload
    
    # 예외처리(토큰 만료, 유효하지 않은 토큰, 그 외 예외)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="access token 만료")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 access token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")

def verify_refresh_token(refresh_token: str) -> dict:
    """JWT Refresh Token 검증 (Access Token과 다른 서명 키 사용)"""
    try:
        # 토큰 검증
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    
    # 예외처리(토큰 만료, 유효하지 않은 토큰, 그 외 예외)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="refresh token 만료")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 refresh token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error : {str(e)}")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """현재 로그인한 사용자 확인 (JWT 검증) + Access Token 자동 갱신"""
    try:
        # Access Token 검증
        payload = verify_access_token(token)

        return payload

    # 예외처리(HTTPException, 그 외 예외)
    except HTTPException as e:
        # Access Token이 만료되었을 경우 자동 갱신 로직
        if e.detail == "토큰이 만료되었습니다.":
            raise HTTPException(status_code=401, detail="access token 만료 refresh token 필요")
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error: {str(e)}")