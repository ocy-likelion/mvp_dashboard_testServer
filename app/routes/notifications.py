from flask import Blueprint, request, jsonify, session
import logging
from app.models.db import get_db_connection
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    로그인 후 새 알림 조회 API
    ---
    tags:
      - Notifications
    responses:
      200:
        description: 알림 조회 성공
      401:
        description: 로그인 필요
      500:
        description: 서버 오류 발생
    """
    if 'user' not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401
    
    prev_login = session.get('prev_login')
    if not prev_login:
        # 첫 로그인이거나 데이터가 없는 경우
        return jsonify({"success": True, "data": {
            "new_notices": [], 
            "new_issues": [], 
            "new_comments": []
        }}), 200
    
    try:
        # ISO 문자열을 datetime으로 변환
        prev_login_date = datetime.fromisoformat(prev_login)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 새 공지사항 조회
        cursor.execute("""
            SELECT id, title, date FROM notices 
            WHERE date > %s AND (is_deleted = FALSE OR is_deleted IS NULL)
            ORDER BY date DESC
        """, (prev_login_date,))
        new_notices = [{"id": row[0], "title": row[1], "date": row[2]} for row in cursor.fetchall()]
        
        # 새 이슈 조회
        cursor.execute("""
            SELECT id, issue, date FROM issues 
            WHERE date > %s AND (is_resolved = FALSE OR is_resolved IS NULL)
            ORDER BY date DESC
        """, (prev_login_date,))
        new_issues = [{"id": row[0], "issue": row[1], "date": row[2]} for row in cursor.fetchall()]
        
        # 새 댓글 조회
        cursor.execute("""
            SELECT ic.id, ic.comment, ic.created_at, i.issue 
            FROM issue_comments ic
            JOIN issues i ON ic.issue_id = i.id
            WHERE ic.created_at > %s
            ORDER BY ic.created_at DESC
        """, (prev_login_date,))
        new_comments = [{
            "id": row[0], 
            "comment": row[1], 
            "date": row[2],
            "issue": row[3]
        } for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "data": {
                "new_notices": new_notices,
                "new_issues": new_issues,
                "new_comments": new_comments
            }
        }), 200
        
    except Exception as e:
        logging.error("알림 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "알림 정보를 가져오는 중 오류가 발생했습니다."}), 500