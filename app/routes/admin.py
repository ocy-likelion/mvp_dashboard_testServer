from flask import Blueprint, jsonify, render_template, redirect, url_for, session
from app.database import get_db_connection
import logging

bp = Blueprint('admin', __name__)

@bp.route('/admin', methods=['GET'])
def admin():
    """
    관리자 대시보드 API
    ---
    tags:
      - Views
    summary: 관리자 대시보드 페이지 반환
    responses:
      200:
        description: 관리자 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('admin.html')

@bp.route('/front_for_pro', methods=['GET'])
def front_for_pro():
    """
    프론트엔드 개발자용 대시보드 API
    ---
    tags:
      - Views
    summary: 프론트엔드 개발자를 위한 대시보드 페이지 반환
    responses:
      200:
        description: 대시보드 HTML 페이지 반환
      302:
        description: 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    """
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('front_for_pro.html')

@bp.route('/admin/task_status', methods=['GET'])
def get_task_status():
    """
    훈련 과정별 업무 체크리스트의 체크율을 조회하는 API
    ---
    tags:
      - Admin
    summary: "훈련 과정별 업무 체크 상태 조회"
    responses:
      200:
        description: 훈련 과정별 체크율 데이터를 반환
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT tc.training_course, ti.dept, 
                   COUNT(*) AS total_tasks, 
                   SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            WHERE DATE(tc.checked_date) = CURRENT_DATE
            GROUP BY tc.training_course, ti.dept
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
    훈련 과정별 업무 체크리스트의 체크율(당일 및 전체)을 조회하는 API
    ---
    tags:
      - Admin
    summary: "훈련 과정별 업무 체크율 조회"
    responses:
      200:
        description: 훈련 과정별 체크율 데이터 반환
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                tc.training_course, 
                ti.dept,
                ti.manager_name,
                COUNT(*) AS total_tasks,
                SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks,
                SUM(CASE WHEN tc.is_checked AND DATE(tc.checked_date) = CURRENT_DATE THEN 1 ELSE 0 END) AS daily_checked_tasks,
                COUNT(CASE WHEN DATE(tc.checked_date) = CURRENT_DATE THEN 1 ELSE NULL END) AS daily_total_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            GROUP BY tc.training_course, ti.dept, ti.manager_name
        ''')

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
            daily_checked_tasks = row[5] if row[5] else 0
            daily_total_tasks = row[6] if row[6] else 0

            overall_check_rate = round((checked_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
            daily_check_rate = round((daily_checked_tasks / daily_total_tasks) * 100, 2) if daily_total_tasks > 0 else 0

            task_status.append({
                "training_course": training_course,
                "dept": dept,
                "manager_name": manager_name,
                "daily_check_rate": f"{daily_check_rate}%",
                "overall_check_rate": f"{overall_check_rate}%"
            })

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("Error retrieving combined task status", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve task status"}), 500 