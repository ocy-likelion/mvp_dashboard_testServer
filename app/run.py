import os
from flask import Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes import auth_bp, notices_bp, issues_bp, tasks_bp, training_bp, admin_bp, notifications_bp
from app.config import PORT, SESSION_CONFIG

def create_app():
    app = Flask(__name__)
    
    # 세션 비밀키 설정
    app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
    
    # config.py에서 가져온 세션 설정 적용
    for key, value in SESSION_CONFIG.items():
        app.config[key] = value
    
    # CORS 설정 (쿠키 허용)
    CORS(app, supports_credentials=True)
    
    # 라우터 등록
    app.register_blueprint(auth_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)  # 새로 추가한 알림 라우터
    
    # Swagger 설정
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    return app

app = create_app()

if __name__ == "__main__":
    print(f"서버가 시작되었습니다. 포트: {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)