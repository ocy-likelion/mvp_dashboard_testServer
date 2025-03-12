# app.py
from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp
from blueprints.notices import notices_bp
from blueprints.attendance import attendance_bp
from blueprints.tasks import tasks_bp
from blueprints.issues import issues_bp
from blueprints.training import training_bp
from blueprints.unchecked import unchecked_bp

app = Flask(__name__)
app.secret_key = "your-secret-key"

CORS(app, supports_credentials=True)
app.config['SWAGGER'] = {'title': "업무 관리 대시보드 API", 'uiversion': 3}
swagger = Swagger(app)

# 블루프린트 등록
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(notices_bp, url_prefix='/notices')
app.register_blueprint(attendance_bp, url_prefix='/attendance')
app.register_blueprint(tasks_bp, url_prefix='/tasks')
app.register_blueprint(issues_bp, url_prefix='/issues')
app.register_blueprint(training_bp, url_prefix='/training')
app.register_blueprint(unchecked_bp, url_prefix='/unchecked')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
