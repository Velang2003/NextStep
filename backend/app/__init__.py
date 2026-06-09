import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from .config import Config
from .celery_app import celary_init_app

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Sentry
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
    
    # Initialize Celery
    celary_init_app(app)
    
    # Load models
    from . import models

    # Initialize extensions
    db.init_app(app)
    
    # Initialize Firebase Admin SDK
    import json
    import base64
    firebase_env = os.getenv('FIREBASE_CREDENTIALS')
    
    if firebase_env:
        try:
            # Try to parse as direct JSON first
            cred_dict = json.loads(firebase_env)
        except json.JSONDecodeError:
            # If it fails, try parsing as base64
            cred_dict = json.loads(base64.b64decode(firebase_env).decode('utf-8'))
            
        cred = credentials.Certificate(cred_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
    else:
        # Fallback to local file for development
        service_account_path = os.path.join(app.root_path, '..', 'firebase-service-account.json')
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
        else:
            app.logger.warning("Firebase credentials not found in env or local file.")

    # Load allowed CORS origins from env for production flexibility
    allowed_origins = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:5174,http://localhost:3000'
    ).split(',')
    CORS(app, resources={r"/api/*": {"origins": [o.strip() for o in allowed_origins]}})

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.jobs import jobs_bp
    from .routes.profile import profile_bp
    from .routes.reports import reports_bp
    from .routes.taxonomy import taxonomy_bp
    from .routes.assessment import assessment_bp
    from .routes.applications import applications_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp,          url_prefix='/api/auth')
    app.register_blueprint(jobs_bp,          url_prefix='/api/jobs')
    app.register_blueprint(profile_bp,       url_prefix='/api/profile')
    app.register_blueprint(reports_bp,       url_prefix='/api/reports')
    app.register_blueprint(taxonomy_bp,      url_prefix='/api/taxonomy')
    app.register_blueprint(assessment_bp,    url_prefix='/api/assessment')
    app.register_blueprint(applications_bp,  url_prefix='/api/applications')
    app.register_blueprint(admin_bp,         url_prefix='/api/admin')

    # Health check
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "version": "2.0.0"}), 200

    # Helper: run the pipeline inside the Flask app context (for background scheduler)
    def _run_pipeline_in_context():
        with app.app_context():
            from app.services.pipeline import run_pipeline
            run_pipeline()

    # Initialize Scheduler — daily job pipeline at 2:00 AM IST
    # In debug mode with reloader, only start in the child worker process
    # (WERKZEUG_RUN_MAIN == 'true'). In production (no reloader), always start.
    import os as _os
    import atexit
    from apscheduler.schedulers.background import BackgroundScheduler

    is_reloader_child = _os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    is_production     = not app.debug

    if is_production or is_reloader_child:
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            func=_run_pipeline_in_context,
            trigger='cron',
            hour=2,
            minute=0,
            timezone='Asia/Kolkata',
            id='daily_pipeline',
            replace_existing=True,
            misfire_grace_time=3600,  # 1-hour grace window
        )
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown(wait=False))
        app.logger.info("Background scheduler started: run_pipeline at 2:00 AM daily.")

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback, logging
        tb = traceback.format_exc()
        # Append to crash log instead of overwriting
        with open('crash_dump.log', 'a') as f:
            f.write(f"\n{'='*60}\n{tb}")
        app.logger.error(tb)
        # Never expose internals to the client in production
        if app.debug:
            return jsonify(error=str(e), traceback=tb), 500
        return jsonify(error='Internal Server Error. Please try again later.'), 500

    return app
