from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

# Blueprint 정의
issues_bp = Blueprint('issues', __name__, url_prefix='/issues')

def init_issues_routes(app):
    """
    이슈 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(issues_bp)

@issues_bp.route('/', methods=['GET'])
def get_issues():
    """
    이슈 목록 조회 API
    ---
    tags:
      - Issues
    summary: 이슈 목록을 조회합니다.
    description: |
      등록된 모든 이슈를 조회합니다.
      필터링 옵션을 통해 특정 조건의 이슈만 조회할 수 있습니다.
    parameters:
      - name: training_course
        in: query
        type: string
        required: false
        description: 훈련 과정명으로 필터링
      - name: status
        in: query
        type: string
        required: false
        description: 상태로 필터링 (open/resolved)
    responses:
      200:
        description: 이슈 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            issues:
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
                  priority:
                    type: string
                  status:
                    type: string
                  created_at:
                    type: string
                    format: date-time
    """
    try:
        training_course = request.args.get('training_course')
        status = request.args.get('status')
        
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, title, content, priority, status, created_at 
            FROM issues 
            WHERE 1=1
        """
        params = []

        if training_course:
            query += " AND training_course = %s"
            params.append(training_course)

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        issues = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "issues": [
                {
                    "id": issue[0],
                    "title": issue[1],
                    "content": issue[2],
                    "priority": issue[3],
                    "status": issue[4],
                    "created_at": issue[5].isoformat() if issue[5] else None
                }
                for issue in issues
            ]
        }), 200

    except Exception as e:
        logging.error("이슈 목록 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "이슈 목록 조회 중 오류가 발생했습니다."
        }), 500

@issues_bp.route('/', methods=['POST'])
def create_issue():
    """
    이슈 등록 API
    ---
    tags:
      - Issues
    summary: 새로운 이슈를 등록합니다.
    description: |
      새로운 이슈를 등록합니다.
      제목, 내용, 우선순위, 훈련 과정명이 필요합니다.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
            - priority
            - training_course
          properties:
            title:
              type: string
              description: 이슈 제목
            content:
              type: string
              description: 이슈 내용
            priority:
              type: string
              description: 우선순위 (high/medium/low)
            training_course:
              type: string
              description: 훈련 과정명
    responses:
      201:
        description: 이슈 등록 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "이슈가 등록되었습니다."
    """
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        priority = data.get('priority')
        training_course = data.get('training_course')

        if not all([title, content, priority, training_course]):
            return jsonify({
                "success": False,
                "message": "필수 데이터가 누락되었습니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO issues 
            (title, content, priority, training_course, status, created_at)
            VALUES (%s, %s, %s, %s, 'open', %s)
            RETURNING id
        """, (title, content, priority, training_course, datetime.now()))

        issue_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "이슈가 등록되었습니다.",
            "id": issue_id
        }), 201

    except Exception as e:
        logging.error("이슈 등록 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "이슈 등록 중 오류가 발생했습니다."
        }), 500

@issues_bp.route('/<int:issue_id>/resolve', methods=['POST'])
def resolve_issue(issue_id):
    """
    이슈 해결 처리 API
    ---
    tags:
      - Issues
    summary: 이슈를 해결 처리합니다.
    description: |
      이슈를 해결 처리하고 해결 시간을 기록합니다.
    parameters:
      - name: issue_id
        in: path
        type: integer
        required: true
        description: 이슈 ID
    responses:
      200:
        description: 이슈 해결 처리 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "이슈가 해결 처리되었습니다."
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE issues 
            SET status = 'resolved', resolved_at = %s 
            WHERE id = %s AND status = 'open'
            RETURNING id
        """, (datetime.now(), issue_id))

        if cursor.fetchone() is None:
            return jsonify({
                "success": False,
                "message": "이슈를 찾을 수 없거나 이미 해결되었습니다."
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "이슈가 해결 처리되었습니다."
        }), 200

    except Exception as e:
        logging.error("이슈 해결 처리 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "이슈 해결 처리 중 오류가 발생했습니다."
        }), 500 