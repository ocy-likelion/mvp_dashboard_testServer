from flask import Blueprint, request, jsonify
from app.database import get_db_connection
import logging
from datetime import datetime, timedelta

# Blueprint 정의
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def init_admin_routes(app):
    """
    관리자 관련 라우트를 초기화합니다.
    """
    app.register_blueprint(admin_bp)

@admin_bp.route('/check_rates', methods=['GET'])
def get_check_rates():
    """
    체크율 조회 API
    ---
    tags:
      - Admin
    summary: 현재일과 전일의 체크율을 조회합니다.
    description: |
      현재일과 전일의 작업 체크율을 계산하여 반환합니다.
      - 총 작업 수
      - 체크된 작업 수
      - 체크율(%)
    parameters:
      - name: training_course
        in: query
        type: string
        required: true
        description: 훈련 과정명
    responses:
      200:
        description: 체크율 조회 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                today:
                  type: object
                  properties:
                    total_tasks:
                      type: integer
                    checked_tasks:
                      type: integer
                    check_rate:
                      type: number
                yesterday:
                  type: object
                  properties:
                    total_tasks:
                      type: integer
                    checked_tasks:
                      type: integer
                    check_rate:
                      type: number
    """
    try:
        training_course = request.args.get('training_course')
        if not training_course:
            return jsonify({
                "success": False,
                "message": "훈련 과정명이 필요합니다."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        # 오늘의 체크율 계산
        today_stats = calculate_check_rate(cursor, training_course, today)
        
        # 어제의 체크율 계산
        yesterday_stats = calculate_check_rate(cursor, training_course, yesterday)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "today": today_stats,
                "yesterday": yesterday_stats
            }
        }), 200

    except Exception as e:
        logging.error("체크율 조회 중 오류 발생", exc_info=True)
        return jsonify({
            "success": False,
            "message": "체크율 조회 중 오류가 발생했습니다."
        }), 500

def calculate_check_rate(cursor, training_course: str, date: datetime.date) -> dict:
    """
    특정 날짜의 체크율을 계산합니다.
    
    Args:
        cursor: 데이터베이스 커서
        training_course (str): 훈련 과정명
        date (datetime.date): 계산할 날짜
    
    Returns:
        dict: 체크율 통계 정보
    """
    # 총 작업 수 조회
    cursor.execute("""
        SELECT COUNT(*) 
        FROM task_checklist tc
        JOIN task_items ti ON tc.task_id = ti.id
        WHERE tc.training_course = %s AND DATE(tc.date) = %s
    """, (training_course, date))
    total_tasks = cursor.fetchone()[0]

    # 체크된 작업 수 조회 (체크된 항목 + 해결된 미체크 항목)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM task_checklist tc
        JOIN task_items ti ON tc.task_id = ti.id
        WHERE tc.training_course = %s 
        AND DATE(tc.date) = %s
        AND (tc.is_checked = true OR EXISTS (
            SELECT 1 FROM unchecked_descriptions ud
            WHERE ud.task_name = ti.task_name
            AND ud.training_course = tc.training_course
            AND DATE(ud.date) = DATE(tc.date)
            AND ud.resolved = true
        ))
    """, (training_course, date))
    checked_tasks = cursor.fetchone()[0]

    # 체크율 계산
    check_rate = round((checked_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

    return {
        "total_tasks": total_tasks,
        "checked_tasks": checked_tasks,
        "check_rate": check_rate
    } 