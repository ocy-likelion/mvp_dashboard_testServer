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
      사용자 ID와 비밀번호를 검증하고 로그인을 처리합니다.
      - 로그인 성공 시 세션에 사용자 정보 저장
      - 실패 시 적절한 에러 메시지 반환
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - password
          properties:
            user_id:
              type: string
              description: 사용자 ID
            password:
              type: string
              description: 사용자 비밀번호
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
        user_id = data.get('user_id')
        password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = %s AND password = %s', (user_id, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user'] = user_id
            return jsonify({"success": True, "message": "로그인 성공"}), 200
        else:
            return jsonify({"success": False, "message": "아이디 또는 비밀번호가 잘못되었습니다."}), 401

    except Exception as e:
        logging.error("Login error", exc_info=True)
        return jsonify({"success": False, "message": "로그인 처리 중 오류가 발생했습니다."}), 500

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