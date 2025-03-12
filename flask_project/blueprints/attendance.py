# blueprints/attendance.py
from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import io
from database import get_db_connection
import logging

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/', methods=['GET'])
def get_attendance():
    try:
        format_type = request.args.get('format', 'json')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM attendance ORDER BY date DESC')
        attendance_records = cursor.fetchall()
        cursor.close()
        conn.close()

        columns = ['ID', '날짜', '강사', '훈련과정', '출근 시간', '퇴근 시간', '일지 작성 완료']
        df = pd.DataFrame(attendance_records, columns=columns)

        if format_type == 'json':
            return jsonify({"success": True, "data": df.to_dict(orient='records')}), 200
        elif format_type == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="출퇴근 기록")
            output.seek(0)
            return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="출퇴근_기록.xlsx")
        else:
            return jsonify({"success": False, "message": "잘못된 포맷 요청"}), 400
    except Exception as e:
        logging.error("출퇴근 기록 조회 오류", exc_info=True)
        return jsonify({"success": False, "message": "출퇴근 기록 조회 실패"}), 500
