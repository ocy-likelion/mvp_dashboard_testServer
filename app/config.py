import os
from dotenv import load_dotenv
from datetime import timedelta

# .env 파일에서 환경 변수 로드
load_dotenv()

# PostgreSQL 데이터베이스 연결 설정
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://cysss:QJxyP6VuLMAZykzMyeRtO3QJUGMf0aWA@dpg-cuim9pogph6c73acoj0g-a/mvp_dashboard"

# 서버 포트 설정
PORT = int(os.getenv("PORT", 10000))  # 기본값을 10000으로 설정

# 세션 설정
SESSION_CONFIG = {
    'PERMANENT_SESSION_LIFETIME': timedelta(minutes=1),  # 1분 세션 타임아웃 (테스트용)
    'SESSION_COOKIE_SECURE': True,  # HTTPS에서만 쿠키 전송
    'SESSION_COOKIE_HTTPONLY': True,  # JS에서 쿠키 접근 방지
    'SESSION_COOKIE_SAMESITE': 'Lax'  # CSRF 방지
}