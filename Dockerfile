# Dockerfile
FROM python:3.9

# 작업 디렉터리 설정
WORKDIR /app

# 필요 패키지 설치를 위한 파일 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 전체 복사
COPY . .

# 환경 변수 설정 (Flask 앱 정보)
ENV FLASK_APP=flask_api.py
ENV FLASK_ENV=production

# 컨테이너에서 사용될 포트 개방
EXPOSE 5000

# Gunicorn을 사용하여 앱 실행
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "flask_api:app"]