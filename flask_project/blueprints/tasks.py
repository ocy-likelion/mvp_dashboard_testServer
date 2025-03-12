# blueprints/tasks.py
from flask import Blueprint, request, jsonify, session
from database import get_db_connection
import logging

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/', methods=['GET'])
def get_tasks():
    """
    업무 체크리스트 조회 API
    ---
    tags:
      - Tasks
    summary: 업무 체크리스트 데이터 조회
    description: 
      모든 업무 체크리스트 데이터를 조회합니다.  
      task_category를 기준으로 필터링할 수 있습니다.
    parameters:
      - name: task_category
        in: query
        type: string
        required: false
        description: "업무 체크리스트의 카테고리 (예: 개발, 디자인)"
    responses:
      200:
        description: 모든 업무 체크리스트 데이터를 반환함
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
                  task_period:
                    type: string
                  task_category:
                    type: string
                  guide:
                    type: string
      400:
        description: "잘못된 요청 (예: 유효하지 않은 task_category 값)"
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
      500:
        description: 서버 오류로 인해 업무 체크리스트 조회 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    try:
        task_category = request.args.get('task_category')  # 선택적 필터링

        conn = get_db_connection()
        cursor = conn.cursor()

        # guide 컬럼 추가
        query = "SELECT id, task_name, task_period, task_category, guide FROM task_items"
        params = []

        if task_category:
            query += " WHERE task_category = %s"
            params.append(task_category)

        query += " ORDER BY id ASC"

        cursor.execute(query, tuple(params))

        tasks = [
            {
                "id": row[0],
                "task_name": row[1],
                "task_period": row[2],
                "task_category": row[3],
                "guide": row[4] if row[4] else "업무 가이드 없음"  # NULL 값 기본 처리
            }
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": tasks}), 200
    except Exception as e:
        logging.error("Error retrieving tasks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve tasks"}), 500

