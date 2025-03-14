from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

# Blueprint 정의
unchecked_bp = Blueprint('unchecked', __name__, url_prefix='/unchecked')

def init_unchecked_routes(app):
    """
    미확인 항목 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(unchecked_bp)

@unchecked_bp.route('/descriptions', methods=['GET'])
def get_unchecked_descriptions():
    """
    미확인 항목 목록 조회 API
    ---
    tags:
      - Unchecked Items
    summary: 미확인 항목 목록을 조회합니다.
    description: |
      등록된 모든 미확인 항목을 조회합니다.
      필터링 옵션을 통해 특정 조건의 항목만 조회할 수 있습니다.
    parameters:
      - name: training_course
        in: query
        type: string
        required: false
        description: 훈련 과정명으로 필터링
      - name: resolved
        in: query
        type: boolean
        required: false
        description: 해결 여부로 필터링
    responses:
      200:
        description: 미확인 항목 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            items:
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
                  date:
                    type: string
                    format: date
                  resolved:
                    type: boolean
    """
    try:
        training_course = request.args.get('training_course')
        resolved = request.args.get('resolved', type=bool)
        
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, task_name, description, date, resolved 
            FROM unchecked_descriptions 
            WHERE 1=1
        """
        params = []

        if training_course:
            query += " AND training_course = %s"
            params.append(training_course)

        if resolved is not None:
            query += " AND resolved = %s"
            params.append(resolved)

        query += " ORDER BY date DESC"

        cursor.execute(query, params)
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "items": [
                {
                    "id": item[0],
                    "task_name": item[1],
                    "description": item[2],
                    "date": item[3].isoformat() if item[3] else None,
                    "resolved": item[4]
                }
                for item in items
            ]
        }), 200

    except Exception as e:
        logging.error("미확인 항목 목록 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "미확인 항목 목록 조회 중 오류가 발생했습니다."
        }), 500

@unchecked_bp.route('/descriptions', methods=['POST'])
def create_unchecked_description():
    """
    미확인 항목 등록 API
    ---
    tags:
      - Unchecked Items
    summary: 새로운 미확인 항목을 등록합니다.
    description: |
      새로운 미확인 항목을 등록합니다.
      작업명, 설명, 훈련 과정명, 날짜가 필요합니다.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - task_name
            - description
            - training_course
            - date
          properties:
            task_name:
              type: string
              description: 작업명
            description:
              type: string
              description: 미확인 사유
            training_course:
              type: string
              description: 훈련 과정명
            date:
              type: string
              format: date
              description: 발생 날짜
    responses:
      201:
        description: 미확인 항목 등록 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "미확인 항목이 등록되었습니다."
    """
    try:
        data = request.get_json()
        task_name = data.get('task_name')
        description = data.get('description')
        training_course = data.get('training_course')
        date = data.get('date')

        if not all([task_name, description, training_course, date]):
            return jsonify({
                "success": False,
                "message": "필수 데이터가 누락되었습니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 해당 작업의 task_checklist id 조회
        cursor.execute("""
            SELECT tc.id 
            FROM task_checklist tc
            JOIN task_items ti ON tc.task_id = ti.id
            WHERE ti.task_name = %s 
            AND tc.training_course = %s 
            AND DATE(tc.date) = DATE(%s)
        """, (task_name, training_course, date))
        
        result = cursor.fetchone()
        id_task = result[0] if result else None

        cursor.execute("""
            INSERT INTO unchecked_descriptions 
            (task_name, description, training_course, date, resolved, id_task)
            VALUES (%s, %s, %s, %s, false, %s)
            RETURNING id
        """, (task_name, description, training_course, date, id_task))

        item_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "미확인 항목이 등록되었습니다.",
            "id": item_id
        }), 201

    except Exception as e:
        logging.error("미확인 항목 등록 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "미확인 항목 등록 중 오류가 발생했습니다."
        }), 500

@unchecked_bp.route('/descriptions/<int:item_id>/resolve', methods=['POST'])
def resolve_unchecked_description(item_id):
    """
    미확인 항목 해결 처리 API
    ---
    tags:
      - Unchecked Items
    summary: 미확인 항목을 해결 처리합니다.
    description: |
      미확인 항목을 해결 처리하고,
      연관된 체크리스트 항목도 체크 처리합니다.
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: 미확인 항목 ID
    responses:
      200:
        description: 미확인 항목 해결 처리 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "미확인 항목이 해결 처리되었습니다."
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 트랜잭션 시작
        cursor.execute("BEGIN")

        try:
            # 미확인 항목 조회
            cursor.execute("""
                SELECT task_name, training_course, date, id_task 
                FROM unchecked_descriptions 
                WHERE id = %s
            """, (item_id,))
            
            item = cursor.fetchone()
            if not item:
                return jsonify({
                    "success": False,
                    "message": "미확인 항목을 찾을 수 없습니다."
                }), 404

            task_name, training_course, date, id_task = item

            # 체크리스트 항목 체크 처리
            if id_task:
                cursor.execute("""
                    UPDATE task_checklist 
                    SET is_checked = true 
                    WHERE id = %s
                """, (id_task,))

            # 미확인 항목 해결 처리
            cursor.execute("""
                UPDATE unchecked_descriptions 
                SET resolved = true, resolved_at = %s 
                WHERE id = %s
            """, (datetime.now(), item_id))

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
            "message": "미확인 항목이 해결 처리되었습니다."
        }), 200

    except Exception as e:
        logging.error("미확인 항목 해결 처리 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "미확인 항목 해결 처리 중 오류가 발생했습니다."
        }), 500 