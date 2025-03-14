from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

# Blueprint 정의
irregular_tasks_bp = Blueprint('irregular_tasks', __name__, url_prefix='/irregular_tasks')

def init_irregular_tasks_routes(app):
    """
    비정기 작업 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(irregular_tasks_bp)

@irregular_tasks_bp.route('/', methods=['GET'])
def get_irregular_tasks():
    """
    비정기 작업 목록 조회 API
    ---
    tags:
      - Irregular Tasks
    summary: 비정기 작업 목록을 조회합니다.
    description: |
      등록된 모든 비정기 작업을 조회합니다.
      필터링 옵션을 통해 특정 조건의 작업만 조회할 수 있습니다.
    parameters:
      - name: training_course
        in: query
        type: string
        required: false
        description: 훈련 과정명으로 필터링
      - name: completed
        in: query
        type: boolean
        required: false
        description: 완료 여부로 필터링
    responses:
      200:
        description: 비정기 작업 목록 조회 성공
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
                  title:
                    type: string
                  description:
                    type: string
                  due_date:
                    type: string
                    format: date
                  completed:
                    type: boolean
    """
    try:
        training_course = request.args.get('training_course')
        completed = request.args.get('completed', type=bool)
        
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, title, description, due_date, completed 
            FROM irregular_tasks 
            WHERE 1=1
        """
        params = []

        if training_course:
            query += " AND training_course = %s"
            params.append(training_course)

        if completed is not None:
            query += " AND completed = %s"
            params.append(completed)

        query += " ORDER BY due_date ASC"

        cursor.execute(query, params)
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "tasks": [
                {
                    "id": task[0],
                    "title": task[1],
                    "description": task[2],
                    "due_date": task[3].isoformat() if task[3] else None,
                    "completed": task[4]
                }
                for task in tasks
            ]
        }), 200

    except Exception as e:
        logging.error("비정기 작업 목록 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "비정기 작업 목록 조회 중 오류가 발생했습니다."
        }), 500

@irregular_tasks_bp.route('/', methods=['POST'])
def create_irregular_task():
    """
    비정기 작업 등록 API
    ---
    tags:
      - Irregular Tasks
    summary: 새로운 비정기 작업을 등록합니다.
    description: |
      새로운 비정기 작업을 등록합니다.
      제목, 설명, 마감일, 훈련 과정명이 필요합니다.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - description
            - due_date
            - training_course
          properties:
            title:
              type: string
              description: 작업 제목
            description:
              type: string
              description: 작업 설명
            due_date:
              type: string
              format: date
              description: 마감일
            training_course:
              type: string
              description: 훈련 과정명
    responses:
      201:
        description: 비정기 작업 등록 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "비정기 작업이 등록되었습니다."
    """
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date = data.get('due_date')
        training_course = data.get('training_course')

        if not all([title, description, due_date, training_course]):
            return jsonify({
                "success": False,
                "message": "필수 데이터가 누락되었습니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO irregular_tasks 
            (title, description, due_date, training_course, completed, created_at)
            VALUES (%s, %s, %s, %s, false, %s)
            RETURNING id
        """, (title, description, due_date, training_course, datetime.now()))

        task_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "비정기 작업이 등록되었습니다.",
            "id": task_id
        }), 201

    except Exception as e:
        logging.error("비정기 작업 등록 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "비정기 작업 등록 중 오류가 발생했습니다."
        }), 500

@irregular_tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
def complete_irregular_task(task_id):
    """
    비정기 작업 완료 처리 API
    ---
    tags:
      - Irregular Tasks
    summary: 비정기 작업을 완료 처리합니다.
    description: |
      비정기 작업을 완료 처리하고 완료 시간을 기록합니다.
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
        description: 비정기 작업 ID
    responses:
      200:
        description: 비정기 작업 완료 처리 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "비정기 작업이 완료 처리되었습니다."
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE irregular_tasks 
            SET completed = true, completed_at = %s 
            WHERE id = %s
            RETURNING id
        """, (datetime.now(), task_id))

        if cursor.fetchone() is None:
            return jsonify({
                "success": False,
                "message": "비정기 작업을 찾을 수 없습니다."
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "비정기 작업이 완료 처리되었습니다."
        }), 200

    except Exception as e:
        logging.error("비정기 작업 완료 처리 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "비정기 작업 완료 처리 중 오류가 발생했습니다."
        }), 500 