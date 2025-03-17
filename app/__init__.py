from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flasgger import Swagger
import logging
from datetime import datetime, timedelta
from app.database import get_db_connection

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Swagger 설정
    swagger = Swagger(app)
    
    # 시크릿 키 설정
    app.secret_key = 'your-secret-key'  # 실제 운영 환경에서는 환경 변수로 관리

    # 로그인 API
    @app.route('/login', methods=['POST'])
    def login():
        """
        사용자 로그인 API
        ---
        tags:
          - Authentication
        summary: 사용자 로그인을 처리합니다.
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  description: 사용자 이름
                password:
                  type: string
                  description: 비밀번호
        responses:
          200:
            description: 로그인 성공
          401:
            description: 로그인 실패
        """
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return jsonify({
                    "success": False,
                    "message": "사용자 이름과 비밀번호를 모두 입력해주세요."
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT username, password FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and user[1] == password:
                session['user'] = username
                return jsonify({
                    "success": True,
                    "message": "로그인 성공"
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "message": "사용자 이름 또는 비밀번호가 잘못되었습니다."
                }), 401

        except Exception as e:
            logging.error("Login error", exc_info=True)
            return jsonify({
                "success": False,
                "message": "로그인 처리 중 오류가 발생했습니다."
            }), 500

    # 로그아웃 API
    @app.route('/logout', methods=['POST'])
    def logout():
        """
        로그아웃 API
        ---
        tags:
          - Authentication
        summary: 사용자 로그아웃을 처리합니다.
        responses:
          200:
            description: 로그아웃 성공
        """
        session.pop('user', None)
        return jsonify({
            "success": True,
            "message": "로그아웃 성공"
        }), 200

    # 작업 목록 조회 API
    @app.route('/tasks', methods=['GET'])
    def get_tasks():
        """
        작업 목록 조회 API
        ---
        tags:
          - Tasks
        summary: 작업 목록을 조회합니다.
        parameters:
          - name: training_course
            in: query
            type: string
            required: false
            description: 훈련 과정명으로 필터링
        responses:
          200:
            description: 작업 목록 조회 성공
        """
        try:
            training_course = request.args.get('training_course')
            
            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT id, task_name, description FROM task_items"
            params = []

            if training_course:
                query += " WHERE training_course = %s"
                params.append(training_course)

            cursor.execute(query, params)
            tasks = cursor.fetchall()
            
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "tasks": [
                    {
                        "id": task[0],
                        "task_name": task[1],
                        "description": task[2]
                    }
                    for task in tasks
                ]
            }), 200

        except Exception as e:
            logging.error("Error fetching tasks", exc_info=True)
            return jsonify({
                "success": False,
                "message": "작업 목록 조회 중 오류가 발생했습니다."
            }), 500

    # 체크리스트 저장 API
    @app.route('/tasks/checklist', methods=['POST'])
    def save_checklist():
        """
        체크리스트 저장 API
        ---
        tags:
          - Tasks
        summary: 작업 체크리스트를 저장합니다.
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - training_course
                - date
                - checklist
              properties:
                training_course:
                  type: string
                date:
                  type: string
                  format: date
                checklist:
                  type: array
                  items:
                    type: object
                    properties:
                      task_id:
                        type: integer
                      is_checked:
                        type: boolean
        responses:
          200:
            description: 체크리스트 저장 성공
        """
        try:
            data = request.get_json()
            training_course = data.get('training_course')
            date = data.get('date')
            checklist = data.get('checklist')

            if not all([training_course, date, checklist]):
                return jsonify({
                    "success": False,
                    "message": "필수 데이터가 누락되었습니다."
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            # 트랜잭션 시작
            cursor.execute("BEGIN")

            try:
                # 해당 날짜의 기존 데이터 삭제
                cursor.execute("""
                    DELETE FROM task_checklist 
                    WHERE training_course = %s 
                    AND DATE(date) = DATE(%s)
                """, (training_course, date))

                # 새로운 체크리스트 데이터 저장
                for item in checklist:
                    cursor.execute("""
                        INSERT INTO task_checklist 
                        (task_id, training_course, date, is_checked)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        item['task_id'],
                        training_course,
                        date,
                        item['is_checked']
                    ))

                # 트랜잭션 커밋
                cursor.execute("COMMIT")

            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e

            finally:
                cursor.close()
                conn.close()

            return jsonify({
                "success": True,
                "message": "체크리스트가 저장되었습니다."
            }), 200

        except Exception as e:
            logging.error("Error saving checklist", exc_info=True)
            return jsonify({
                "success": False,
                "message": "체크리스트 저장 중 오류가 발생했습니다."
            }), 500

    # 공지사항 목록 조회 API
    @app.route('/notices', methods=['GET'])
    def get_notices():
        """
        공지사항 목록 조회 API
        ---
        tags:
          - Notices
        summary: 공지사항 목록을 조회합니다.
        parameters:
          - name: training_course
            in: query
            type: string
            required: false
            description: 훈련 과정명으로 필터링
        responses:
          200:
            description: 공지사항 목록 조회 성공
        """
        try:
            training_course = request.args.get('training_course')
            
            conn = get_db_connection()
            cursor = conn.cursor()

            query = "SELECT id, title, content, created_at FROM notices"
            params = []

            if training_course:
                query += " WHERE training_course = %s"
                params.append(training_course)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            notices = cursor.fetchall()
            
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "notices": [
                    {
                        "id": notice[0],
                        "title": notice[1],
                        "content": notice[2],
                        "created_at": notice[3].isoformat() if notice[3] else None
                    }
                    for notice in notices
                ]
            }), 200

        except Exception as e:
            logging.error("Error fetching notices", exc_info=True)
            return jsonify({
                "success": False,
                "message": "공지사항 목록 조회 중 오류가 발생했습니다."
            }), 500

    # 공지사항 등록 API
    @app.route('/notices', methods=['POST'])
    def create_notice():
        """
        공지사항 등록 API
        ---
        tags:
          - Notices
        summary: 새로운 공지사항을 등록합니다.
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - title
                - content
                - training_course
              properties:
                title:
                  type: string
                content:
                  type: string
                training_course:
                  type: string
        responses:
          201:
            description: 공지사항 등록 성공
        """
        try:
            data = request.get_json()
            title = data.get('title')
            content = data.get('content')
            training_course = data.get('training_course')

            if not all([title, content, training_course]):
                return jsonify({
                    "success": False,
                    "message": "필수 데이터가 누락되었습니다."
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO notices (title, content, training_course, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (title, content, training_course, datetime.now()))

            notice_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": "공지사항이 등록되었습니다.",
                "id": notice_id
            }), 201

        except Exception as e:
            logging.error("Error creating notice", exc_info=True)
            return jsonify({
                "success": False,
                "message": "공지사항 등록 중 오류가 발생했습니다."
            }), 500

    # 미확인 항목 목록 조회 API
    @app.route('/unchecked/descriptions', methods=['GET'])
    def get_unchecked_descriptions():
        """
        미확인 항목 목록 조회 API
        ---
        tags:
          - Unchecked Items
        summary: 미확인 항목 목록을 조회합니다.
        parameters:
          - name: training_course
            in: query
            type: string
            required: false
            description: 훈련 과정명으로 필터링
          - name: resolved
            in: query
            type: boolean
            required: false
            description: 해결 여부로 필터링
        responses:
          200:
            description: 미확인 항목 목록 조회 성공
        """
        try:
            training_course = request.args.get('training_course')
            resolved = request.args.get('resolved', type=bool)
            
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT id, task_name, description, date, resolved 
                FROM unchecked_descriptions 
                WHERE 1=1
            """
            params = []

            if training_course:
                query += " AND training_course = %s"
                params.append(training_course)

            if resolved is not None:
                query += " AND resolved = %s"
                params.append(resolved)

            query += " ORDER BY date DESC"

            cursor.execute(query, params)
            items = cursor.fetchall()
            
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "items": [
                    {
                        "id": item[0],
                        "task_name": item[1],
                        "description": item[2],
                        "date": item[3].isoformat() if item[3] else None,
                        "resolved": item[4]
                    }
                    for item in items
                ]
            }), 200

        except Exception as e:
            logging.error("Error fetching unchecked descriptions", exc_info=True)
            return jsonify({
                "success": False,
                "message": "미확인 항목 목록 조회 중 오류가 발생했습니다."
            }), 500

    # 미확인 항목 등록 API
    @app.route('/unchecked/descriptions', methods=['POST'])
    def create_unchecked_description():
        """
        미확인 항목 등록 API
        ---
        tags:
          - Unchecked Items
        summary: 새로운 미확인 항목을 등록합니다.
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - task_name
                - description
                - training_course
                - date
              properties:
                task_name:
                  type: string
                description:
                  type: string
                training_course:
                  type: string
                date:
                  type: string
                  format: date
        responses:
          201:
            description: 미확인 항목 등록 성공
        """
        try:
            data = request.get_json()
            task_name = data.get('task_name')
            description = data.get('description')
            training_course = data.get('training_course')
            date = data.get('date')

            if not all([task_name, description, training_course, date]):
                return jsonify({
                    "success": False,
                    "message": "필수 데이터가 누락되었습니다."
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            # 해당 작업의 task_checklist id 조회
            cursor.execute("""
                SELECT tc.id 
                FROM task_checklist tc
                JOIN task_items ti ON tc.task_id = ti.id
                WHERE ti.task_name = %s 
                AND tc.training_course = %s 
                AND DATE(tc.date) = DATE(%s)
            """, (task_name, training_course, date))
            
            result = cursor.fetchone()
            id_task = result[0] if result else None

            cursor.execute("""
                INSERT INTO unchecked_descriptions 
                (task_name, description, training_course, date, resolved, id_task)
                VALUES (%s, %s, %s, %s, false, %s)
                RETURNING id
            """, (task_name, description, training_course, date, id_task))

            item_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": "미확인 항목이 등록되었습니다.",
                "id": item_id
            }), 201

        except Exception as e:
            logging.error("Error creating unchecked description", exc_info=True)
            return jsonify({
                "success": False,
                "message": "미확인 항목 등록 중 오류가 발생했습니다."
            }), 500

    # 미확인 항목 해결 처리 API
    @app.route('/unchecked/descriptions/<int:item_id>/resolve', methods=['POST'])
    def resolve_unchecked_description(item_id):
        """
        미확인 항목 해결 처리 API
        ---
        tags:
          - Unchecked Items
        summary: 미확인 항목을 해결 처리합니다.
        parameters:
          - name: item_id
            in: path
            type: integer
            required: true
            description: 미확인 항목 ID
        responses:
          200:
            description: 미확인 항목 해결 처리 성공
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 트랜잭션 시작
            cursor.execute("BEGIN")

            try:
                # 미확인 항목 조회
                cursor.execute("""
                    SELECT task_name, training_course, date, id_task 
                    FROM unchecked_descriptions 
                    WHERE id = %s
                """, (item_id,))
                
                item = cursor.fetchone()
                if not item:
                    return jsonify({
                        "success": False,
                        "message": "미확인 항목을 찾을 수 없습니다."
                    }), 404

                task_name, training_course, date, id_task = item

                # 체크리스트 항목 체크 처리
                if id_task:
                    cursor.execute("""
                        UPDATE task_checklist 
                        SET is_checked = true 
                        WHERE id = %s
                    """, (id_task,))

                # 미확인 항목 해결 처리
                cursor.execute("""
                    UPDATE unchecked_descriptions 
                    SET resolved = true, resolved_at = %s 
                    WHERE id = %s
                """, (datetime.now(), item_id))

                # 트랜잭션 커밋
                cursor.execute("COMMIT")

            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e

            finally:
                cursor.close()
                conn.close()

            return jsonify({
                "success": True,
                "message": "미확인 항목이 해결 처리되었습니다."
            }), 200

        except Exception as e:
            logging.error("Error resolving unchecked description", exc_info=True)
            return jsonify({
                "success": False,
                "message": "미확인 항목 해결 처리 중 오류가 발생했습니다."
            }), 500

    # 체크율 조회 API
    @app.route('/admin/check_rates', methods=['GET'])
    def get_check_rates():
        """
        체크율 조회 API
        ---
        tags:
          - Admin
        summary: 현재일과 전일의 체크율을 조회합니다.
        parameters:
          - name: training_course
            in: query
            type: string
            required: true
            description: 훈련 과정명
        responses:
          200:
            description: 체크율 조회 성공
        """
        try:
            training_course = request.args.get('training_course')
            if not training_course:
                return jsonify({
                    "success": False,
                    "message": "훈련 과정명이 필요합니다."
                }), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            today = datetime.now().date()
            yesterday = today - timedelta(days=1)

            def calculate_check_rate(date):
                # 총 작업 수 조회
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM task_checklist tc
                    JOIN task_items ti ON tc.task_id = ti.id
                    WHERE tc.training_course = %s AND DATE(tc.date) = %s
                """, (training_course, date))
                total_tasks = cursor.fetchone()[0]

                # 체크된 작업 수 조회 (체크된 항목 + 해결된 미체크 항목)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM task_checklist tc
                    JOIN task_items ti ON tc.task_id = ti.id
                    WHERE tc.training_course = %s 
                    AND DATE(tc.date) = %s
                    AND (tc.is_checked = true OR EXISTS (
                        SELECT 1 FROM unchecked_descriptions ud
                        WHERE ud.task_name = ti.task_name
                        AND ud.training_course = tc.training_course
                        AND DATE(ud.date) = DATE(tc.date)
                        AND ud.resolved = true
                    ))
                """, (training_course, date))
                checked_tasks = cursor.fetchone()[0]

                # 체크율 계산
                check_rate = round((checked_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

                return {
                    "total_tasks": total_tasks,
                    "checked_tasks": checked_tasks,
                    "check_rate": check_rate
                }

            # 오늘과 어제의 체크율 계산
            today_stats = calculate_check_rate(today)
            yesterday_stats = calculate_check_rate(yesterday)

            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "data": {
                    "today": today_stats,
                    "yesterday": yesterday_stats
                }
            }), 200

        except Exception as e:
            logging.error("Error calculating check rates", exc_info=True)
            return jsonify({
                "success": False,
                "message": "체크율 조회 중 오류가 발생했습니다."
            }), 500

    # 통합 체크율 조회 API
    @app.route('/admin/task_status_combined', methods=['GET'])
    def get_combined_task_status():
        """
        통합 체크율 조회 API
        ---
        tags:
          - Admin
        summary: 훈련 과정별 당일, 전날, 월별 누적 체크율을 조회합니다.
        description: |
            각 훈련 과정별로 다음 정보를 반환합니다:
            - 당일 체크율
            - 전날 체크율
            - 월별 누적 체크율
        responses:
          200:
            description: 체크율 조회 성공
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
                      dept:
                        type: string
                      manager_name:
                        type: string
                      daily_check_rate:
                        type: string
                      yesterday_check_rate:
                        type: string
                      monthly_check_rate:
                        type: string
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 현재 월의 첫날과 마지막 날 계산
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            first_date = today.replace(day=1)
            last_date = today

            cursor.execute('''
                WITH monthly_checks AS (
                    SELECT 
                        tc.training_course,
                        ti.dept,
                        ti.manager_name,
                        COUNT(*) AS total_tasks,
                        SUM(CASE 
                            WHEN tc.is_checked THEN 1
                            WHEN EXISTS (
                                SELECT 1 FROM unchecked_descriptions ud
                                WHERE ud.task_name = (
                                    SELECT task_name FROM task_items WHERE id = tc.task_id
                                )
                                AND ud.training_course = tc.training_course
                                AND DATE(ud.date) = DATE(tc.date)
                                AND ud.resolved = TRUE
                            ) THEN 1
                            ELSE 0 
                        END) AS checked_tasks,
                        -- 당일 체크 데이터
                        SUM(CASE WHEN DATE(tc.date) = CURRENT_DATE THEN 1 ELSE 0 END) AS daily_total_tasks,
                        SUM(CASE 
                            WHEN DATE(tc.date) = CURRENT_DATE AND (
                                tc.is_checked OR EXISTS (
                                    SELECT 1 FROM unchecked_descriptions ud
                                    WHERE ud.task_name = (
                                        SELECT task_name FROM task_items WHERE id = tc.task_id
                                    )
                                    AND ud.training_course = tc.training_course
                                    AND DATE(ud.date) = CURRENT_DATE
                                    AND ud.resolved = TRUE
                                )
                            ) THEN 1 
                            ELSE 0 
                        END) AS daily_checked_tasks,
                        -- 전날 체크 데이터
                        SUM(CASE WHEN DATE(tc.date) = CURRENT_DATE - INTERVAL '1 day' THEN 1 ELSE 0 END) AS yesterday_total_tasks,
                        SUM(CASE 
                            WHEN DATE(tc.date) = CURRENT_DATE - INTERVAL '1 day' AND (
                                tc.is_checked OR EXISTS (
                                    SELECT 1 FROM unchecked_descriptions ud
                                    WHERE ud.task_name = (
                                        SELECT task_name FROM task_items WHERE id = tc.task_id
                                    )
                                    AND ud.training_course = tc.training_course
                                    AND DATE(ud.date) = CURRENT_DATE - INTERVAL '1 day'
                                    AND ud.resolved = TRUE
                                )
                            ) THEN 1 
                            ELSE 0 
                        END) AS yesterday_checked_tasks
                    FROM task_checklist tc
                    JOIN training_info ti ON tc.training_course = ti.training_course
                    WHERE DATE(tc.date) BETWEEN %s AND %s
                    GROUP BY tc.training_course, ti.dept, ti.manager_name
                )
                SELECT 
                    training_course,
                    dept,
                    manager_name,
                    total_tasks,
                    checked_tasks,
                    daily_total_tasks,
                    daily_checked_tasks,
                    yesterday_total_tasks,
                    yesterday_checked_tasks
                FROM monthly_checks
            ''', (first_date, last_date))

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            task_status = []
            for row in results:
                training_course = row[0]
                dept = row[1]
                manager_name = row[2] if row[2] else "담당자 없음"
                total_tasks = row[3]
                checked_tasks = row[4] if row[4] else 0
                daily_total_tasks = row[5] if row[5] else 0
                daily_checked_tasks = row[6] if row[6] else 0
                yesterday_total_tasks = row[7] if row[7] else 0
                yesterday_checked_tasks = row[8] if row[8] else 0

                # 월별 누적 체크율 계산
                monthly_check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
                # 당일 체크율 계산
                daily_check_rate = round((daily_checked_tasks / daily_total_tasks) * 100, 2) if daily_total_tasks > 0 else 0
                # 전날 체크율 계산
                yesterday_check_rate = round((yesterday_checked_tasks / yesterday_total_tasks) * 100, 2) if yesterday_total_tasks > 0 else 0

                task_status.append({
                    "training_course": training_course,
                    "dept": dept,
                    "manager_name": manager_name,
                    "daily_check_rate": f"{daily_check_rate}%",
                    "yesterday_check_rate": f"{yesterday_check_rate}%",
                    "monthly_check_rate": f"{monthly_check_rate}%"
                })

            return jsonify({"success": True, "data": task_status}), 200

        except Exception as e:
            logging.error("통합 체크율 조회 중 오류 발생", exc_info=True)
            return jsonify({
                "success": False, 
                "message": "체크율 조회 중 오류가 발생했습니다."
            }), 500

    return app 