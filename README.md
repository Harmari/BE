# Harmari_BE

할머리 백엔드 레포지토리입니다.

## Tech

- Fastapi + Python 3.12
- MongoDB + Motor
- Pydantic

## Structure

```tsx
// Harmari_BE 폴더구조
├─app/
│  ├─api/
│  │  ├─payment/
│  │  │  └─router.py
│  │  ├─auth.py
│  │  ├─bi.py
│  │  ├─designer.py
│  │  ├─reservation.py
│  │  ├─test.py
│  │  └─user.py
│  │
│  ├─analytics/
│  │  └─metrics_analyzer.py
│  │
│  ├─core/
│  │  ├─config.py
│  │  └─security.py
│  │
│  ├─db/
│  │  └─session.py
│  │
│  ├─middleware/
│  │  ├─cors_middleware.py
│  │  └─metrics_middleware.py
│  │
│  ├─repository/
│  │  ├─designer_repository.py
│  │  └─user_repository.py
│  │
│  ├─scheduler/
│  │  └─schedulers.py
│  │
│  ├─schemas/
│  │  ├─designer_schema.py
│  │  ├─payments_schema.py
│  │  ├─reservation_schema.py
│  │  ├─test_schema.py
│  │  ├─user_schema.py
│  │
│  ├─services/
│  │  ├─auth_service.py
│  │  ├─designer_service.py
│  │  ├─google_service.py
│  │  ├─kakao_pay.py
│  │  ├─reservation_service.py
│  │  ├─test_service.py
│  │  └─user_service.py
│  │
│  └─main.py
│
├─.github/
│  └─workflows/
│     └─main.yml
│
├─requirements.txt
└─.env
```

# Run Locally

1. miniforge 설치, 가상환경 생성

```bash
conda create -m harmari python=3.12 
```

2. 프로젝트 클론

```bash
git clone https://github.com/Harmari/BE.git 
```

3. 프로젝트 진입

```bash
cd BE
```

4. 패키지 설치

```bash
pip install -r requirements.txt
```

5. 서버 실행

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-config logging_config.ini
```
