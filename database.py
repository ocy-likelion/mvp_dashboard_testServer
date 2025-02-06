# database.py
import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres_password@db:5432/mvp_dashboard')

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()


# 사용자 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

cursor.execute(
    "INSERT INTO users (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING",
    ("1234", "0000")
)


# 공지사항/전달사항 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS notices (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,           -- "공지사항" 또는 "전달사항"을 구분하는 컬럼
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    date TIMESTAMP NOT NULL
)
''')

# 출퇴근 기록 테이블 생성 (훈련과정명 포함)
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    instructor TEXT NOT NULL,
    training_course TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    daily_log BOOLEAN DEFAULT FALSE
)
''')

# 달력 데이터 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS calendar (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    event TEXT NOT NULL
)
''')

# 업무 체크리스트 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS task_checklist (
    id SERIAL PRIMARY KEY,
    task_name TEXT NOT NULL,
    is_checked BOOLEAN DEFAULT FALSE,
    checked_date TEXT
)
''')

# 기본 업무 체크리스트 복원
tasks = [
    "강사 근태 관련 daily 확인",
    "보조강사 RnR 지정 및 실행 여부 확인",
    "운영 계획서와 실제 운영의 일치 여부",
    "커리큘럼 변경 시 사전 공유 진행 여부 (PA팀 / 고용센터)",
    "프로젝트 시수의 프로젝트 강사 참여 수준 및 근태 확인",
    "디스코드 상 상담 및 운영 내역의 아카이브 진행 여부",
    "DM으로 진행된 내용에 대한 팀 내 공유 여부"
]

for task in tasks:
    cursor.execute('INSERT INTO task_checklist (task_name, is_checked, checked_date) VALUES (%s, %s, %s) ON CONFLICT (task_name) DO NOTHING', (task, False, None))

conn.commit()
cursor.close()
conn.close()

print("✅ PostgreSQL 데이터베이스 초기화 및 데이터 복원 완료.")
