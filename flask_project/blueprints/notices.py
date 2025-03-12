# blueprints/notices.py
from flask import Blueprint, request, jsonify
from database import get_db_connection
import logging
from datetime import datetime

notices_bp = Blueprint('notices', __name__)

@notices_bp.route('/', methods=['GET'])
def get_notices():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 공지사항과 전달사항을 모두 불러옴
        cursor.execute('SELECT * FROM notices ORDER BY date DESC')
        notices = cursor.fetchall()
        cursor.close()
        conn.close()
        # '전달사항'만 필터링하여 별도로 제공 (notice[1]가 타입으로 가정)
        return jsonify({
            "success": True,
            "data": {
                "notices": notices,
                "remarks": [notice for notice in notices if notice[1] == '전달사항']
            }
        }), 200
    except Exception as e:
        logging.error("Error retrieving notices", exc_info=True)
        return jsonify({"success": False, "message": "Failed to retrieve notices"}), 500
