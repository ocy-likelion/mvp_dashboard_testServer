from flask import Blueprint, request, jsonify, session
from app.database import get_db_connection
import logging

# Blueprint 정의
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def init_auth_routes(app):
    """
    인증 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(auth_bp)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    사용자 로그인 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그인을 처리합니다.
    description: |
      사용자 이름과 비밀번호를 검증하고 로그인을 처리합니다.
      성공 시 세션에 사용자 정보를 저장합니다.
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
              example: true
            message:
              type: string
              example: "로그인 성공"
      401:
        description: 인증 실패
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "사용자 이름 또는 비밀번호가 잘못되었습니다."
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                "success": False,
                "message": "사용자 이름과 비밀번호를 모두 입력해주세요."
            }), 400

        logging.info(f"로그인 시도 - username: {username}")
        
        user = authenticate_user(username, password)
        
        if user:
            session['user'] = username
            logging.info(f"로그인 성공 - username: {username}")
            return jsonify({
                "success": True,
                "message": "로그인 성공"
            }), 200
        
        logging.warning(f"로그인 실패 - username: {username}")
        return jsonify({
            "success": False,
            "message": "사용자 이름 또는 비밀번호가 잘못되었습니다."
        }), 401

    except Exception as e:
        logging.error("로그인 처리 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "로그인 처리 중 오류가 발생했습니다."
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    로그아웃 API
    ---
    tags:
      - Authentication
    summary: 사용자 로그아웃을 처리합니다.
    description: 세션에서 사용자 정보를 제거합니다.
    responses:
      200:
        description: 로그아웃 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "로그아웃 성공"
    """
    try:
        username = session.pop('user', None)
        if username:
            logging.info(f"로그아웃 성공 - username: {username}")
        return jsonify({
            "success": True,
            "message": "로그아웃 성공"
        }), 200
    except Exception as e:
        logging.error("로그아웃 처리 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "로그아웃 처리 중 오류가 발생했습니다."
        }), 500

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """
    인증 상태 확인 API
    ---
    tags:
      - Authentication
    summary: 현재 사용자의 인증 상태를 확인합니다.
    description: 세션에 저장된 사용자 정보를 확인합니다.
    responses:
      200:
        description: 인증 상태 확인 성공
        schema:
          type: object
          properties:
            authenticated:
              type: boolean
              example: true
            username:
              type: string
              example: "user123"
    """
    username = session.get('user')
    return jsonify({
        "authenticated": bool(username),
        "username": username
    }), 200

def authenticate_user(username: str, password: str) -> bool:
    """
    사용자 인증을 처리하는 헬퍼 함수
    
    Args:
        username (str): 사용자 이름
        password (str): 비밀번호
    
    Returns:
        bool: 인증 성공 여부
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'SELECT username, password FROM users WHERE username = %s',
            (username,)
        )
        user = cursor.fetchone()
        return user is not None and user[1] == password
    finally:
        cursor.close()
        conn.close() 