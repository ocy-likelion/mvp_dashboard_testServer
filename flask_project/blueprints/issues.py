# blueprints/issues.py
from flask import Blueprint, request, jsonify
from database import get_db_connection
import logging

issues_bp = Blueprint('issues', __name__)

@issues_bp.route('/', methods=['POST'])
def save_issue():
    """
    이슈사항 저장 API
    ---
    tags:
      - Issues
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            issue:
              type: string
              example: "강의 자료 오류 발생"
    responses:
      201:
        description: 이슈사항 저장 성공
      400:
        description: 요청 데이터 오류
      500:
        description: 서버 오류
    """
    try:
        data = request.json
        issue_text = data.get('issue')
        training_course = data.get('training_course')
        date = data.get('date')

        if not issue_text or not training_course or not date:
            return jsonify({"success": False, "message": "이슈, 훈련 과정, 날짜를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO issues (content, date, training_course, created_at, resolved)
            VALUES (%s, %s, %s, NOW(), FALSE)
        ''', (issue_text, date, training_course))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 저장 실패"}), 500
