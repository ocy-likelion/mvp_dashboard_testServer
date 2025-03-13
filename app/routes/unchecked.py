from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

bp = Blueprint('unchecked', __name__)

@bp.route('/unchecked_descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미체크 항목 목록 조회 API
    ---
    tags:
      - Unchecked Items
    summary: 미체크 항목 설명 및 액션 플랜 목록을 조회합니다.
    description: |
      해결되지 않은 미체크 항목들의 목록을 조회합니다.
      - 미체크 항목의 내용, 액션 플랜, 훈련 과정 정보 등 반환
      - 생성일시 기준 내림차순 정렬
      - 부서 정보도 함께 반환
    responses:
      200:
        description: 미체크 항목 목록 조회 성공
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
                    description: 미체크 항목 ID
                  content:
                    type: string
                    description: 미체크 항목 내용
                  action_plan:
                    type: string
                    description: 액션 플랜
                  training_course:
                    type: string
                    description: 훈련 과정명
                  dept:
                    type: string
                    description: 부서명
                  created_at:
                    type: string
                    format: date-time
                    description: 생성일시
                  resolved:
                    type: boolean
                    description: 해결 여부
                  task_checklist_id:
                    type: integer
                    description: 연결된 task_checklist의 ID
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
            SELECT ud.id, ud.content, ud.action_plan, ud.training_course, 
                   ti.dept, ud.created_at, ud.resolved, ud.id_task
            FROM unchecked_descriptions ud
            JOIN training_info ti ON ud.training_course = ti.training_course
            WHERE ud.resolved = FALSE  
            ORDER BY ud.created_at DESC;
        ''')
        unchecked_items = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": row[0],
                    "content": row[1],
                    "action_plan": row[2],
                    "training_course": row[3],
                    "dept": row[4],
                    "created_at": row[5],
                    "resolved": row[6],
                    "task_checklist_id": row[7]
                } for row in unchecked_items
            ]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked descriptions", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 목록을 불러오는 중 오류 발생"}), 500

@bp.route('/unchecked_descriptions', methods=['POST'])
def save_unchecked_description():
    """
    미체크 항목 등록 API
    ---
    tags:
      - Unchecked Items
    summary: 새로운 미체크 항목을 등록합니다.
    description: |
      체크되지 않은 업무에 대한 설명과 액션 플랜을 등록합니다.
      - 미체크 항목 내용, 액션 플랜, 훈련 과정명 필수 입력
      - task_checklist의 ID를 함께 저장하여 추후 해결 시 연동
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - description
            - action_plan
            - training_course
          properties:
            description:
              type: string
              description: 미체크 항목 내용
            action_plan:
              type: string
              description: 액션 플랜
            training_course:
              type: string
              description: 훈련 과정명
    responses:
      201:
        description: 미체크 항목 등록 성공
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
        if not request.is_json:
            return jsonify({"success": False, "message": "Invalid JSON format"}), 400

        data = request.get_json()
        description = data.get("description", "").strip()
        action_plan = data.get("action_plan", "").strip()
        training_course = data.get("training_course", "").strip()

        if not description or not action_plan or not training_course:
            return jsonify({"success": False, "message": "설명, 액션 플랜, 훈련과정명을 모두 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 트랜잭션 시작
            cursor.execute("BEGIN")

            # task_checklist에서 해당하는 id 찾기
            cursor.execute("""
                SELECT tc.id 
                FROM task_checklist tc
                JOIN task_items ti ON tc.task_id = ti.id
                WHERE ti.task_name = %s 
                AND tc.training_course = %s
                AND DATE(tc.checked_date) = CURRENT_DATE
                AND tc.is_checked = FALSE
            """, (description, training_course))
            
            task_checklist = cursor.fetchone()
            
            if not task_checklist:
                cursor.execute("ROLLBACK")
                return jsonify({"success": False, "message": "해당하는 미체크 항목을 찾을 수 없습니다."}), 404

            task_checklist_id = task_checklist[0]

            # unchecked_descriptions에 저장
            cursor.execute('''
                INSERT INTO unchecked_descriptions 
                (content, action_plan, training_course, created_at, resolved, id_task)
                VALUES (%s, %s, %s, NOW(), FALSE, %s)
            ''', (description, action_plan, training_course, task_checklist_id))

            # 트랜잭션 커밋
            cursor.execute("COMMIT")

            return jsonify({"success": True, "message": "미체크 항목과 액션 플랜이 저장되었습니다!"}), 201

        except Exception as e:
            cursor.execute("ROLLBACK")
            raise e

    except Exception as e:
        logging.error("Error saving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "서버 오류 발생"}), 500
    
    finally:
        cursor.close()
        conn.close()

@bp.route('/unchecked_descriptions/resolve', methods=['POST'])
def resolve_unchecked_description():
    """
    미체크 항목 해결 API
    ---
    tags:
      - Unchecked Items
    summary: 미체크 항목을 해결 상태로 변경합니다.
    description: |
      특정 미체크 항목을 해결 상태로 변경하고, 연관된 task_checklist의 상태도 업데이트합니다.
      - 미체크 항목의 resolved 상태를 TRUE로 변경
      - 연결된 task_checklist의 is_checked 상태를 TRUE로 변경
      - 해결 시간 기록
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
          properties:
            unchecked_id:
              type: integer
              description: 해결할 미체크 항목의 ID
    responses:
      200:
        description: 미체크 항목 해결 성공
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
        description: 미체크 항목을 찾을 수 없음
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
        data = request.json
        unchecked_id = data.get('unchecked_id')

        if not unchecked_id:
            return jsonify({"success": False, "message": "미체크 항목 ID가 필요합니다."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 트랜잭션 시작
            cursor.execute("BEGIN")

            # 1. 미체크 항목 정보와 연결된 task_checklist id 조회
            cursor.execute("""
                SELECT id_task
                FROM unchecked_descriptions 
                WHERE id = %s
            """, (unchecked_id,))
            
            unchecked_item = cursor.fetchone()
            if not unchecked_item:
                cursor.execute("ROLLBACK")
                return jsonify({"success": False, "message": "해당 미체크 항목을 찾을 수 없습니다."}), 404

            task_checklist_id = unchecked_item[0]

            # 2. task_checklist 업데이트
            cursor.execute("""
                UPDATE task_checklist
                SET is_checked = TRUE
                WHERE id = %s
            """, (task_checklist_id,))

            # 3. 미체크 항목을 해결 상태로 변경
            cursor.execute("""
                UPDATE unchecked_descriptions 
                SET resolved = TRUE,
                    resolved_at = NOW()
                WHERE id = %s
            """, (unchecked_id,))

            # 트랜잭션 커밋
            cursor.execute("COMMIT")

            return jsonify({
                "success": True, 
                "message": "미체크 항목이 해결되었으며, 체크 상태가 업데이트되었습니다."
            }), 200

        except Exception as e:
            # 오류 발생 시 롤백
            cursor.execute("ROLLBACK")
            raise e

    except Exception as e:
        logging.error("Error resolving unchecked description", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 해결 실패"}), 500

    finally:
        cursor.close()
        conn.close()

@bp.route('/unchecked_comments', methods=['GET'])
def get_unchecked_comments():
    """
    미체크 항목 댓글 조회 API
    ---
    tags:
      - Unchecked Comments
    summary: 특정 미체크 항목의 댓글 목록을 조회합니다.
    description: |
      지정된 미체크 항목에 대한 모든 댓글을 조회합니다.
      - 댓글 ID, 내용, 작성일시 반환
      - 작성일시 기준 오름차순 정렬
    parameters:
      - name: unchecked_id
        in: query
        type: integer
        required: true
        description: 댓글을 조회할 미체크 항목의 ID
    responses:
      200:
        description: 댓글 목록 조회 성공
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
                    description: 댓글 ID
                  comment:
                    type: string
                    description: 댓글 내용
                  created_at:
                    type: string
                    format: date-time
                    description: 작성일시
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
        unchecked_id = request.args.get('unchecked_id')

        if not unchecked_id:
            return jsonify({"success": False, "message": "미체크 항목 ID를 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, comment, created_at FROM unchecked_comments WHERE unchecked_id = %s ORDER BY created_at ASC",
            (unchecked_id,)
        )
        comments = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{"id": row[0], "comment": row[1], "created_at": row[2]} for row in comments]
        }), 200
    except Exception as e:
        logging.error("Error retrieving unchecked comments", exc_info=True)
        return jsonify({"success": False, "message": "미체크 항목 댓글 조회 실패"}), 500

@bp.route('/unchecked_comments', methods=['POST'])
def add_unchecked_comment():
    """
    미체크 항목 댓글 등록 API
    ---
    tags:
      - Unchecked Comments
    summary: 미체크 항목에 새로운 댓글을 등록합니다.
    description: |
      특정 미체크 항목에 대한 새로운 댓글을 등록합니다.
      - 댓글 내용과 미체크 항목 ID 필수 입력
      - 작성일시는 자동으로 현재 시간 저장
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - unchecked_id
            - comment
          properties:
            unchecked_id:
              type: integer
              description: 댓글을 등록할 미체크 항목의 ID
            comment:
              type: string
              description: 댓글 내용
    responses:
      201:
        description: 댓글 등록 성공
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
        data = request.json
        unchecked_id = data.get('unchecked_id')
        comment = data.get('comment')

        if not unchecked_id or not comment:
            return jsonify({"success": False, "message": "미체크 항목 ID와 댓글을 입력하세요."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unchecked_comments (unchecked_id, comment, created_at) VALUES (%s, %s, NOW())",
            (unchecked_id, comment)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "댓글이 저장되었습니다."}), 201
    except Exception as e:
        logging.error("Error saving unchecked comment", exc_info=True)
        return jsonify({"success": False, "message": "댓글 저장 실패"}), 500 