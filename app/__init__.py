from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Swagger 설정
    swagger = Swagger(app)
    
    # 시크릿 키 설정
    app.secret_key = 'your-secret-key'  # 실제 운영 환경에서는 환경 변수로 관리
    
    # Blueprint 등록
    from app.routes.auth import init_auth_routes
    from app.routes.admin import init_admin_routes
    from app.routes.tasks import init_tasks_routes
    from app.routes.notices import init_notices_routes
    from app.routes.unchecked import init_unchecked_routes
    from app.routes.irregular_tasks import init_irregular_tasks_routes
    from app.routes.issues import init_issues_routes
    from app.routes.training import init_training_routes
    
    # 각 Blueprint 초기화
    init_auth_routes(app)
    init_admin_routes(app)
    init_tasks_routes(app)
    init_notices_routes(app)
    init_unchecked_routes(app)
    init_irregular_tasks_routes(app)
    init_issues_routes(app)
    init_training_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 