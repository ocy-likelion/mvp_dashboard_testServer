# blueprints/unchecked.py
from flask import Blueprint, request, jsonify
from database import get_db_connection
import logging

unchecked_bp = Blueprint('unchecked', __name__)

@unchecked_bp.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """미체크 항목 조회 API"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, content, action_plan, training_course, created_at, resolved FROM unchecked_descriptions WHERE resolved = FALSE ORDER BY created_at DESC')
        unchecked_items = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {"id": row[0], "content": row[1], "action_plan": row[2], "training_course": row[3], "created_at": row[4], "resolved": row[5]}
                for row in unchecked_items
            ]
        }), 200
    except Exception as e:
        logging.error("미체크 항목 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 조회 실패"}), 500


@unchecked_bp.route('/task_status', methods=['GET'])
def get_task_status():
    """훈련 과정별 당일 체크율 조회 API"""
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

        task_status = [
            {
                "training_course": row[0],
                "dept": row[1],
                "check_rate": f"{round((row[3] / row[2]) * 100, 2) if row[2] > 0 else 0}%"
            }
            for row in results
        ]

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("당일 체크율 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "체크율 조회 실패"}), 500


@unchecked_bp.route('/task_status_overall', methods=['GET'])
def get_overall_task_status():
    """훈련 과정별 전체 체크율 조회 API"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT tc.training_course, ti.dept, 
                   COUNT(*) AS total_tasks, 
                   SUM(CASE WHEN tc.is_checked THEN 1 ELSE 0 END) AS checked_tasks
            FROM task_checklist tc
            JOIN training_info ti ON tc.training_course = ti.training_course
            GROUP BY tc.training_course, ti.dept
        ''')

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        task_status = [
            {
                "training_course": row[0],
                "dept": row[1],
                "check_rate": f"{round((row[3] / row[2]) * 100, 2) if row[2] > 0 else 0}%"
            }
            for row in results
        ]

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("전체 체크율 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "체크율 조회 실패"}), 500


@unchecked_bp.route('/task_status_combined', methods=['GET'])
def get_combined_task_status():
    """훈련 과정별 당일 및 전체 체크율 + 담당자 정보 조회 API"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT tc.training_course, ti.dept, ti.manager_name,
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

        task_status = [
            {
                "training_course": row[0],
                "dept": row[1],
                "manager_name": row[2] if row[2] else "담당자 없음",
                "daily_check_rate": f"{round((row[5] / row[6]) * 100, 2) if row[6] > 0 else 0}%",
                "overall_check_rate": f"{round((row[3] / row[2]) * 100, 2) if row[2] > 0 else 0}%"
            }
            for row in results
        ]

        return jsonify({"success": True, "data": task_status}), 200
    except Exception as e:
        logging.error("당일 및 전체 체크율 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "체크율 조회 실패"}), 500
