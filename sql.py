import sqlite3

conn = sqlite3.connect('mvp_dashboard.db')  # 데이터베이스 파일 열기
cursor = conn.cursor()

cursor.execute('SELECT * FROM attendance')  # 출퇴근 기록 조회
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()  # 연결 닫기
