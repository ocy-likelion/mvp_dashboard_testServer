import io
import pandas as pd
from flask import Flask, Response, request, jsonify, render_template, redirect, send_file, url_for, session, flash
from flask_cors import CORS  # CORS 추가
from flasgger import Swagger, swag_from
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
    

# ------------------- API 엔드포인트 문서화 시작 -------------------


# healthcheck 라우트 -> DB 확인하기 위함
@app.route('/healthcheck', methods=['GET'])
@swag_from({
    'tags': ['System'],
    'summary': '서버 상태 확인',
    'responses': {
        200: {
            'description': '서버가 정상적으로 작동함',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        }
    }
})
def healthcheck():
    return jsonify({"status": "ok", "message": "Service is running!"}), 200


# 로그인 페이지 및 처리
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    로그인 API
    ---
    tags:
      - Auth
    summary: 로그인 페이지 및 인증 처리
    description: 
      - **GET 요청**: 로그인 페이지 HTML을 반환합니다.  
      - **POST 요청**: 입력한 사용자 정보를 검증하여 로그인 처리를 수행합니다.
    parameters:
      - in: body
        name: body
        required: false
        description: 로그인 시 사용되는 사용자 정보 (POST 요청 시 필요)
        schema:
          type: object
          properties:
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: 로그인 페이지 HTML 반환 (GET 요청)
      302:
        description: 로그인 성공 시 홈 화면으로 리다이렉트
      400:
        description: 로그인 실패 - 잘못된 사용자 정보
    """
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
    """
    로그아웃 API
    ---
    tags:
      - Auth
    summary: 현재 사용자의 세션을 종료하고 로그아웃합니다.
    description: 
      사용자의 로그인 세션을 삭제한 후 로그인 페이지로 리다이렉트합니다.
    responses:
      302:
        description: 로그아웃 후 로그인 페이지로 리다이렉트
    """
    session.pop('user', None)
    return redirect(url_for('login'))


# 홈 화면 (로그인 후 접근 가능한 사원 관리 화면)
@app.route('/', methods=['GET'])
def home():
    """
    홈 화면 API
    ---
    tags:
      - Views
    summary: 홈 화면 접근
    description: 
      - 로그인한 사용자가 홈 화면으로 이동합니다.  
      - 로그인하지 않은 경우 로그인 페이지로 리다이렉트됩니다.
    responses:
      302:
        description: 로그인 상태 확인 후 리다이렉트 (로그인 페이지 또는 홈 화면)
    """
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('front_for_pro'))

# front_for_pro 페이지
@app.route('/front_for_pro', methods=['GET'])
def front_for_pro():
    """
    프론트엔드 개발자용 대시보드 API
    ---
    tags:
      - Views
    summary: 프론트엔드 개발자를 위한 대시보드 페이지 반환
    description: 
      사용자가 로그인한 경우 대시보드 페이지 (front_for_pro.html)을 반환합니다.
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
    responses:
      200:
        description: 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('front_for_pro.html')


# admin 페이지
@app.route('/admin', methods=['GET'])
def admin():
    """
    관리자 대시보드 API
    ---
    tags:
      - Views
    summary: 관리자 대시보드 페이지 반환
    description: 
      사용자가 로그인한 경우 관리자 대시보드 (admin.html)을 반환합니다.  
      로그인하지 않은 경우 로그인 페이지로 이동됩니다.
    responses:
      200:
        description: 관리자 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')


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

# 과정명 선택할 수 있는 드롭다운 설정
@app.route('/training_courses', methods=['GET'])
def get_training_courses():
    """
    training_info 테이블에서 training_course 목록을 가져오는 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 훈련과정 목록 반환
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: string
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT training_course FROM training_info ORDER BY start_date DESC")
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [course[0] for course in courses]  # 리스트 형태로 반환
        }), 200
    except Exception as e:
        logging.error("Error fetching training courses", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch training courses"}), 500


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

# 출퇴근 기록 저장
@app.route('/attendance', methods=['POST'])
def save_attendance():
    """
    출퇴근 기록 저장 API
    ---
    tags:
      - Attendance
    summary: 출퇴근 기록을 저장합니다.
    description: 
      - 강사명이 포함된 출퇴근 기록을 attendance 테이블에 저장합니다.
      - 주강사와 보조강사의 출퇴근 기록을 분리하여 저장합니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - date
            - instructor
            - instructor_name
            - training_course
            - check_in
            - check_out
          properties:
            date:
              type: string
              format: date
              example: "2025-02-12"
            instructor:
              type: string
              example: "1"
              description: "1: 주강사, 2: 보조강사"
            instructor_name:
              type: string
              example: "홍길동"
              description: "강사 이름"
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
              example: true
              description: "일지 작성 여부"
    responses:
      201:
        description: 출퇴근 기록 저장 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 출퇴근 기록 저장 실패
    """
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        date = data.get('date')
        instructor = data.get('instructor')
        instructor_name = data.get('instructor_name')  # ✅ 강사명 추가
        training_course = data.get('training_course')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        daily_log = data.get('daily_log', False)

        if not date or not instructor or not instructor_name or not training_course or not check_in or not check_out:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (date, instructor, instructor_name, training_course, check_in, check_out, daily_log)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (date, instructor, instructor_name, training_course, check_in, check_out, daily_log))
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
        training_course = data.get('training_course')
        date = data.get('date')

        if not issue_text or not training_course or not date:
            return jsonify({"success": False, "message": "이슈, 훈련 과정, 날짜를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO issues (content, date, training_course, created_at, resolved)
            VALUES (%s, %s, %s, NOW(), FALSE)
        ''', (issue_text, date, training_course))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 저장 실패"}), 500



@app.route('/issues', methods=['GET'])
def get_issues():
    """
    해결되지 않은 이슈 목록 조회 API
    ---
    tags:
      - Issues
    summary: "해결되지 않은 이슈 목록을 조회합니다."
    responses:
      200:
        description: 해결되지 않은 이슈 목록 반환
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
                  content:
                    type: string
                  date:
                    type: string
                  training_course:
                    type: string
                  created_at:
                    type: string
                  resolved:
                    type: boolean
      500:
        description: 이슈 목록 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT training_course, json_agg(json_build_object(
                'id', i.id, 
                'content', i.content, 
                'date', i.date, 
                'created_at', i.created_at, 
                'resolved', i.resolved,
                'comments', (
                    SELECT json_agg(json_build_object(
                        'id', ic.id, 
                        'comment', ic.comment, 
                        'created_at', ic.created_at
                    )) FROM issue_comments ic WHERE ic.issue_id = i.id
                )
            )) AS issues
            FROM issues i
            WHERE i.resolved = FALSE  
            GROUP BY training_course
            ORDER BY MIN(i.created_at) DESC;
        ''')
        issues_grouped = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {"training_course": row[0], "issues": row[1]} for row in issues_grouped
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving issues", exc_info=True)
        return jsonify({"success": False, "message": "이슈 목록을 불러오는 중 오류 발생"}), 500


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
    summary: "특정 이슈에 대한 댓글 목록을 조회합니다."
    parameters:
      - name: issue_id
        in: query
        type: integer
        required: true
        description: "조회할 이슈 ID"
    responses:
      200:
        description: 이슈사항의 댓글 목록 반환
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
                  comment:
                    type: string
                  created_at:
                    type: string
      500:
        description: 댓글 조회 실패
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
    summary: "특정 이슈를 해결 처리합니다."
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
        description: 이슈 해결 실패
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

# 이슈사항 전체 다운로드
@app.route('/issues/download', methods=['GET'])
def download_issues():
    """
    이슈사항을 Excel 파일로 다운로드하는 API
    ---
    tags:
      - Issues
    responses:
      200:
        description: 이슈사항을 Excel 파일로 다운로드
      500:
        description: 이슈사항 다운로드 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, content, date, training_course, created_at, resolved FROM issues")
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        # DataFrame 생성
        columns = ["ID", "이슈 내용", "날짜", "훈련 과정", "생성일", "해결됨"]
        df = pd.DataFrame(issues, columns=columns)

        # Excel 파일 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="이슈사항")
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="이슈사항.xlsx"
        )
    except Exception as e:
        logging.error("이슈사항 다운로드 실패", exc_info=True)
        return jsonify({"success": False, "message": "이슈 다운로드 실패"}), 500


@app.route('/irregular_tasks', methods=['GET'])
def get_irregular_tasks():
    """
    비정기 업무 체크리스트 조회 API (가장 최근 상태만 반환)
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트의 가장 최근 상태를 조회합니다."
    responses:
      200:
        description: 비정기 업무 체크리스트 조회 성공
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
        description: 비정기 업무 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT ON (task_name) id, task_name, is_checked, checked_date
            FROM irregular_tasks
            ORDER BY task_name, checked_date DESC
        ''')
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": t[0], "task_name": t[1], "is_checked": t[2], "checked_date": t[3]} for t in tasks]
        }), 200
    except Exception as e:
        logging.error("비정기 업무 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "비정기 업무 조회 실패"}), 500



@app.route('/irregular_tasks', methods=['POST'])
def save_irregular_tasks():
    """
    비정기 업무 체크리스트 추가 저장 API
    기존 데이터를 덮어씌우지 않고 새로운 체크 상태를 추가
    ---
    tags:
      - Irregular Tasks
    summary: "비정기 업무 체크리스트 업데이트 데이터를 저장합니다."
    parameters:
      - in: body
        name: body
        description: "저장할 비정기 업무 체크리스트 업데이트 데이터"
        required: true
        schema:
          type: object
          properties:
            updates:
              type: array
              items:
                type: object
                properties:
                  task_name:
                    type: string
                  is_checked:
                    type: boolean
    responses:
      201:
        description: 비정기 업무 체크리스트 저장 성공
      500:
        description: 비정기 업무 체크리스트 저장 실패
    """
    try:
        data = request.json
        updates = data.get('updates')

        if not updates:
            return jsonify({"success": False, "message": "No data provided"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked")  # True/False 값

            cursor.execute('''
                INSERT INTO irregular_tasks (task_name, is_checked, checked_date)
                VALUES (%s, %s, NOW())
            ''', (task_name, is_checked))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "비정기 업무 체크리스트가 저장되었습니다!"}), 201
    except Exception as e:
        logging.error("비정기 업무 체크리스트 저장 오류", exc_info=True)
        return jsonify({"success": False, "message": "비정기 업무 체크리스트 저장 실패"}), 500


@app.route('/training_info', methods=['POST'])
def save_training_info():
    """
    훈련 과정 정보 저장 API
    ---
    tags:
      - Training Info
    parameters:
      - in: body
        name: body
        description: "훈련 과정 정보를 JSON 형식으로 전달"
        required: true
        schema:
          type: object
          required:
            - training_course
            - start_date
            - end_date
            - dept
          properties:
            training_course:
              type: string
              example: "데이터 분석 스쿨 100기"
            start_date:
              type: string
              format: date
              example: "2025-01-02"
            end_date:
              type: string
              format: date
              example: "2025-06-01"
            dept:
              type: string
              example: "TechSol"
    responses:
      201:
        description: 훈련 과정 저장 성공
      400:
        description: 필수 필드 누락
      500:
        description: 훈련 과정 저장 실패
    """
    try:
        data = request.json
        training_course = data.get("training_course", "").strip()
        start_date = data.get("start_date", "").strip()
        end_date = data.get("end_date", "").strip()
        dept = data.get("dept", "").strip()

        if not training_course or not start_date or not end_date or not dept:
            return jsonify({"success": False, "message": "모든 필드를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO training_info (training_course, start_date, end_date, dept)
            VALUES (%s, %s, %s, %s)
        ''', (training_course, start_date, end_date, dept))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "훈련 과정이 저장되었습니다!"}), 201
    except Exception as e:
        logging.error("Error saving training info", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save training info"}), 500


@app.route('/training_info', methods=['GET'])
def get_training_info():
    """
    훈련 과정 목록 조회 API
    ---
    tags:
      - Training Info
    responses:
      200:
        description: 저장된 훈련 과정 목록 반환
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
                  training_course:
                    type: string
                  start_date:
                    type: string
                  end_date:
                    type: string
                  dept:
                    type: string
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT training_course, start_date, end_date, dept FROM training_info ORDER BY start_date DESC')
        courses = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {"training_course": row[0], "start_date": row[1], "end_date": row[2], "dept": row[3]}
                for row in courses
            ]
        })
    except Exception as e:
        logging.error("Error fetching training info", exc_info=True)
        return jsonify({"success": False, "message": "Failed to fetch training info"}), 500


# ✅ 미체크 항목 불러오기
@app.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미체크 항목 설명 목록 조회 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 미체크 항목 설명 목록을 조회합니다.
    description: 
      데이터베이스에서 해결되지 않은 미체크 항목 목록을 훈련 과정별로 그룹화하여 반환합니다.
    responses:
      200:
        description: 미체크 항목 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                    example: "데이터 분석 스쿨"
                  unchecked_items:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: integer
                          example: 1
                        content:
                          type: string
                          example: "출석 체크 시스템 오류로 인해 확인 불가"
                        created_at:
                          type: string
                          example: "2025-02-12 10:30:00"
                        resolved:
                          type: boolean
                          example: false
                        comments:
                          type: array
                          items:
                            type: object
                            properties:
                              id:
                                type: integer
                                example: 1
                              comment:
                                type: string
                                example: "확인 후 조치 예정입니다."
                              created_at:
                                type: string
                                example: "2025-02-12 11:00:00"
      500:
        description: 미체크 항목 목록 조회 실패
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT training_course, json_agg(json_build_object(
                'id', ud.id, 
                'content', ud.content, 
                'created_at', ud.created_at, 
                'resolved', ud.resolved,
                'comments', (
                    SELECT json_agg(json_build_object(
                        'id', uc.id, 
                        'comment', uc.comment, 
                        'created_at', uc.created_at
                    )) FROM unchecked_comments uc WHERE uc.unchecked_id = ud.id
                )
            )) AS unchecked_items
            FROM unchecked_descriptions ud
            WHERE ud.resolved = FALSE  
            GROUP BY training_course
            ORDER BY MIN(ud.created_at) DESC;
        ''')
        unchecked_grouped = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {"training_course": row[0], "unchecked_items": row[1]} for row in unchecked_grouped
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked descriptions", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 목록을 불러오는 중 오류 발생"}), 500


# ✅ 미체크 항목 저장
@app.route('/unchecked_descriptions', methods=['POST'])
def save_unchecked_description():
    """
    미체크 항목 설명 저장 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 새로운 미체크 항목 설명을 저장합니다.
    description: 
      사용자가 미체크 항목에 대한 설명을 입력하여 데이터베이스에 저장합니다.
    parameters:
      - in: body
        name: body
        description: 미체크 항목 데이터
        required: true
        schema:
          type: object
          required:
            - description
            - training_course
          properties:
            description:
              type: string
              example: "출석 체크 시스템 오류로 인해 확인 불가"
            training_course:
              type: string
              example: "데이터 분석 스쿨"
    responses:
      201:
        description: 미체크 항목 설명 저장 성공
      400:
        description: 필수 데이터 누락
      500:
        description: 서버 오류 발생
    """
    try:
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid JSON format"}), 400

        data = request.get_json()
        description = data.get("description", "").strip()
        training_course = data.get("training_course", "").strip()

        if not description or not training_course:
            return jsonify({"success": False, "message": "설명과 훈련과정명을 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO unchecked_descriptions (content, training_course, created_at, resolved)
            VALUES (%s, %s, NOW(), FALSE)
        ''', (description, training_course))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "미체크 항목 설명이 저장되었습니다!"}), 201

    except Exception as e:
        logging.error("Error saving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500


# ✅ 미체크 항목 댓글 저장
@app.route('/unchecked_comments', methods=['POST'])
def add_unchecked_comment():
    """
    미체크 항목에 댓글 추가 API
    ---
    tags:
      - Unchecked Comments
    summary: 미체크 항목에 대한 댓글을 저장합니다.
    description: 사용자가 특정 미체크 항목에 대해 댓글을 추가할 수 있습니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
            - comment
          properties:
            unchecked_id:
              type: integer
              example: 1
            comment:
              type: string
              example: "확인 후 조치 예정입니다."
    responses:
      201:
        description: 댓글 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        unchecked_id = data.get('unchecked_id')
        comment = data.get('comment')

        if not unchecked_id or not comment:
            return jsonify({"success": False, "message": "미체크 항목 ID와 댓글을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unchecked_comments (unchecked_id, comment, created_at) VALUES (%s, %s, NOW())",
            (unchecked_id, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving unchecked comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500


# ✅ 미체크 항목 해결
@app.route('/unchecked_descriptions/resolve', methods=['POST'])
def resolve_unchecked_description():
    """
    미체크 항목 해결 API
    ---
    tags:
      - Unchecked Descriptions
    summary: 특정 미체크 항목을 해결 상태로 변경합니다.
    description: 사용자가 특정 미체크 항목을 해결했음을 표시합니다.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
          properties:
            unchecked_id:
              type: integer
              example: 1
    responses:
      200:
        description: 미체크 항목 해결 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류 발생
    """
    try:
        data = request.json
        unchecked_id = data.get('unchecked_id')

        if not unchecked_id:
            return jsonify({"success": False, "message": "미체크 항목 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE unchecked_descriptions SET resolved = TRUE WHERE id = %s", (unchecked_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "미체크 항목이 해결되었습니다."}), 200
    except Exception as e:
        logging.error("Error resolving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 해결 실패"}), 500



# ------------------- API 엔드포인트 문서화 끝 -------------------

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)