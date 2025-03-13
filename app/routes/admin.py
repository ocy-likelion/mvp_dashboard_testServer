from flask import Blueprint, jsonify, render_template, redirect, url_for, session
from app.database import get_db_connection
import logging
from datetime import datetime, date, timedelta
import calendar

bp = Blueprint('admin', __name__)

@bp.route('/admin', methods=['GET'])
def admin():
    """
    관리자 대시보드 페이지
    ---
    tags:
      - Admin Views
    summary: 관리자 대시보드 페이지를 반환합니다.
    description: 로그인된 사용자에게 관리자 대시보드 페이지를 제공합니다.
    responses:
      200:
        description: 관리자 대시보드 HTML 페이지
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('admin.html')

@bp.route('/front_for_pro', methods=['GET'])
def front_for_pro():
    """
    프론트엔드 개발자용 대시보드 페이지
    ---
    tags:
      - Admin Views
    summary: 프론트엔드 개발자를 위한 대시보드 페이지를 반환합니다.
    description: 로그인된 사용자에게 프론트엔드 개발자용 대시보드 페이지를 제공합니다.
    responses:
      200:
        description: 프론트엔드 개발자용 대시보드 HTML 페이지
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('front_for_pro.html')

@bp.route('/admin/task_status', methods=['GET'])
def get_task_status():
    """
    당일 체크율 조회 API
    ---
    tags:
      - Admin Task Status
    summary: 훈련 과정별 당일 업무 체크 상태를 조회합니다.
    description: |
      각 훈련 과정별로 당일의 업무 체크 상태를 반환합니다.
      - 체크된 항목과 미체크 항목 중 해결된 항목을 모두 포함하여 계산합니다.
      - 체크율은 소수점 둘째 자리까지 계산됩니다.
    responses:
      200:
        description: 성공적으로 체크율을 조회한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                    description: 훈련 과정명
                  dept:
                    type: string
                    description: 부서명
                  check_rate:
                    type: string
                    description: 체크율 (백분율)
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            message:
              type: string
              description: 오류 메시지
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 당일 체크율 계산 (해결된 미체크 항목 포함)
        cursor.execute('''
            WITH daily_checks AS (
                SELECT 
                    tc.training_course,
                    ti.dept,
                    COUNT(*) AS total_tasks,
                    SUM(CASE 
                        WHEN tc.is_checked THEN 1
                        WHEN EXISTS (
                            SELECT 1 FROM unchecked_descriptions ud
                            WHERE ud.content = (
                                SELECT task_name FROM task_items WHERE id = tc.task_id
                            )
                            AND ud.training_course = tc.training_course
                            AND DATE(ud.created_at) = DATE(tc.checked_date)
                            AND ud.resolved = TRUE
                        ) THEN 1
                        ELSE 0 
                    END) AS checked_tasks
                FROM task_checklist tc
                JOIN training_info ti ON tc.training_course = ti.training_course
                WHERE DATE(tc.checked_date) = CURRENT_DATE
                GROUP BY tc.training_course, ti.dept
            )
            SELECT 
                training_course,
                dept,
                total_tasks,
                checked_tasks
            FROM daily_checks
        ''')
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        task_status = []
        for row in results:
            training_course = row[0]
            dept = row[1]
            total_tasks = row[2]
            checked_tasks = row[3] if row[3] else 0
            check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

            task_status.append({
                "training_course": training_course,
                "dept": dept,
                "check_rate": f"{check_rate}%"
            })

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("Error retrieving task status", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve task status"}), 500

@bp.route('/admin/task_status_combined', methods=['GET'])
def get_combined_task_status():
    """
    통합 체크율 조회 API
    ---
    tags:
      - Admin Task Status
    summary: 훈련 과정별 당일 및 월별 누적 체크율을 조회합니다.
    description: |
      각 훈련 과정별로 당일 체크율과 월별 누적 체크율을 함께 반환합니다.
      - 당일 체크율: 해당일의 체크 완료된 업무 비율
      - 월별 누적 체크율: 해당 월의 전체 업무 중 체크 완료된 업무 비율
      - 체크된 항목과 미체크 항목 중 해결된 항목을 모두 포함하여 계산
      - 체크율은 소수점 둘째 자리까지 계산
    responses:
      200:
        description: 성공적으로 체크율을 조회한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            data:
              type: array
              items:
                type: object
                properties:
                  training_course:
                    type: string
                    description: 훈련 과정명
                  dept:
                    type: string
                    description: 부서명
                  manager_name:
                    type: string
                    description: 담당자 이름
                  daily_check_rate:
                    type: string
                    description: 당일 체크율 (백분율)
                  monthly_check_rate:
                    type: string
                    description: 월별 누적 체크율 (백분율)
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            message:
              type: string
              description: 오류 메시지
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 현재 월의 첫날과 마지막 날 계산
        today = date.today()
        _, last_day = calendar.monthrange(today.year, today.month)
        first_date = date(today.year, today.month, 1)
        last_date = date(today.year, today.month, last_day)

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
                            WHERE ud.content = (
                                SELECT task_name FROM task_items WHERE id = tc.task_id
                            )
                            AND ud.training_course = tc.training_course
                            AND DATE(ud.created_at) = DATE(tc.checked_date)
                            AND ud.resolved = TRUE
                        ) THEN 1
                        ELSE 0 
                    END) AS checked_tasks,
                    SUM(CASE WHEN DATE(tc.checked_date) = CURRENT_DATE THEN 1 ELSE 0 END) AS daily_total_tasks,
                    SUM(CASE 
                        WHEN DATE(tc.checked_date) = CURRENT_DATE AND (
                            tc.is_checked OR EXISTS (
                                SELECT 1 FROM unchecked_descriptions ud
                                WHERE ud.content = (
                                    SELECT task_name FROM task_items WHERE id = tc.task_id
                                )
                                AND ud.training_course = tc.training_course
                                AND DATE(ud.created_at) = CURRENT_DATE
                                AND ud.resolved = TRUE
                            )
                        ) THEN 1 
                        ELSE 0 
                    END) AS daily_checked_tasks
                FROM task_checklist tc
                JOIN training_info ti ON tc.training_course = ti.training_course
                WHERE DATE(tc.checked_date) BETWEEN %s AND %s
                GROUP BY tc.training_course, ti.dept, ti.manager_name
            )
            SELECT 
                training_course,
                dept,
                manager_name,
                total_tasks,
                checked_tasks,
                daily_total_tasks,
                daily_checked_tasks
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

            # 월별 누적 체크율 계산
            monthly_check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
            # 당일 체크율 계산
            daily_check_rate = round((daily_checked_tasks / daily_total_tasks) * 100, 2) if daily_total_tasks > 0 else 0

            task_status.append({
                "training_course": training_course,
                "dept": dept,
                "manager_name": manager_name,
                "daily_check_rate": f"{daily_check_rate}%",
                "monthly_check_rate": f"{monthly_check_rate}%"
            })

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("Error retrieving combined task status", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve task status"}), 500 

@bp.route('/admin/previous_day_task_status', methods=['GET'])
def get_previous_day_task_status():
    """
    전날 체크율 조회 API
    ---
    tags:
      - Admin Task Status
    summary: 전날의 업무 체크율을 조회합니다.
    description: |
      전날의 전체 업무 대비 체크 완료된 업무의 비율을 계산하여 반환합니다.
      - 체크된 항목과 미체크 항목 중 해결된 항목을 모두 포함하여 계산
      - 체크율은 소수점 둘째 자리까지 계산
      - 데이터가 없는 경우 모든 값이 0으로 반환됨
    responses:
      200:
        description: 성공적으로 체크율을 조회한 경우
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            data:
              type: object
              properties:
                total_tasks:
                  type: integer
                  description: 전체 업무 수
                checked_tasks:
                  type: integer
                  description: 체크 완료된 업무 수
                check_rate:
                  type: number
                  format: float
                  description: 체크율 (백분율)
                date:
                  type: string
                  format: date
                  description: 전날 날짜 (YYYY-MM-DD)
      500:
        description: 서버 오류 발생
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            message:
              type: string
              description: 오류 메시지
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # WITH 절을 사용하여 전날의 체크율 계산
        cursor.execute("""
            WITH task_counts AS (
                SELECT 
                    COUNT(DISTINCT tc.task_id) as total_tasks,
                    COUNT(DISTINCT CASE 
                        WHEN tc.is_checked = TRUE OR 
                             EXISTS (
                                SELECT 1 
                                FROM unchecked_descriptions ud 
                                WHERE ud.id_task = tc.id 
                                AND ud.resolved = TRUE
                             )
                        THEN tc.task_id 
                    END) as checked_tasks
                FROM task_checklist tc
                WHERE DATE(tc.checked_date) = CURRENT_DATE - INTERVAL '1 day'
            )
            SELECT 
                total_tasks,
                checked_tasks,
                CASE 
                    WHEN total_tasks = 0 THEN 0
                    ELSE ROUND((checked_tasks::float / total_tasks::float) * 100, 2)
                END as check_rate
            FROM task_counts;
        """)

        result = cursor.fetchone()
        
        if result:
            total_tasks, checked_tasks, check_rate = result
            response_data = {
                "success": True,
                "data": {
                    "total_tasks": total_tasks,
                    "checked_tasks": checked_tasks,
                    "check_rate": check_rate,
                    "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                }
            }
        else:
            response_data = {
                "success": True,
                "data": {
                    "total_tasks": 0,
                    "checked_tasks": 0,
                    "check_rate": 0,
                    "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                }
            }

        return jsonify(response_data), 200

    except Exception as e:
        logging.error("Error retrieving previous day task status", exc_info=True)
        return jsonify({"success": False, "message": "전날 체크율 조회 중 오류가 발생했습니다."}), 500

    finally:
        cursor.close()
        conn.close() 