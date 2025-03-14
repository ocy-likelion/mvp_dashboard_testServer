from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

# Blueprint 정의
tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

def init_tasks_routes(app):
    """
    작업 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(tasks_bp)

@tasks_bp.route('/', methods=['GET'])
def get_tasks():
    """
    작업 목록 조회 API
    ---
    tags:
      - Tasks
    summary: 작업 목록을 조회합니다.
    description: |
      등록된 모든 작업 항목을 조회합니다.
      필터링 옵션을 통해 특정 조건의 작업만 조회할 수 있습니다.
    parameters:
      - name: training_course
        in: query
        type: string
        required: false
        description: 훈련 과정명으로 필터링
    responses:
      200:
        description: 작업 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            tasks:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  task_name:
                    type: string
                  description:
                    type: string
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
        logging.error("작업 목록 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "작업 목록 조회 중 오류가 발생했습니다."
        }), 500

@tasks_bp.route('/checklist', methods=['POST'])
def save_checklist():
    """
    체크리스트 저장 API
    ---
    tags:
      - Tasks
    summary: 작업 체크리스트를 저장합니다.
    description: |
      작업 체크 상태를 저장합니다.
      동일 날짜의 데이터가 있는 경우 업데이트합니다.
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
              description: 훈련 과정명
            date:
              type: string
              format: date
              description: 체크리스트 날짜
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
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "체크리스트가 저장되었습니다."
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
        logging.error("체크리스트 저장 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "체크리스트 저장 중 오류가 발생했습니다."
        }), 500 