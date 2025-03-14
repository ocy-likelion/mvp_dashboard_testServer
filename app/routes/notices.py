from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

# Blueprint 정의
notices_bp = Blueprint('notices', __name__, url_prefix='/notices')

def init_notices_routes(app):
    """
    공지사항 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(notices_bp)

@notices_bp.route('/', methods=['GET'])
def get_notices():
    """
    공지사항 목록 조회 API
    ---
    tags:
      - Notices
    summary: 공지사항 목록을 조회합니다.
    description: |
      등록된 모든 공지사항을 조회합니다.
      필터링 옵션을 통해 특정 조건의 공지사항만 조회할 수 있습니다.
    parameters:
      - name: training_course
        in: query
        type: string
        required: false
        description: 훈련 과정명으로 필터링
    responses:
      200:
        description: 공지사항 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            notices:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  content:
                    type: string
                  created_at:
                    type: string
                    format: date-time
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
        logging.error("공지사항 목록 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "공지사항 목록 조회 중 오류가 발생했습니다."
        }), 500

@notices_bp.route('/', methods=['POST'])
def create_notice():
    """
    공지사항 등록 API
    ---
    tags:
      - Notices
    summary: 새로운 공지사항을 등록합니다.
    description: |
      새로운 공지사항을 등록합니다.
      제목, 내용, 훈련 과정명이 필요합니다.
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
              description: 공지사항 제목
            content:
              type: string
              description: 공지사항 내용
            training_course:
              type: string
              description: 훈련 과정명
    responses:
      201:
        description: 공지사항 등록 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "공지사항이 등록되었습니다."
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
        logging.error("공지사항 등록 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "공지사항 등록 중 오류가 발생했습니다."
        }), 500 