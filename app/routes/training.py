from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

# Blueprint 정의
training_bp = Blueprint('training', __name__, url_prefix='/training')

def init_training_routes(app):
    """
    교육 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(training_bp)

@training_bp.route('/courses', methods=['GET'])
def get_training_courses():
    """
    교육 과정 목록 조회 API
    ---
    tags:
      - Training
    summary: 교육 과정 목록을 조회합니다.
    description: |
      등록된 모든 교육 과정을 조회합니다.
      필터링 옵션을 통해 특정 조건의 과정만 조회할 수 있습니다.
    parameters:
      - name: dept
        in: query
        type: string
        required: false
        description: 부서명으로 필터링
      - name: active_only
        in: query
        type: boolean
        required: false
        description: 진행 중인 과정만 조회
    responses:
      200:
        description: 교육 과정 목록 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            courses:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  training_course:
                    type: string
                  dept:
                    type: string
                  manager_name:
                    type: string
                  start_date:
                    type: string
                    format: date
                  end_date:
                    type: string
                    format: date
    """
    try:
        dept = request.args.get('dept')
        active_only = request.args.get('active_only', type=bool)
        
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, training_course, dept, manager_name, start_date, end_date 
            FROM training_courses 
            WHERE 1=1
        """
        params = []

        if dept:
            query += " AND dept = %s"
            params.append(dept)

        if active_only:
            query += " AND start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE"

        query += " ORDER BY start_date DESC"

        cursor.execute(query, params)
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "courses": [
                {
                    "id": course[0],
                    "training_course": course[1],
                    "dept": course[2],
                    "manager_name": course[3],
                    "start_date": course[4].isoformat() if course[4] else None,
                    "end_date": course[5].isoformat() if course[5] else None
                }
                for course in courses
            ]
        }), 200

    except Exception as e:
        logging.error("교육 과정 목록 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "교육 과정 목록 조회 중 오류가 발생했습니다."
        }), 500

@training_bp.route('/courses', methods=['POST'])
def create_training_course():
    """
    교육 과정 등록 API
    ---
    tags:
      - Training
    summary: 새로운 교육 과정을 등록합니다.
    description: |
      새로운 교육 과정을 등록합니다.
      과정명, 부서, 담당자, 시작일, 종료일이 필요합니다.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - training_course
            - dept
            - manager_name
            - start_date
            - end_date
          properties:
            training_course:
              type: string
              description: 교육 과정명
            dept:
              type: string
              description: 부서명
            manager_name:
              type: string
              description: 담당자 이름
            start_date:
              type: string
              format: date
              description: 시작일
            end_date:
              type: string
              format: date
              description: 종료일
    responses:
      201:
        description: 교육 과정 등록 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "교육 과정이 등록되었습니다."
    """
    try:
        data = request.get_json()
        training_course = data.get('training_course')
        dept = data.get('dept')
        manager_name = data.get('manager_name')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not all([training_course, dept, manager_name, start_date, end_date]):
            return jsonify({
                "success": False,
                "message": "필수 데이터가 누락되었습니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO training_courses 
            (training_course, dept, manager_name, start_date, end_date, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (training_course, dept, manager_name, start_date, end_date, datetime.now()))

        course_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "교육 과정이 등록되었습니다.",
            "id": course_id
        }), 201

    except Exception as e:
        logging.error("교육 과정 등록 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "교육 과정 등록 중 오류가 발생했습니다."
        }), 500

@training_bp.route('/courses/<int:course_id>', methods=['PUT'])
def update_training_course(course_id):
    """
    교육 과정 수정 API
    ---
    tags:
      - Training
    summary: 교육 과정 정보를 수정합니다.
    description: |
      기존 교육 과정의 정보를 수정합니다.
      과정명, 부서, 담당자, 시작일, 종료일을 수정할 수 있습니다.
    parameters:
      - name: course_id
        in: path
        type: integer
        required: true
        description: 교육 과정 ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            training_course:
              type: string
              description: 교육 과정명
            dept:
              type: string
              description: 부서명
            manager_name:
              type: string
              description: 담당자 이름
            start_date:
              type: string
              format: date
              description: 시작일
            end_date:
              type: string
              format: date
              description: 종료일
    responses:
      200:
        description: 교육 과정 수정 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "교육 과정이 수정되었습니다."
    """
    try:
        data = request.get_json()
        updates = []
        params = []
        
        # 수정할 필드 확인
        if 'training_course' in data:
            updates.append("training_course = %s")
            params.append(data['training_course'])
        if 'dept' in data:
            updates.append("dept = %s")
            params.append(data['dept'])
        if 'manager_name' in data:
            updates.append("manager_name = %s")
            params.append(data['manager_name'])
        if 'start_date' in data:
            updates.append("start_date = %s")
            params.append(data['start_date'])
        if 'end_date' in data:
            updates.append("end_date = %s")
            params.append(data['end_date'])

        if not updates:
            return jsonify({
                "success": False,
                "message": "수정할 데이터가 없습니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 수정 쿼리 실행
        query = f"""
            UPDATE training_courses 
            SET {", ".join(updates)}, updated_at = %s
            WHERE id = %s
            RETURNING id
        """
        params.extend([datetime.now(), course_id])

        cursor.execute(query, params)
        
        if cursor.fetchone() is None:
            return jsonify({
                "success": False,
                "message": "교육 과정을 찾을 수 없습니다."
            }), 404
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "교육 과정이 수정되었습니다."
        }), 200

    except Exception as e:
        logging.error("교육 과정 수정 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "교육 과정 수정 중 오류가 발생했습니다."
        }), 500 