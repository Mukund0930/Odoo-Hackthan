from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
import os

from .config import config_by_name

# Initialize extensions without app context yet
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()
scheduler = BackgroundScheduler(daemon=True) # daemon=True for dev, consider timezone

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__, instance_relative_config=True) # instance_relative_config=True
    app.config.from_object(config_by_name[config_name])
    app.config.from_pyfile('config.py', silent=True) # Load instance config if it exists

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists

    # Initialize extensions with app context
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    # Allow all origins from your frontend URL, and common methods/headers
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get('FRONTEND_URL', '*')}})
    mail.init_app(app)

    # Import models here to ensure they are known to SQLAlchemy before db operations
    from . import models

    # Register Blueprints
    from .apis import api_bp  # Import the main API blueprint
    app.register_blueprint(api_bp)

    # Configure JWT error handlers (optional, but good for consistent responses)
    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return {'message': 'Missing Authorization Header'}, 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return {'message': 'Invalid token'}, 422 # Unprocessable Entity

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401

    # --- APScheduler Tasks (Example: Daily Event Reminders) ---
    # You'll need to define this function properly
    def send_daily_event_reminders_job():
        with app.app_context(): # Need app context for db access and config
            from .models import Event, User, Rsvp
            from .services.notification_service import send_event_reminder
            from datetime import datetime, timedelta, timezone

            app.logger.info("Running daily event reminder job...")
            tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
            
            # Find events happening tomorrow
            events_tomorrow = Event.query.filter(
                db.func.date(Event.start_datetime) == tomorrow,
                Event.status == 'APPROVED'
            ).all()

            for event in events_tomorrow:
                app.logger.info(f"Processing reminders for event: {event.title}")
                # Get users who RSVPd and prefer email notifications
                rsvps = Rsvp.query.filter_by(event_id=event.id).all()
                for rsvp_entry in rsvps:
                    if rsvp_entry.user_id: # Registered user
                        user = User.query.get(rsvp_entry.user_id)
                        if user and 'email' in user.notification_preference and user.email:
                            send_event_reminder(event, user)
                            app.logger.info(f"Sent reminder to user {user.username} for event {event.title}")
                    # elif rsvp_entry.guest_email: # Guest RSVP - implement if needed
                        # send_guest_event_reminder(event, rsvp_entry.guest_email, rsvp_entry.guest_name)

    if not scheduler.running and app.config.get('SCHEDULER_API_ENABLED', False): # SCHEDULER_API_ENABLED for safety
        # Schedule the job to run daily (e.g., at 2 AM UTC)
        scheduler.add_job(send_daily_event_reminders_job, 'cron', hour=2, minute=0, timezone='UTC')
        try:
            scheduler.start()
            app.logger.info("Scheduler started for background tasks.")
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            app.logger.info("Scheduler shut down.")
        except Exception as e:
            app.logger.error(f"Error starting scheduler: {e}")


    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': models.User, 'Event': models.Event, 'Rsvp': models.Rsvp}

    return app