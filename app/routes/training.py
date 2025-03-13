from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime

bp = Blueprint('training', __name__)

@bp.route('/training/courses', methods=['GET'])
def get_training_courses():
    """
    훈련 과정 목록 조회 API
    ---
    tags:
      - Training
    summary: 등록된 훈련 과정 목록을 조회합니다.
    description: |
      시스템에 등록된 모든 훈련 과정 정보를 조회합니다.
      - 과정 ID, 과정명, 부서, 담당자 등 반환
      - 부서별 정렬 및 필터링 가능
      - 현재 진행 중인 과정만 조회 가능
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
        description: 진행 중인 과정만 조회 (기본값: true)
    responses:
      200:
        description: 훈련 과정 목록 조회 성공
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
                    description: 과정 ID
                  training_course:
                    type: string
                    description: 과정명
                  dept:
                    type: string
                    description: 담당 부서
                  manager_name:
                    type: string
                    description: 담당자 이름
                  start_date:
                    type: string
                    format: date
                    description: 과정 시작일
                  end_date:
                    type: string
                    format: date
                    description: 과정 종료일
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
        dept = request.args.get('dept')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, training_course, dept, manager_name, start_date, end_date
            FROM training_info
            WHERE 1=1
        '''
        params = []
        
        if dept:
            query += ' AND dept = %s'
            params.append(dept)
            
        if active_only:
            query += ' AND end_date >= CURRENT_DATE'
            
        query += ' ORDER BY dept, start_date DESC'
        
        cursor.execute(query, params if params else None)
        courses = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": [{
                "id": row[0],
                "training_course": row[1],
                "dept": row[2],
                "manager_name": row[3],
                "start_date": row[4],
                "end_date": row[5]
            } for row in courses]
        }), 200

    except Exception as e:
        logging.error("Error retrieving training courses", exc_info=True)
        return jsonify({"success": False, "message": "훈련 과정 목록을 불러오는 중 오류가 발생했습니다."}), 500

@bp.route('/training/courses', methods=['POST'])
def create_training_course():
    """
    훈련 과정 등록 API
    ---
    tags:
      - Training
    summary: 새로운 훈련 과정을 등록합니다.
    description: |
      새로운 훈련 과정을 시스템에 등록합니다.
      - 과정명, 부서, 담당자, 시작일, 종료일은 필수 입력 항목
      - 과정 기간은 시작일이 종료일보다 이전이어야 함
      - 동일한 과정명이 이미 존재하는 경우 등록 불가
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
              description: 과정명
            dept:
              type: string
              description: 담당 부서
            manager_name:
              type: string
              description: 담당자 이름
            start_date:
              type: string
              format: date
              description: 과정 시작일 (YYYY-MM-DD)
            end_date:
              type: string
              format: date
              description: 과정 종료일 (YYYY-MM-DD)
    responses:
      201:
        description: 훈련 과정 등록 성공
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
        training_course = data.get('training_course', '').strip()
        dept = data.get('dept', '').strip()
        manager_name = data.get('manager_name', '').strip()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not all([training_course, dept, manager_name, start_date, end_date]):
            return jsonify({
                "success": False, 
                "message": "과정명, 부서, 담당자, 시작일, 종료일을 모두 입력하세요."
            }), 400

        # 날짜 형식 검증
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if start > end:
                return jsonify({
                    "success": False,
                    "message": "종료일이 시작일보다 이전일 수 없습니다."
                }), 400
        except ValueError:
            return jsonify({
                "success": False,
                "message": "올바른 날짜 형식이 아닙니다. (YYYY-MM-DD)"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 중복 과정 체크
        cursor.execute(
            'SELECT id FROM training_info WHERE training_course = %s',
            (training_course,)
        )
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "이미 존재하는 과정명입니다."
            }), 400

        # 과정 등록
        cursor.execute('''
            INSERT INTO training_info 
            (training_course, dept, manager_name, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s)
        ''', (training_course, dept, manager_name, start_date, end_date))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "훈련 과정이 등록되었습니다."
        }), 201

    except Exception as e:
        logging.error("Error creating training course", exc_info=True)
        return jsonify({
            "success": False,
            "message": "훈련 과정 등록 중 오류가 발생했습니다."
        }), 500

@bp.route('/training/courses/<int:course_id>', methods=['PUT'])
def update_training_course():
    """
    훈련 과정 수정 API
    ---
    tags:
      - Training
    summary: 기존 훈련 과정 정보를 수정합니다.
    description: |
      등록된 훈련 과정의 정보를 수정합니다.
      - 과정명, 부서, 담당자, 시작일, 종료일 수정 가능
      - 과정 기간은 시작일이 종료일보다 이전이어야 함
      - 다른 과정과 중복되는 과정명으로는 수정 불가
    parameters:
      - name: course_id
        in: path
        type: integer
        required: true
        description: 수정할 훈련 과정의 ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            training_course:
              type: string
              description: 과정명
            dept:
              type: string
              description: 담당 부서
            manager_name:
              type: string
              description: 담당자 이름
            start_date:
              type: string
              format: date
              description: 과정 시작일 (YYYY-MM-DD)
            end_date:
              type: string
              format: date
              description: 과정 종료일 (YYYY-MM-DD)
    responses:
      200:
        description: 훈련 과정 수정 성공
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
      404:
        description: 과정을 찾을 수 없음
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
        course_id = request.view_args.get('course_id')
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 과정 존재 여부 확인
        cursor.execute('SELECT id FROM training_info WHERE id = %s', (course_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "해당 훈련 과정을 찾을 수 없습니다."
            }), 404

        # 수정할 필드 확인
        update_fields = []
        params = []
        if 'training_course' in data:
            update_fields.append('training_course = %s')
            params.append(data['training_course'].strip())
        if 'dept' in data:
            update_fields.append('dept = %s')
            params.append(data['dept'].strip())
        if 'manager_name' in data:
            update_fields.append('manager_name = %s')
            params.append(data['manager_name'].strip())
        if 'start_date' in data:
            update_fields.append('start_date = %s')
            params.append(data['start_date'])
        if 'end_date' in data:
            update_fields.append('end_date = %s')
            params.append(data['end_date'])

        if not update_fields:
            return jsonify({
                "success": False,
                "message": "수정할 내용이 없습니다."
            }), 400

        # 과정 정보 수정
        query = f'''
            UPDATE training_info 
            SET {', '.join(update_fields)}
            WHERE id = %s
        '''
        params.append(course_id)
        
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "훈련 과정 정보가 수정되었습니다."
        }), 200

    except Exception as e:
        logging.error("Error updating training course", exc_info=True)
        return jsonify({
            "success": False,
            "message": "훈련 과정 수정 중 오류가 발생했습니다."
        }), 500 