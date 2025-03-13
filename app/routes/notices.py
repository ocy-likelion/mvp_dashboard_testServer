from flask import Blueprint, request, jsonify
from app.database import get_db_connection
from datetime import datetime
import logging

bp = Blueprint('notices', __name__)

@bp.route('/notices', methods=['GET'])
def get_notices():
    """
    공지사항 목록 조회 API
    ---
    tags:
      - Notices
    summary: 공지사항 목록을 조회합니다.
    description: |
      등록된 모든 공지사항을 최신순으로 조회합니다.
      - 공지사항 ID, 제목, 내용, 작성일 등 반환
      - 작성일 기준 내림차순 정렬
    responses:
      200:
        description: 공지사항 목록 조회 성공
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
                  id:
                    type: integer
                    description: 공지사항 ID
                  title:
                    type: string
                    description: 제목
                  content:
                    type: string
                    description: 내용
                  created_at:
                    type: string
                    format: date-time
                    description: 작성일시
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, content, created_at FROM notices ORDER BY created_at DESC')
        notices = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": row[3]
            } for row in notices]
        }), 200

    except Exception as e:
        logging.error("Error retrieving notices", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 목록을 불러오는 중 오류가 발생했습니다."}), 500

@bp.route('/notices', methods=['POST'])
def create_notice():
    """
    공지사항 등록 API
    ---
    tags:
      - Notices
    summary: 새로운 공지사항을 등록합니다.
    description: |
      새로운 공지사항을 데이터베이스에 등록합니다.
      - 제목과 내용은 필수 입력 항목
      - 작성일시는 자동으로 현재 시간 저장
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
          properties:
            title:
              type: string
              description: 공지사항 제목
            content:
              type: string
              description: 공지사항 내용
    responses:
      201:
        description: 공지사항 등록 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            message:
              type: string
              description: 성공 메시지
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
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({"success": False, "message": "제목과 내용을 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notices (title, content, created_at) VALUES (%s, %s, NOW())',
            (title, content)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "공지사항이 등록되었습니다."}), 201

    except Exception as e:
        logging.error("Error creating notice", exc_info=True)
        return jsonify({"success": False, "message": "공지사항 등록 중 오류가 발생했습니다."}), 500

@bp.route('/remarks', methods=['POST'])
def save_remarks():
    """
    전달사항 저장 API
    ---
    tags:
      - Remarks
    """
    try:
        data = request.json
        remarks = data.get('remarks')
        if not remarks:
            return jsonify({"success": False, "message": "Remarks are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notices (type, title, content, date)
            VALUES (%s, %s, %s, %s)
        ''', ("전달사항", "전달사항 제목", remarks, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Remarks saved!"}), 201
    except Exception as e:
        logging.error("Error saving remarks", exc_info=True)
        return jsonify({"success": False, "message": "Failed to save remarks"}), 500 