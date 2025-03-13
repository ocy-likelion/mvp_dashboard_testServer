from flask import Blueprint, request, jsonify, send_file
from app.database import get_db_connection
import pandas as pd
import io
import logging
from datetime import datetime

bp = Blueprint('issues', __name__)

@bp.route('/issues', methods=['GET'])
def get_issues():
    """
    이슈 목록 조회 API
    ---
    tags:
      - Issues
    summary: 등록된 이슈 목록을 조회합니다.
    description: |
      시스템에 등록된 모든 이슈 목록을 조회합니다.
      - 이슈 ID, 제목, 내용, 상태, 우선순위 등 반환
      - 생성일시 기준 내림차순 정렬
      - 해결 상태에 따른 필터링 가능
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: 이슈 상태 필터 (미해결/해결)
    responses:
      200:
        description: 이슈 목록 조회 성공
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
                    description: 이슈 ID
                  title:
                    type: string
                    description: 이슈 제목
                  content:
                    type: string
                    description: 이슈 내용
                  priority:
                    type: string
                    description: 우선순위 (높음/중간/낮음)
                  status:
                    type: string
                    description: 이슈 상태 (미해결/해결)
                  created_at:
                    type: string
                    format: date-time
                    description: 생성일시
                  resolved_at:
                    type: string
                    format: date-time
                    description: 해결일시 (해결된 경우에만)
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
        status = request.args.get('status')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, title, content, priority, status, created_at, resolved_at 
            FROM issues 
        '''
        params = []
        
        if status:
            query += ' WHERE status = %s'
            params.append(status)
            
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params if params else None)
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "priority": row[3],
                "status": row[4],
                "created_at": row[5],
                "resolved_at": row[6]
            } for row in issues]
        }), 200

    except Exception as e:
        logging.error("Error retrieving issues", exc_info=True)
        return jsonify({"success": False, "message": "이슈 목록을 불러오는 중 오류가 발생했습니다."}), 500

@bp.route('/issues', methods=['POST'])
def create_issue():
    """
    이슈 등록 API
    ---
    tags:
      - Issues
    summary: 새로운 이슈를 등록합니다.
    description: |
      새로운 이슈를 시스템에 등록합니다.
      - 이슈 제목, 내용, 우선순위는 필수 입력 항목
      - 초기 상태는 '미해결'로 설정
      - 생성일시는 자동으로 현재 시간 저장
      - 우선순위는 '높음', '중간', '낮음' 중 하나여야 함
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
          properties:
            title:
              type: string
              description: 이슈 제목
            content:
              type: string
              description: 이슈 내용
            priority:
              type: string
              enum: [높음, 중간, 낮음]
              description: 우선순위
    responses:
      201:
        description: 이슈 등록 성공
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
        priority = data.get('priority', '').strip()

        if not title or not content or not priority:
            return jsonify({"success": False, "message": "제목, 내용, 우선순위를 모두 입력하세요."}), 400

        if priority not in ['높음', '중간', '낮음']:
            return jsonify({"success": False, "message": "유효하지 않은 우선순위입니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO issues (title, content, priority, status, created_at)
            VALUES (%s, %s, %s, '미해결', NOW())
        ''', (title, content, priority))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "이슈가 등록되었습니다."}), 201

    except Exception as e:
        logging.error("Error creating issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 등록 중 오류가 발생했습니다."}), 500

@bp.route('/issues/comments', methods=['POST'])
def add_issue_comment():
    """
    이슈사항에 대한 댓글 저장 API
    ---
    tags:
      - Issues
    """
    try:
        data = request.json
        issue_id = data.get('issue_id')
        comment = data.get('comment')

        if not issue_id or not comment:
            return jsonify({"success": False, "message": "이슈 ID와 댓글 내용을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO issue_comments (issue_id, comment, created_at) VALUES (%s, %s, NOW())",
            (issue_id, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving issue comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500

@bp.route('/issues/<int:issue_id>/resolve', methods=['POST'])
def resolve_issue():
    """
    이슈 해결 처리 API
    ---
    tags:
      - Issues
    summary: 특정 이슈를 해결 처리합니다.
    description: |
      지정된 이슈의 상태를 해결로 변경합니다.
      - 이슈 상태를 '해결'로 변경
      - 해결일시를 현재 시간으로 기록
      - 이미 해결된 이슈는 다시 해결 처리할 수 없음
    parameters:
      - name: issue_id
        in: path
        type: integer
        required: true
        description: 해결 처리할 이슈의 ID
    responses:
      200:
        description: 이슈 해결 처리 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: API 호출 성공 여부
            message:
              type: string
              description: 성공 메시지
      404:
        description: 이슈를 찾을 수 없음
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
        issue_id = request.view_args.get('issue_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 이슈 존재 여부 확인
        cursor.execute('SELECT status FROM issues WHERE id = %s', (issue_id,))
        issue = cursor.fetchone()
        
        if not issue:
            return jsonify({"success": False, "message": "해당 이슈를 찾을 수 없습니다."}), 404
            
        if issue[0] == '해결':
            return jsonify({"success": False, "message": "이미 해결된 이슈입니다."}), 400

        # 이슈 해결 처리
        cursor.execute('''
            UPDATE issues 
            SET status = '해결', resolved_at = NOW() 
            WHERE id = %s
        ''', (issue_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "이슈가 해결 처리되었습니다."
        }), 200

    except Exception as e:
        logging.error("Error resolving issue", exc_info=True)
        return jsonify({"success": False, "message": "이슈 해결 처리 중 오류가 발생했습니다."}), 500

@bp.route('/issues/download', methods=['GET'])
def download_issues():
    """
    이슈사항을 Excel 파일로 다운로드하는 API
    ---
    tags:
      - Issues
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, content, date, training_course, created_at, resolved FROM issues")
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        columns = ["ID", "이슈 내용", "날짜", "훈련 과정", "생성일", "해결됨"]
        df = pd.DataFrame(issues, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name="이슈사항")
        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="이슈사항.xlsx"
        )
    except Exception as e:
        logging.error("이슈사항 다운로드 실패", exc_info=True)
        return jsonify({"success": False, "message": "이슈 다운로드 실패"}), 500 