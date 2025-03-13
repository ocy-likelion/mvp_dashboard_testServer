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

@bp.route('/tasks/checklist', methods=['POST'])
def save_task_checklist():
    """
    업무 체크리스트 저장 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트를 저장합니다.
    description: |
      업무 체크리스트를 저장합니다.
      - 같은 날짜(년,월,일)에 데이터가 있는 경우 UPDATE
      - 없는 경우 새로 INSERT
      - 체크되지 않은 항목은 unchecked_descriptions 테이블에서 기존 항목을 삭제 후 새로 등록
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - task_id
            - training_course
            - date
            - is_checked
            - description
          properties:
            task_id:
              type: integer
              description: 업무 ID
            training_course:
              type: string
              description: 훈련 과정명
            date:
              type: string
              format: date
              description: 체크리스트 날짜
            is_checked:
              type: boolean
              description: 체크 여부
            description:
              type: string
              description: 업무 설명
    responses:
      201:
        description: 체크리스트 저장 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      400:
        description: 잘못된 요청
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
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
        date = data.get('date')
        is_checked = data.get('is_checked')
        description = data.get('description')

        if not all([task_id, training_course, date, isinstance(is_checked, bool), description]):
            return jsonify({
                "success": False,
                "message": "필수 입력값이 누락되었습니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 트랜잭션 시작
            cursor.execute("BEGIN")

            # 해당 날짜의 체크리스트 데이터 확인 (시간 제외)
            cursor.execute("""
                SELECT id FROM task_checklist 
                WHERE task_id = %s 
                AND training_course = %s 
                AND DATE(date) = DATE(%s)
            """, (task_id, training_course, date))
            existing_record = cursor.fetchone()

            if existing_record:
                # 기존 데이터가 있는 경우 UPDATE
                cursor.execute("""
                    UPDATE task_checklist 
                    SET is_checked = %s, description = %s, updated_at = NOW()
                    WHERE task_id = %s 
                    AND training_course = %s 
                    AND DATE(date) = DATE(%s)
                    RETURNING id
                """, (is_checked, description, task_id, training_course, date))
            else:
                # 새로운 데이터 INSERT
                cursor.execute("""
                    INSERT INTO task_checklist 
                    (task_id, training_course, date, is_checked, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    RETURNING id
                """, (task_id, training_course, date, is_checked, description))

            checklist_id = cursor.fetchone()[0]

            # 체크되지 않은 항목 처리
            if not is_checked:
                # 기존 미체크 항목 삭제 (resolved가 false이고 같은 날짜인 항목만)
                cursor.execute("""
                    DELETE FROM unchecked_descriptions
                    WHERE task_id = %s 
                    AND training_course = %s 
                    AND DATE(date) = DATE(%s)
                    AND resolved = false
                """, (task_id, training_course, date))
                
                # 새로운 미체크 항목 등록
                cursor.execute("""
                    INSERT INTO unchecked_descriptions 
                    (task_id, training_course, date, description, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (task_id, training_course, date, description))
            else:
                # 체크된 경우 기존의 미해결 미체크 항목 삭제
                cursor.execute("""
                    DELETE FROM unchecked_descriptions
                    WHERE task_id = %s 
                    AND training_course = %s 
                    AND DATE(date) = DATE(%s)
                    AND resolved = false
                """, (task_id, training_course, date))

            # 트랜잭션 커밋
            cursor.execute("COMMIT")

            return jsonify({
                "success": True,
                "message": "체크리스트가 저장되었습니다.",
                "id": checklist_id
            }), 201

        except Exception as e:
            # 오류 발생 시 롤백
            cursor.execute("ROLLBACK")
            raise e

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logging.error("Error saving task checklist", exc_info=True)
        return jsonify({
            "success": False,
            "message": "체크리스트 저장 중 오류가 발생했습니다."
        }), 500

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