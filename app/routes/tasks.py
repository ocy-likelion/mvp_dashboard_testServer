from flask import Blueprint, request, jsonify, session
from app.database import get_db_connection
import logging
from datetime import datetime, date

bp = Blueprint('tasks', __name__)

@bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    업무 목록 조회 API
    ---
    tags:
      - Tasks
    summary: 훈련 과정별 업무 목록을 조회합니다.
    description: |
      특정 훈련 과정의 모든 업무 항목을 조회합니다.
      - 훈련 과정명을 쿼리 파라미터로 받아 해당 과정의 업무 목록 반환
      - 각 업무의 체크 상태도 함께 반환
    parameters:
      - name: training_course
        in: query
        type: string
        required: true
        description: 훈련 과정명
    responses:
      200:
        description: 업무 목록 조회 성공
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
                  task_id:
                    type: integer
                    description: 업무 ID
                  task_name:
                    type: string
                    description: 업무명
                  is_checked:
                    type: boolean
                    description: 체크 여부
      500:
        description: 서버 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    try:
        training_course = request.args.get('training_course')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ti.id, ti.task_name, 
                   COALESCE(tc.is_checked, FALSE) as is_checked,
                   tc.id as checklist_id
            FROM task_items ti
            LEFT JOIN task_checklist tc ON ti.id = tc.task_id 
                AND tc.training_course = %s 
                AND DATE(tc.checked_date) = CURRENT_DATE
            ORDER BY ti.id;
        ''', (training_course,))
        
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{
                "task_id": row[0],
                "task_name": row[1],
                "is_checked": row[2],
                "checklist_id": row[3]
            } for row in tasks]
        }), 200

    except Exception as e:
        logging.error("Error retrieving tasks", exc_info=True)
        return jsonify({"success": False, "message": "업무 목록을 불러오는 중 오류가 발생했습니다."}), 500

@bp.route('/tasks', methods=['POST'])
def save_tasks():
    """
    업무 체크리스트 저장 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 저장
    """
    if 'user' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    user_id = session['user']['username']

    data = request.json
    updates = data.get("updates")
    training_course = data.get("training_course")

    if not updates or not training_course:
        return jsonify({"success": False, "message": "No data provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for update in updates:
            task_name = update.get("task_name")
            is_checked = update.get("is_checked", False)

            cursor.execute("SELECT id FROM task_items WHERE task_name = %s", (task_name,))
            task_item = cursor.fetchone()
            if not task_item:
                return jsonify({"success": False, "message": f"Task '{task_name}' does not exist"}), 400

            task_id = task_item[0]

            cursor.execute("""
                INSERT INTO task_checklist (task_id, training_course, is_checked, checked_date, username)
                VALUES (%s, %s, %s, NOW(), %s);
            """, (task_id, training_course, is_checked, user_id))

        conn.commit()
        return jsonify({"success": True, "message": "Tasks saved successfully!"}), 201

    except Exception as e:
        logging.error("Error saving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save tasks"}), 500

    finally:
        cursor.close()
        conn.close()

@bp.route('/tasks/check', methods=['POST'])
def check_task():
    """
    업무 체크 상태 변경 API
    ---
    tags:
      - Tasks
    summary: 특정 업무의 체크 상태를 변경합니다.
    description: |
      업무의 체크 상태를 변경하고 기록합니다.
      - 체크되지 않은 업무를 체크하거나, 체크된 업무를 체크 해제
      - 변경 시 task_checklist 테이블에 기록 저장
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - task_id
            - training_course
            - is_checked
          properties:
            task_id:
              type: integer
              description: 업무 ID
            training_course:
              type: string
              description: 훈련 과정명
            is_checked:
              type: boolean
              description: 체크 상태 (true/false)
    responses:
      200:
        description: 체크 상태 변경 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            message:
              type: string
              description: 성공 메시지
      500:
        description: 서버 오류
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        training_course = data.get('training_course')
        is_checked = data.get('is_checked')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO task_checklist (task_id, training_course, is_checked, checked_date)
            VALUES (%s, %s, %s, CURRENT_DATE)
            ON CONFLICT (task_id, training_course, checked_date)
            DO UPDATE SET is_checked = %s;
        ''', (task_id, training_course, is_checked, is_checked))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "업무 체크 상태가 변경되었습니다."
        }), 200

    except Exception as e:
        logging.error("Error checking task", exc_info=True)
        return jsonify({"success": False, "message": "업무 체크 상태 변경 중 오류가 발생했습니다."}), 500 