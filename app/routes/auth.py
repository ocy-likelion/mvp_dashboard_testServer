from flask import Blueprint, request, jsonify, session, redirect, url_for
from app.database import get_db_connection
import logging

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """
    사용자 로그인 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그인을 처리합니다.
    description: |
      사용자 이름과 비밀번호를 검증하고 로그인을 처리합니다.
      - 로그인 성공 시 세션에 사용자 정보 저장
      - 실패 시 적절한 에러 메시지 반환
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: 사용자 이름
            password:
              type: string
              description: 비밀번호
    responses:
      200:
        description: 로그인 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: 로그인 성공 여부
            message:
              type: string
              description: 성공 메시지
      401:
        description: 로그인 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: 로그인 실패 여부
            message:
              type: string
              description: 실패 사유
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
        username = data.get('username')  # user_id 대신 username 사용
        password = data.get('password')

        # 입력값 검증
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "사용자 이름과 비밀번호를 모두 입력해주세요."
            }), 400

        # 디버깅을 위한 로그
        logging.info(f"Login attempt - username: {username}")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 사용자 존재 여부 확인
        cursor.execute('SELECT username, password FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        
        # 디버깅을 위한 로그
        logging.info(f"Database query result: {user is not None}")

        cursor.close()
        conn.close()

        if user and user[1] == password:
            session['user'] = user[0]  # username 저장
            return jsonify({
                "success": True,
                "message": "로그인 성공"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "사용자 이름 또는 비밀번호가 잘못되었습니다."
            }), 401

    except Exception as e:
        logging.error("Login error", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"로그인 처리 중 오류가 발생했습니다. 오류: {str(e)}"
        }), 500

@bp.route('/logout', methods=['POST'])
def logout():
    """
    로그아웃 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그아웃을 처리합니다.
    description: |
      현재 로그인된 사용자의 세션을 종료합니다.
      - 세션에서 사용자 정보 제거
      - 로그아웃 후 로그인 페이지로 리다이렉트
    responses:
      200:
        description: 로그아웃 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: 로그아웃 성공 여부
            message:
              type: string
              description: 성공 메시지
    """
    session.pop('user', None)
    return jsonify({"success": True, "message": "로그아웃 되었습니다."}), 200

@bp.route('/current_user', methods=['GET'])
def get_current_user():
    """
    현재 로그인된 사용자 정보 조회 API
    ---
    tags:
      - Authentication
    summary: 현재 로그인된 사용자 정보를 반환합니다.
    description: |
      세션에 저장된 현재 로그인된 사용자 정보를 반환합니다.
      - 로그인된 경우 사용자 ID 반환
      - 로그인되지 않은 경우 null 반환
    responses:
      200:
        description: 사용자 정보 조회 성공
        schema:
          type: object
          properties:
            user:
              type: string
              description: 로그인된 사용자 ID (없으면 null)
    """
    return jsonify({"user": session.get('user', None)}) 