import io
import pandas as pd
from flask import Flask, Response, request, jsonify, render_template, redirect, send_file, url_for, session, flash
from flask_cors import CORS  # CORS 추가
from flasgger import Swagger
from dotenv import load_dotenv
import os, psycopg2
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.ERROR)

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your-secret-key'  # 실제 운영 환경에서는 안전한 난수를 사용하세요.
CORS(app)  # 전체 애플리케이션에 대해 CORS 허용
app.config['SWAGGER'] = {
    'title': "업무 관리 대시보드 API",
    'uiversion': 3,  # 최신 Swagger UI 사용
    'specs_route': "/apidocs/"  # Swagger UI 접근 경로 설정
}
swagger = Swagger(app)  # Flasgger 초기화

# ✅ .env 파일에서 환경 변수 로드
load_dotenv()

# PostgreSQL 데이터베이스 연결 함수
def get_db_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")  # ✅ 환경 변수 읽기
    
    # 환경 변수가 없으면 강제 설정 (백업용, 하지만 로컬에서는 .env가 있으므로 필요 없음)
    if not DATABASE_URL:
        DATABASE_URL = "postgresql://cysss:QJxyP6VuLMAZykzMyeRtO3QJUGMf0aWA@dpg-cuim9pogph6c73acoj0g-a/mvp_dashboard"
    
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# 사용자 로그인 검증 함수 (users 테이블에서 username과 password 확인)
def check_login(username, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user is not None
    except Exception as e:
        logging.error("Error checking login", exc_info=True)
        return False

# healthcheck 라우트 -> DB 확인하기 위함
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "ok", "message": "Service is running!"}), 200


# 로그인 페이지 및 처리
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if check_login(username, password):
            session['user'] = username
            return redirect(url_for('home'))
        else:
            flash("로그인 정보가 올바르지 않습니다.")
            return render_template('login.html')
    else:
        return render_template('login.html')

# 로그아웃 기능
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# 홈 화면 (로그인 후 접근 가능한 사원 관리 화면)
@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('front_for_pro'))

# front_for_pro 페이지
@app.route('/front_for_pro')
def front_for_pro():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('front_for_pro.html')

# admin 페이지
@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# ------------------- API 엔드포인트 문서화 시작 -------------------

@app.route('/notices', methods=['GET'])
def get_notices():
    """
    공지사항 및 전달사항 조회 API
    ---
    tags:
      - Notices
    responses:
      200:
        description: 공지사항 및 전달사항 데이터를 포함한 응답
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                notices:
                  type: array
                  description: 모든 공지사항 데이터
                remarks:
                  type: array
                  description: "전달사항 타입인 공지 데이터"
      500:
        description: 공지사항을 불러오는 데 실패함
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 공지사항과 전달사항을 모두 불러옴
        cursor.execute('SELECT * FROM notices ORDER BY date DESC')
        notices = cursor.fetchall()
        cursor.close()
        conn.close()
        # '전달사항'만 필터링하여 별도로 제공 (notice[1]가 타입으로 가정)
        return jsonify({
            "success": True,
            "data": {
                "notices": notices,
                "remarks": [notice for notice in notices if notice[1] == '전달사항']
            }
        }), 200
    except Exception as e:
        logging.error("Error retrieving notices", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve notices"}), 500

@app.route('/attendance', methods=['GET'])
def get_attendance():
    """
    출퇴근 기록 파일 다운로드 API
    ---
    tags:
      - Attendance
    parameters:
      - name: format
        in: query
        type: string
        required: false
        description: "csv 또는 excel 형식으로 다운로드 (기본값: JSON 반환)"
    responses:
      200:
        description: 출퇴근 기록 데이터 반환 또는 파일 다운로드
      500:
        description: 데이터 조회 실패
    """
    try:
        format_type = request.args.get('format', 'json')  # 기본값 JSON
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, date, instructor, training_course, check_in, check_out, daily_log FROM attendance ORDER BY date DESC')
        attendance_records = cursor.fetchall()
        cursor.close()
        conn.close()

        columns = ['ID', '날짜', '강사', '훈련과정', '출근 시간', '퇴근 시간', '일지 작성 완료']
        df = pd.DataFrame(attendance_records, columns=columns)

        # ✅ JSON 응답 (기본값)
        if format_type == 'json':
            return jsonify({"success": True, "data": df.to_dict(orient='records')}), 200

        # ✅ Excel 파일 다운로드
        elif format_type == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="출퇴근 기록")
            output.seek(0)
            return send_file(
                output,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="출퇴근_기록.xlsx"
            )

        else:
            return jsonify({"success": False, "message": "잘못된 포맷 요청"}), 400

    except Exception as e:
        logging.error("출퇴근 기록 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "출퇴근 기록 조회 실패"}), 500


@app.route('/attendance', methods=['POST'])
def save_attendance():
    """
    출퇴근 기록 저장 API
    ---
    tags:
      - Attendance
    parameters:
      - in: body
        name: body
        description: 출퇴근 기록 데이터를 JSON 형식으로 전달
        required: true
        schema:
          type: object
          required:
            - date
            - instructor
            - training_course
            - check_in
            - check_out
          properties:
            date:
              type: string
              example: "2025-02-03"
            instructor:
              type: string
              example: "1"
            training_course:
              type: string
              example: "데이터 분석 스쿨"
            check_in:
              type: string
              example: "09:00"
            check_out:
              type: string
              example: "18:00"
            daily_log:
              type: boolean
              example: false
    responses:
      201:
        description: 출퇴근 기록 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: 필수 필드 누락
      500:
        description: 출퇴근 기록 저장 실패
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        date = data.get('date')
        instructor = data.get('instructor')
        training_course = data.get('training_course')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        daily_log = data.get('daily_log', False)

        if not date or not instructor or not training_course or not check_in or not check_out:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (date, instructor, training_course, check_in, check_out, daily_log)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (date, instructor, training_course, check_in, check_out, daily_log))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Attendance saved!"}), 201
    except Exception as e:
        logging.error("Error saving attendance", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save attendance"}), 500

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """
    업무 체크리스트 조회 API
    ---
    tags:
      - Tasks
    responses:
      200:
        description: 업무 체크리스트 데이터를 반환함
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
                  checked_date:
                    type: string
      500:
        description: 업무 체크리스트 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, task_name, is_checked, checked_date FROM task_checklist')
        tasks = [
            {
                "id": row[0],
                "task_name": row[1],
                "is_checked": bool(row[2]),
                "checked_date": row[3] if row[3] else "미체크"
            }
            for row in cursor.fetchall()
        ]
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": tasks}), 200
    except Exception as e:
        logging.error("Error retrieving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve tasks"}), 500

@app.route('/tasks', methods=['POST'])
def save_tasks():
    """
    업무 체크리스트 저장 API (새로운 기록 추가, 기존 데이터는 유지)
    ---
    tags:
      - Tasks
    parameters:
      - in: body
        name: body
        description: 저장할 체크리스트 업데이트 데이터
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                required:
                  - task_name
                  - is_checked
                properties:
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
    responses:
      201:
        description: 업무 체크리스트 업데이트 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: 업데이트할 데이터 없음
      500:
        description: 업무 체크리스트 업데이트 실패
    """
    try:
        data = request.json
        updates = data.get("updates")

        if not updates:
            return jsonify({"success": False, "message": "No data provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked")  # True/False 값

            # ✅ 기존 데이터를 유지하면서 새로운 체크 기록을 추가하는 방식
            cursor.execute('''
                INSERT INTO task_checklist (task_name, is_checked, checked_date)
                VALUES (%s, %s, %s)
            ''', (task_name, is_checked, datetime.now().strftime("%Y-%m-%d")))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Tasks saved successfully!"}), 201
    except Exception as e:
        logging.error("Error saving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save tasks"}), 500

@app.route('/remarks', methods=['POST'])
def save_remarks():
    """
    전달사항 저장 API
    ---
    tags:
      - Remarks
    parameters:
      - in: body
        name: body
        description: 저장할 전달사항 데이터
        required: true
        schema:
          type: object
          required:
            - remarks
          properties:
            remarks:
              type: string
              example: "전달사항 내용 예시"
    responses:
      201:
        description: 전달사항 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: 전달사항 데이터 누락
      500:
        description: 전달사항 저장 실패
    """
    try:
        data = request.json
        remarks = data.get('remarks')
        if not remarks:
            return jsonify({"success": False, "message": "Remarks are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notices (type, title, content, date)
            VALUES (%s, %s, %s, %s)
        ''', ("전달사항", "전달사항 제목", remarks, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Remarks saved!"}), 201
    except Exception as e:
        logging.error("Error saving remarks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save remarks"}), 500

@app.route('/issues', methods=['POST'])
def save_issue():
    """
    이슈사항 저장 API
    ---
    tags:
      - Issues
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            issue:
              type: string
              example: "강의 자료 오류 발생"
    responses:
      201:
        description: 이슈사항 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        issue_text = data.get('issue')

        if not issue_text:
            return jsonify({"success": False, "message": "이슈 내용을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO issues (content, created_at, resolved) VALUES (%s, %s, FALSE)", (issue_text, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈 사항이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 사항 저장 실패"}), 500

@app.route('/issues', methods=['GET'])
def get_issues():
    """
    해결되지 않은 이슈 목록 조회 API
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, content, created_at, resolved FROM issues ORDER BY created_at DESC")
        issues = cursor.fetchall()

        cursor.close()
        conn.close()

        logging.info(f"📌 조회된 이슈 개수: {len(issues)}")  # ✅ 로그 추가
        logging.info(f"📌 이슈 데이터: {issues}")  # ✅ 디버깅용 로그 추가

        return jsonify({
            "success": True,
            "data": [{"id": row[0], "content": row[1], "created_at": row[2], "resolved": row[3]} for row in issues]
        }), 200

    except Exception as e:
        logging.error("❌ 이슈 목록 조회 실패", exc_info=True)
        return jsonify({"success": False, "message": f"이슈 목록을 불러오는 중 오류 발생: {str(e)}"}), 500


# 이슈에 대한 댓글 달기
@app.route('/issues/comments', methods=['POST'])
def add_issue_comment():
    """
    이슈사항에 대한 댓글 저장 API
    ---
    tags:
      - Issues
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            issue_id:
              type: integer
              example: 1
            comment:
              type: string
              example: "이슈에 대한 답변입니다."
    responses:
      201:
        description: 댓글 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        issue_id = data.get('issue_id')
        comment = data.get('comment')

        if not issue_id or not comment:
            return jsonify({"success": False, "message": "이슈 ID와 댓글 내용을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO issue_comments (issue_id, comment, created_at) VALUES (%s, %s, NOW())",
            (issue_id, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500

# 이슈에 대한 댓글 조회
@app.route('/issues/comments', methods=['GET'])
def get_issue_comments():
    """
    이슈사항의 댓글 조회 API
    ---
    tags:
      - Issues
    parameters:
      - name: issue_id
        in: query
        type: integer
        required: true
        description: "조회할 이슈 ID"
    responses:
      200:
        description: 이슈사항의 댓글 목록 반환
      500:
        description: 서버 오류
    """
    try:
        issue_id = request.args.get('issue_id')

        if not issue_id:
            return jsonify({"success": False, "message": "이슈 ID를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, comment, created_at FROM issue_comments WHERE issue_id = %s ORDER BY created_at ASC",
            (issue_id,)
        )
        comments = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": row[0], "comment": row[1], "created_at": row[2]} for row in comments]
        }), 200
    except Exception as e:
        logging.error("Error retrieving issue comments", exc_info=True)
        return jsonify({"success": False, "message": "댓글 조회 실패"}), 500

# 해결된 이슈 클릭
@app.route('/issues/resolve', methods=['POST'])
def resolve_issue():
    """
    이슈 해결 API
    ---
    tags:
      - Issues
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            issue_id:
              type: integer
              example: 1
    responses:
      200:
        description: 이슈 해결 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        issue_id = data.get('issue_id')

        if not issue_id:
            return jsonify({"success": False, "message": "이슈 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE issues SET resolved = TRUE WHERE id = %s",
            (issue_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 해결되었습니다."}), 200
    except Exception as e:
        logging.error("Error resolving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 해결 실패"}), 500


# ✅ 미체크 항목 설명 저장
@app.route('/unchecked_descriptions', methods=['POST'])
def save_unchecked_description():
    """
    미체크 항목 설명 저장 API
    ---
    tags:
      - Unchecked Descriptions
    parameters:
      - in: body
        name: body
        description: 미체크된 항목에 대한 설명을 JSON 형식으로 전달
        required: true
        schema:
          type: object
          required:
            - description
          properties:
            description:
              type: string
              example: "출석 체크 시스템 오류로 인해 확인 불가"
    responses:
      201:
        description: 미체크 항목 설명 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Unchecked description saved successfully!"
      400:
        description: 설명이 제공되지 않음
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "No description provided"
      500:
        description: 서버 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Failed to save unchecked description"
    """
    try:
        data = request.json
        description = data.get("description", "")

        if not description:
            return jsonify({"success": False, "message": "No description provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO unchecked_descriptions (content, created_at)
            VALUES (%s, NOW())
        ''', (description,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Unchecked description saved successfully!"}), 201
    except Exception as e:
        logging.error("Error saving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save unchecked description"}), 500


# ✅ 미체크 항목 설명 불러오기
@app.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미체크 항목 설명 조회 API
    ---
    tags:
      - Unchecked Descriptions
    responses:
      200:
        description: 저장된 미체크 항목 설명 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: string
              example: ["출석 체크 시스템 오류로 인해 확인 불가", "네트워크 문제로 인한 미체크"]
      500:
        description: 서버 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Failed to fetch unchecked descriptions"
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT content FROM unchecked_descriptions ORDER BY created_at DESC')
        descriptions = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": [desc[0] for desc in descriptions]})  # ✅ 데이터를 리스트로 변환하여 반환
    except Exception as e:
        logging.error("Error fetching unchecked descriptions", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch unchecked descriptions"}), 500


@app.route('/irregular_tasks', methods=['GET'])
def get_irregular_tasks():
    """
    비정기 업무 체크리스트 조회 API
    ---
    tags:
      - Irregular Tasks
    responses:
      200:
        description: 비정기 업무 리스트 반환
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, task_name, is_checked FROM irregular_tasks ORDER BY created_at DESC')
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": t[0], "task_name": t[1], "is_checked": t[2]} for t in tasks]
        }), 200
    except Exception as e:
        logging.error("비정기 업무 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "비정기 업무 조회 실패"}), 500


@app.route('/irregular_tasks', methods=['POST'])
def save_irregular_tasks():
    """
    비정기 업무 체크리스트 상태 업데이트 API (여러 개 한 번에 저장)
    """
    try:
        data = request.json
        updates = data.get('updates')

        if not updates:
            return jsonify({"success": False, "message": "No data provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        for update in updates:
            task_id = update.get("id")
            is_checked = update.get("is_checked")

            cursor.execute(
                'UPDATE irregular_tasks SET is_checked = %s WHERE id = %s',
                (is_checked, task_id)
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "비정기 업무 체크리스트 저장 완료!"}), 201
    except Exception as e:
        logging.error("비정기 업무 체크리스트 저장 오류", exc_info=True)
        return jsonify({"success": False, "message": "비정기 업무 체크리스트 저장 실패"}), 500



# ------------------- API 엔드포인트 문서화 끝 -------------------

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)