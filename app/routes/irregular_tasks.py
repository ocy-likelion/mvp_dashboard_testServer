from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

bp = Blueprint('irregular_tasks', __name__)

@bp.route('/irregular_tasks', methods=['GET'])
def get_irregular_tasks():
    """
    불규칙 업무 목록 조회 API
    ---
    tags:
      - Irregular Tasks
    summary: 불규칙 업무 목록을 조회합니다.
    description: |
      등록된 모든 불규칙 업무 목록을 조회합니다.
      - 업무 ID, 제목, 내용, 상태, 담당자 등 반환
      - 생성일시 기준 내림차순 정렬
      - 완료 여부에 따른 상태 표시
    responses:
      200:
        description: 불규칙 업무 목록 조회 성공
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
                    description: 불규칙 업무 ID
                  title:
                    type: string
                    description: 업무 제목
                  content:
                    type: string
                    description: 업무 내용
                  status:
                    type: string
                    description: 업무 상태 (진행중/완료)
                  assignee:
                    type: string
                    description: 담당자
                  created_at:
                    type: string
                    format: date-time
                    description: 생성일시
                  completed_at:
                    type: string
                    format: date-time
                    description: 완료일시 (완료된 경우에만)
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
        cursor.execute('''
            SELECT id, title, content, status, assignee, created_at, completed_at 
            FROM irregular_tasks 
            ORDER BY created_at DESC
        ''')
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "status": row[3],
                "assignee": row[4],
                "created_at": row[5],
                "completed_at": row[6]
            } for row in tasks]
        }), 200

    except Exception as e:
        logging.error("Error retrieving irregular tasks", exc_info=True)
        return jsonify({"success": False, "message": "불규칙 업무 목록을 불러오는 중 오류가 발생했습니다."}), 500

@bp.route('/irregular_tasks', methods=['POST'])
def create_irregular_task():
    """
    불규칙 업무 등록 API
    ---
    tags:
      - Irregular Tasks
    summary: 새로운 불규칙 업무를 등록합니다.
    description: |
      새로운 불규칙 업무를 시스템에 등록합니다.
      - 업무 제목, 내용, 담당자는 필수 입력 항목
      - 초기 상태는 '진행중'으로 설정
      - 생성일시는 자동으로 현재 시간 저장
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - content
            - assignee
          properties:
            title:
              type: string
              description: 업무 제목
            content:
              type: string
              description: 업무 내용
            assignee:
              type: string
              description: 담당자
    responses:
      201:
        description: 불규칙 업무 등록 성공
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
        assignee = data.get('assignee', '').strip()

        if not title or not content or not assignee:
            return jsonify({"success": False, "message": "제목, 내용, 담당자를 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO irregular_tasks (title, content, status, assignee, created_at)
            VALUES (%s, %s, '진행중', %s, NOW())
        ''', (title, content, assignee))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "불규칙 업무가 등록되었습니다."}), 201

    except Exception as e:
        logging.error("Error creating irregular task", exc_info=True)
        return jsonify({"success": False, "message": "불규칙 업무 등록 중 오류가 발생했습니다."}), 500

@bp.route('/irregular_tasks/<int:task_id>/complete', methods=['POST'])
def complete_irregular_task():
    """
    불규칙 업무 완료 처리 API
    ---
    tags:
      - Irregular Tasks
    summary: 특정 불규칙 업무를 완료 처리합니다.
    description: |
      지정된 불규칙 업무의 상태를 완료로 변경합니다.
      - 업무 상태를 '완료'로 변경
      - 완료일시를 현재 시간으로 기록
      - 이미 완료된 업무는 다시 완료 처리할 수 없음
    parameters:
      - name: task_id
        in: path
        type: integer
        required: true
        description: 완료 처리할 불규칙 업무의 ID
    responses:
      200:
        description: 업무 완료 처리 성공
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
        description: 업무를 찾을 수 없음
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
        task_id = request.view_args.get('task_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 업무 존재 여부 확인
        cursor.execute('SELECT status FROM irregular_tasks WHERE id = %s', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return jsonify({"success": False, "message": "해당 업무를 찾을 수 없습니다."}), 404
            
        if task[0] == '완료':
            return jsonify({"success": False, "message": "이미 완료된 업무입니다."}), 400

        # 업무 완료 처리
        cursor.execute('''
            UPDATE irregular_tasks 
            SET status = '완료', completed_at = NOW() 
            WHERE id = %s
        ''', (task_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "업무가 완료 처리되었습니다."
        }), 200

    except Exception as e:
        logging.error("Error completing irregular task", exc_info=True)
        return jsonify({"success": False, "message": "업무 완료 처리 중 오류가 발생했습니다."}), 500 